import re
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.review import PerformanceReview
from app.models.user import User
from app.schemas.review import ReviewDraftResponse
from app.services.genai.llm_client import llm_client
from app.services.genai.prompts import REVIEW_DRAFT_SYSTEM_PROMPT, REVIEW_DRAFT_USER_TEMPLATE

RATING_LABEL = {5: "Exceptional", 4: "Exceeds expectations", 3: "Meets expectations", 2: "Needs improvement", 1: "Unsatisfactory"}

_HEADINGS = [
    ("summary", r"(?:overall\s+)?(?:performance\s+)?summary"),
    ("strengths", r"(?:key\s+)?strengths"),
    ("growth_areas", r"(?:areas?\s+(?:for|of)\s+(?:growth|improvement)|growth\s+areas?|development\s+areas?)"),
    ("goals", r"(?:key\s+)?goals(?:\s*(?:&|and)\s*(?:next\s+)?milestones)?|next\s+milestones"),
]
_HEAD_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\d+[\.\)]\s*)?(?:\*\*|__)?\s*(" + "|".join(f"(?P<{k}>{p})" for k, p in _HEADINGS) + r")\s*(?:\*\*|__)?\s*:?\s*(?:\*\*|__)?\s*(?P<rest>.*)$",
    re.IGNORECASE,
)


def parse_draft_sections(raw_text: str) -> Dict[str, str]:
    """Split LLM output into the four sections. Accepts '2. Strengths', '## Strengths', '**Strengths:**' and 'Strengths:' styles.
    A section the model did not write stays EMPTY: we no longer paper over it with invented filler text."""
    sections = {"summary": [], "strengths": [], "growth_areas": [], "goals": []}
    current: Optional[str] = None
    for line in raw_text.splitlines():
        m = _HEAD_RE.match(line)
        # A heading line is short; this avoids treating "Summary of work..." prose as a heading.
        if m and len(line.strip()) <= 80:
            current = next(k for k, _ in _HEADINGS if m.group(k))
            rest = (m.group("rest") or "").strip()
            if rest:
                sections[current].append(rest)
            continue
        if current:
            sections[current].append(line.rstrip())
    out = {k: "\n".join(v).strip() for k, v in sections.items()}
    if not any(out.values()):
        out["summary"] = raw_text.strip()
    return out


_GROWTH = ("improve", "needs", "need to", "should", "lacks", "lack ", "struggle", "weak", "late", "miss", "slow", "work on", "more ", "better")
_GOALS = ("goal", "next ", "will ", "plan", "target", "aim", "by q", "okr", "learn", "certif", "lead the", "take on")


def offline_draft(name: str, rating: int, cycle: str, notes: str) -> Dict[str, str]:
    """Deterministic structure-only draft used when no LLM is reachable. It re-files the manager's own bullets
    under the right headings and adds NO claims of its own."""
    bullets = [re.sub(r"^[\-\*\u2022\d\.\)\s]+", "", ln).strip() for ln in notes.splitlines()]
    bullets = [b for b in bullets if len(b) > 2]
    strengths: List[str] = []
    growth: List[str] = []
    goals: List[str] = []
    for b in bullets:
        low = b.lower()
        if any(k in low for k in _GOALS):
            goals.append(b)
        elif any(k in low for k in _GROWTH):
            growth.append(b)
        else:
            strengths.append(b)
    fmt = lambda xs: "\n".join(f"- {x}" for x in xs)
    summary = f"{name} was rated {rating}/5 ({RATING_LABEL.get(rating, '')}) for {cycle}."
    if bullets:
        summary += " Key observations from the manager: " + "; ".join(bullets[:4]).rstrip(".") + "."
    return {"summary": summary, "strengths": fmt(strengths), "growth_areas": fmt(growth), "goals": fmt(goals)}


def generate_review_draft_for_employee(
    employee_id: int, bullet_notes: str, review_cycle: Optional[str], rating: Optional[int], current_user: User, db: Session
) -> ReviewDraftResponse:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp_user = emp.user
    is_direct_mgr = bool(emp_user and emp_user.manager_id == current_user.id)
    is_hr_admin = current_user.role.lower() in ("admin", "hr", "superadmin")
    if not (is_direct_mgr or is_hr_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only the assigned manager or HR can generate an AI review draft")
    if emp.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot draft a review for yourself.")

    rating = int(rating) if rating else int(round(emp.performance_rating or 3))
    rating = min(max(rating, 1), 5)
    cycle = review_cycle or "current cycle"
    name = emp_user.full_name if emp_user else "The employee"
    dept = emp_user.department.name if (emp_user and emp_user.department) else "Engineering"

    prompt = REVIEW_DRAFT_USER_TEMPLATE.format(
        employee_name=name, job_title=emp.job_title, department=dept, rating=rating, review_cycle=cycle,
        bullet_notes=bullet_notes.replace("</notes>", ""),
    )
    raw, mode = llm_client.generate(prompt, system=REVIEW_DRAFT_SYSTEM_PROMPT, temperature=0.3)
    parsed = parse_draft_sections(raw) if raw else offline_draft(name, rating, cycle, bullet_notes)

    return ReviewDraftResponse(
        draft_review=raw or "\n\n".join(f"{t}\n{parsed[k]}" for t, k in (("Summary", "summary"), ("Strengths", "strengths"), ("Areas for Growth", "growth_areas"), ("Goals", "goals"))),
        summary=parsed["summary"], strengths=parsed["strengths"], growth_areas=parsed["growth_areas"], goals=parsed["goals"], mode=mode,
    )


def generate_review_draft(review_id: int, bullet_notes: str, current_user: User, db: Session) -> ReviewDraftResponse:
    """Legacy path /reviews/{id}/ai-draft: `id` is a REVIEW id only (it used to fall back to an employee id, which
    could silently pick the wrong person when the two id spaces collided)."""
    review = db.query(PerformanceReview).filter(PerformanceReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail=f"Review #{review_id} not found. To draft before saving, use POST /reviews/draft.")
    return generate_review_draft_for_employee(review.employee_id, bullet_notes, review.review_cycle, review.rating, current_user, db)
