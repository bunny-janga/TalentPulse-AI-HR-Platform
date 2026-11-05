import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.communication import ChatMessage
from app.models.policy import PolicyDocument
from app.services.genai.llm_client import llm_client
from app.services.genai.prompts import RAG_HELP_DESK_SYSTEM_PROMPT, RAG_HELP_DESK_USER_TEMPLATE

NOT_COVERED = "This question is not covered in current policy. Please contact HR Operations at hr@talentpulse.local for assistance."
MIN_SCORE = 0.06          # below this a passage is treated as unrelated (0.01 used to let nearly anything through)
MAX_QUERY_CHARS = 500

# The TF-IDF index only changes when policies change, so cache it keyed by a cheap signature.
_cache: Dict[str, Any] = {"sig": None, "chunks": [], "vectorizer": None, "matrix": None}


def _load_chunks(db: Session) -> Tuple[tuple, List[Dict[str, Any]]]:
    chunks, sig = [], []
    for doc in db.query(PolicyDocument).order_by(PolicyDocument.id).all():
        sig.append((doc.id, len(doc.chunks_json or "")))
        if not doc.chunks_json:
            continue
        try:
            for c in json.loads(doc.chunks_json):
                text = (c.get("text") or "").strip()
                if text:
                    chunks.append({"doc_id": doc.id, "title": c.get("title") or doc.title, "category": c.get("category") or doc.category, "text": text})
        except Exception:
            continue
    return tuple(sig), chunks


def _index(db: Session):
    sig, chunks = _load_chunks(db)
    if sig != _cache["sig"]:
        _cache.update(sig=sig, chunks=chunks, vectorizer=None, matrix=None)
        if chunks:
            vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
            try:
                _cache.update(vectorizer=vec, matrix=vec.fit_transform([c["text"] for c in chunks]))
            except ValueError:  # empty vocabulary
                _cache.update(chunks=[], vectorizer=None, matrix=None)
    return _cache


def retrieve_policy_chunks(query: str, db: Session, top_k: int = 4) -> List[Dict[str, Any]]:
    """Top-k passages by TF-IDF cosine similarity. No external vector database needed."""
    idx = _index(db)
    if not idx["chunks"] or idx["vectorizer"] is None:
        return []
    try:
        scores = cosine_similarity(idx["vectorizer"].transform([query]), idx["matrix"]).flatten()
    except Exception:
        return []
    out = []
    for i in np.argsort(scores)[::-1][:top_k]:
        score = float(scores[i])
        if score < MIN_SCORE:
            continue
        c = idx["chunks"][i]
        out.append({"title": c["title"], "category": c["category"], "snippet": c["text"][:300] + ("..." if len(c["text"]) > 300 else ""), "full_text": c["text"], "score": round(score, 3)})
    return out


_STOP = set("a an the of to in for is are was were be do does did can i my me we our you your how what when where which who whom why will would should could may might about on at by with from and or if it this that these those there their them as per get have has had any".split())


def _tokens(text: str) -> set:
    return {w[:5] for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP and len(w) > 2}


def extractive_answer(query: str, chunks: List[Dict[str, Any]]) -> str:
    """Offline answer built ONLY from retrieved text: the sentences that best overlap the question."""
    q = _tokens(query)
    scored = []
    for rank, c in enumerate(chunks[:3]):
        for sent in re.split(r"(?<=[.!?])\s+|\n+", c["full_text"]):
            sent = sent.strip(" -*•\t")
            if len(sent) < 25:
                continue
            overlap = len(q & _tokens(sent))
            if overlap:
                scored.append((overlap - rank * 0.25, c["title"], sent))
    if not scored:
        return NOT_COVERED
    scored.sort(key=lambda x: x[0], reverse=True)
    best_title = scored[0][1]
    same = [s for s in scored if s[1] == best_title]
    floor = max(1, same[0][0] - 1)   # keep only sentences about as relevant as the best one
    picked = [s for s in same if s[0] >= floor][:2]
    body = " ".join(p[2] for p in picked)
    if not llm_client.is_configured():
        return f"From [Source: {best_title}]: {body}\n\n(Live AI is not connected, so this is the matching text taken straight from the policy.)"
    return f"From [Source: {best_title}]: {body}"


GREETING_PATTERN = re.compile(
    r"^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|day)|howdy|sup|yo|what\s+can\s+you\s+do|who\s+are\s+you|help)\b",
    re.IGNORECASE,
)


def ask_policy_rag(query: str, user_id: int, db: Session) -> Dict[str, Any]:
    """Retrieve -> grounded prompt -> LLM (or an extractive fallback) -> persist."""
    query = query.strip()[:MAX_QUERY_CHARS]
    mode: str = "live" if llm_client.is_configured() else "offline"

    # Check for greetings / conversational pleasantries
    if GREETING_PATTERN.search(query):
        if llm_client.is_configured():
            prompt = (
                f"The employee just said: '{query}'. Reply as the TalentPulse AI HR Policy Assistant. "
                f"Warmly greet them and briefly offer help with leave policies, work-from-home rules, health insurance, attendance, or employee benefits."
            )
            text, gen_mode = llm_client.generate(
                prompt,
                system="You are the TalentPulse AI HR Helpdesk Assistant for an IT center in Visakhapatnam. Be concise (under 50 words), warm and professional.",
                temperature=0.3,
            )
            answer = text or "Hello! I am your TalentPulse HR Helpdesk Assistant. Ask me any question about company policies, leave entitlements, work-from-home rules, health insurance, or employee benefits."
            mode = gen_mode or mode
        else:
            answer = "Hello! I am your TalentPulse HR Helpdesk Assistant. Ask me any question about company policies, leave entitlements, work-from-home rules, health insurance, or employee benefits."
            mode = "offline"
        sources = []
    else:
        top_chunks = retrieve_policy_chunks(query, db, top_k=4)
        sources = [{"title": c["title"], "category": c["category"], "snippet": c["snippet"], "score": c["score"]} for c in top_chunks]

        if not top_chunks:
            answer = NOT_COVERED
            sources = []
            mode = "live" if llm_client.is_configured() else "offline"
        else:
            context = "\n\n".join(f"[Source Document: {c['title']} | Category: {c['category']}]\n{c['full_text']}" for c in top_chunks)
            text, mode = llm_client.generate(
                RAG_HELP_DESK_USER_TEMPLATE.format(context_chunks=context, query=query.replace("</question>", "")),
                system=RAG_HELP_DESK_SYSTEM_PROMPT, temperature=0.1,
            )
            answer = text if text else extractive_answer(query, top_chunks)
            if answer == NOT_COVERED:
                sources = []

    db.add(ChatMessage(user_id=user_id, query=query, response=answer, sources_json=json.dumps(sources), created_at=datetime.utcnow()))
    db.commit()
    return {"query": query, "answer": answer, "sources": sources, "mode": mode, "timestamp": datetime.utcnow()}
