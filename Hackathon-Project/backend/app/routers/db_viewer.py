"""Read-only database browser for admins.

Security model (this used to be open to the internet):
* every data endpoint requires an Admin / Super Admin bearer token;
* the SQLite connection is opened read-only AND guarded by an authorizer that only allows SELECT;
* password columns can never be read, even with SELECT * or a sub-query;
* results are capped.
The HTML shell itself holds no data; it reads the token the main app stored in localStorage.
"""
import sqlite3
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.dependencies import require_admin
from app.models.user import User

router = APIRouter(tags=["Database Explorer"])

DB_PATH = Path(settings.DATABASE_URL.replace("sqlite:///", "", 1))
HIDDEN_COLUMNS = {("users", "hashed_password"), ("users", "initial_password")}
ROW_LIMIT = 500


class QueryRequest(BaseModel):
    sql: str = Field(..., min_length=1, max_length=4000)


def _authorizer(action, arg1, arg2, db_name, source):
    # Only plain reads: SELECT (21), READ (20), FUNCTION (31), RECURSIVE (33).
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION, 33):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        if (str(arg1).lower(), str(arg2).lower()) in HIDDEN_COLUMNS:
            return sqlite3.SQLITE_IGNORE  # the column reads as NULL
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _connect():
    if not settings.DATABASE_URL.startswith("sqlite"):
        raise HTTPException(status_code=501, detail="The browser supports the bundled SQLite database only.")
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="Database file not found")
    conn = sqlite3.connect(f"file:{quote(DB_PATH.as_posix(), safe='/:')}?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.set_authorizer(_authorizer)
    return conn


def _run(sql: str):
    stmt = sql.strip().rstrip(";").strip()
    if ";" in stmt:
        raise HTTPException(status_code=400, detail="Only a single statement is allowed.")
    if not stmt.lower().startswith(("select", "with")):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")
    conn = _connect()
    try:
        cur = conn.execute(stmt)
        rows = cur.fetchmany(ROW_LIMIT + 1)
        cols = [d[0] for d in cur.description] if cur.description else []
        truncated = len(rows) > ROW_LIMIT
        return {"columns": cols, "rows": [list(r) for r in rows[:ROW_LIMIT]], "truncated": truncated, "row_count": min(len(rows), ROW_LIMIT)}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=400, detail=f"SQL error: {exc}")
    finally:
        conn.close()


@router.get("/db/api/tables")
def list_tables(_: User = Depends(require_admin)):
    conn = _connect()
    try:
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        out = []
        for n in names:
            count = conn.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0]
            out.append({"name": n, "rows": count})
        return {"tables": out}
    finally:
        conn.close()


@router.post("/db/query")
def run_query(req: QueryRequest, _: User = Depends(require_admin)):
    return _run(req.sql)


