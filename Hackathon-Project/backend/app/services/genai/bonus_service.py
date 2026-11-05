import re
from collections import Counter
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.survey import EngagementSurvey, SurveyResponse
from app.services.genai.llm_client import llm_client
from app.services.genai.prompts import DATA_RULE, SURVEY_SENTIMENT_THEMES_PROMPT

EXIT_INTERVIEW_PROMPT = """Role: {title} | Department: {department}

<notes>
{notes}
</notes>

From the notes only, write three short sections:
1. Primary reason for leaving
2. Work-environment factors that contributed
3. What leadership could have done six months earlier to keep this person"""

THEMES = {
    "Compensation": (("salary", "pay", "hike", "compensation", "bonus", "increment", "underpaid"), "Benchmark pay for the affected bands and communicate the review timeline."),
    "Workload and burnout": (("overtime", "deadline", "weekend", "on-call", "oncall", "burnout", "workload", "stress", "late night", "overload"), "Rebalance on-call rotas and track overtime per team."),
    "Career growth": (("promotion", "growth", "career", "learning", "training", "stagnat", "appraisal"), "Publish clear promotion criteria and run career conversations each half-year."),
    "Management and communication": (("manager", "leadership", "support", "feedback", "communication", "micromanag"), "Coach managers on regular 1-on-1s and feedback."),
    "Flexibility": (("hybrid", "remote", "wfh", "work from home", "flexible", "flexibility", "commute"), "Review the hybrid policy against what teams actually need."),
    "Team and culture": (("team", "culture", "collaborat", "friendly", "colleague", "environment"), "Keep doing what works; share team practices that score well."),
}


def offline_themes(comments: list) -> str:
    counts, example = Counter(), {}
    for c in comments:
        low = c.lower()
        for theme, (keys, _) in THEMES.items():
            if any(k in low for k in keys):
                counts[theme] += 1
                example.setdefault(theme, c.strip()[:140])
    if not counts:
        return "No clear themes found in the comments."
    lines = [f"- {t} ({n} of {len(comments)} comments), e.g. “{example[t]}”" for t, n in counts.most_common(4)]
    recs = [f"- {THEMES[t][1]}" for t, _ in counts.most_common(2)]
    return "Themes (keyword grouping, no live AI):\n" + "\n".join(lines) + "\n\nSuggested actions:\n" + "\n".join(recs)


def generate_survey_ai_themes(survey_id: int, db: Session) -> Dict[str, Any]:
    survey = db.query(EngagementSurvey).filter(EngagementSurvey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_id, SurveyResponse.comments != None).all()  # noqa: E711
    comments = [r.comments.strip() for r in responses if r.comments and len(r.comments.strip()) > 5]
    if not comments:
        return {"survey_id": survey_id, "survey_title": survey.title, "themes_summary": "Not enough written comments to find themes yet.", "total_analyzed": 0, "mode": "offline"}

    formatted = "\n".join(f"- {c[:400].replace('</comments>', '')}" for c in comments[:25])
    text, mode = llm_client.generate(
        SURVEY_SENTIMENT_THEMES_PROMPT.format(comments_text=formatted),
        system="You are a Chief People Officer analysing anonymous pulse-survey comments. " + DATA_RULE,
    )
    return {"survey_id": survey_id, "survey_title": survey.title, "total_analyzed": len(comments), "themes_summary": text or offline_themes(comments), "mode": mode}


def offline_exit_summary(notes: str) -> str:
    low = notes.lower()
    reasons = [("Compensation", ("salary", "pay", "offer", "hike", "ctc")), ("Career growth", ("promotion", "stuck", "stagnat", "growth", "same level")),
               ("Workload and burnout", ("overtime", "weekend", "on-call", "burnout", "stress", "deployment")), ("Management", ("manager", "micromanag", "feedback", "toxic")),
               ("Flexibility", ("remote", "hybrid", "commute", "relocat"))]
    hits = [name for name, keys in reasons if any(k in low for k in keys)]
    first = ", ".join(hits) if hits else "Not clear from the notes"
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", notes) if s.strip()][:3]
    return (f"1. Primary reason for leaving\n{hits[0] if hits else 'Not clear from the notes'}\n\n"
            f"2. Factors mentioned\n{first}. From the notes: " + " ".join(sentences) + "\n\n"
            "3. What could have been done earlier\nHold a stay-interview when these themes first appeared and act on them (offline summary: no live AI).")


def summarize_exit_interview(notes: str, title: str = "Software Engineer", department: str = "Engineering") -> Dict[str, Any]:
    text, mode = llm_client.generate(
        EXIT_INTERVIEW_PROMPT.format(title=title, department=department, notes=notes.replace("</notes>", "")),
        system="You are an HR retention analyst. Use only the notes. " + DATA_RULE,
    )
    return {"title": title, "department": department, "exit_summary": text or offline_exit_summary(notes), "mode": mode}