_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TalentPulse AI · DB Browser</title>
<style>
:root{--ink:#111;--paper:#fff4d6;--y:#ffd23f;--p:#ff7ab8;--b:#62b6ff;--g:#5be3a0;--r:#ff5d62}
*{box-sizing:border-box}body{margin:0;background:var(--paper);background-image:radial-gradient(circle at 1px 1px,#11111138 1.2px,transparent 1.4px);background-size:22px 22px;color:var(--ink);font:15px/1.5 "Segoe UI",system-ui,Arial,sans-serif}
.wrap{max-width:1400px;margin:0 auto;padding:24px}
header{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;align-items:center;border:3px solid var(--ink);background:var(--y);padding:14px 18px;box-shadow:6px 6px 0 var(--ink)}
h1{margin:0;font-size:1.4rem;letter-spacing:-.03em}small{font-family:ui-monospace,Consolas,monospace}
a.btn,button{font:inherit;font-weight:800;border:3px solid var(--ink);background:#fff;padding:8px 14px;cursor:pointer;box-shadow:3px 3px 0 var(--ink);color:var(--ink);text-decoration:none}
a.btn:hover,button:hover{transform:translate(-2px,-2px);box-shadow:5px 5px 0 var(--ink)}button:active{transform:translate(3px,3px);box-shadow:none}
.pills{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0}.pills button.on{background:var(--p)}
.box{border:3px solid var(--ink);background:#fff;padding:16px;box-shadow:6px 6px 0 var(--ink);margin-bottom:22px}
textarea{width:100%;height:84px;font:14px ui-monospace,Consolas,monospace;border:3px solid var(--ink);padding:10px}
.scroll{overflow:auto;max-height:60vh;border:3px solid var(--ink);margin-top:14px}
table{border-collapse:collapse;width:100%;font-size:.85rem;background:#fff}th{position:sticky;top:0;background:var(--y);text-align:left;font:700 .72rem ui-monospace,Consolas,monospace;text-transform:uppercase;letter-spacing:.06em}
th,td{padding:8px 12px;border-bottom:2px solid var(--ink);border-right:2px solid var(--ink);white-space:nowrap;max-width:360px;overflow:hidden;text-overflow:ellipsis}tr:nth-child(even) td{background:#fff9e8}
.msg{padding:12px;border:3px solid var(--ink);font-weight:700;margin:14px 0}.err{background:var(--r)}.ok{background:var(--g)}
</style></head><body><div class="wrap">
<header><div><h1>TalentPulse AI · Database Browser</h1><small>read-only · admins only · password columns are hidden</small></div>
<div><a class="btn" href="/ui">Main app</a> <a class="btn" href="/docs">Swagger</a></div></header>
<div id="status"></div><div class="pills" id="tables"></div>
<div class="box"><b>Run a SELECT query</b><textarea id="sql">SELECT id, email, role, is_active FROM users LIMIT 20</textarea>
<div style="margin-top:10px"><button id="run">Run query</button></div><div id="stats"></div><div class="scroll" id="out" hidden></div></div>
</div><script>
const S=(()=>{try{return JSON.parse(localStorage.getItem('tp.session')||'null')}catch(e){return null}})();
const $=id=>document.getElementById(id);
function msg(t,c){$('status').innerHTML='<div class="msg '+c+'"></div>';$('status').firstChild.textContent=t}
async function call(path,opts){const r=await fetch(path,Object.assign({headers:{'Authorization':'Bearer '+(S&&S.access_token),'Content-Type':'application/json'}},opts||{}));
 const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.detail||('HTTP '+r.status));return j}
function render(d){const o=$('out');o.hidden=false;const t=document.createElement('table');const h=t.createTHead().insertRow();
 d.columns.forEach(c=>{const th=document.createElement('th');th.textContent=c;h.appendChild(th)});const b=t.createTBody();
 d.rows.forEach(r=>{const tr=b.insertRow();r.forEach(v=>{const td=tr.insertCell();td.textContent=v===null?'NULL':String(v)})});
 o.replaceChildren(t);$('stats').textContent=d.row_count+' row(s)'+(d.truncated?' (capped at 500)':'')}
async function run(){try{render(await call('/db/query',{method:'POST',body:JSON.stringify({sql:$('sql').value})}));$('status').innerHTML=''}catch(e){msg(e.message,'err')}}
async function init(){if(!S||!S.access_token){msg('Sign in to the main app as an Admin first, then reopen this page.','err');return}
 try{const d=await call('/db/api/tables');const p=$('tables');d.tables.forEach(t=>{const b=document.createElement('button');b.textContent=t.name+' ('+t.rows+')';
  b.onclick=()=>{document.querySelectorAll('#tables button').forEach(x=>x.classList.remove('on'));b.classList.add('on');$('sql').value='SELECT * FROM "'+t.name+'" LIMIT 50';run()};p.appendChild(b)})}
 catch(e){msg(e.message+' (Admin or Super Admin role required)','err')}}
$('run').onclick=run;init();
</script></body></html>"""


@router.get("/db", response_class=HTMLResponse)
def db_explorer_page():
    return _PAGE
