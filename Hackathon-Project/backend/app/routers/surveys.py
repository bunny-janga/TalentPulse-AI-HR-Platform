from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.dependencies import require_authenticated, require_hr_or_admin
from app.models.survey import EngagementSurvey, SurveyResponse
from app.models.employee import Employee
from app.models.user import User
from app.schemas.survey import (
    SurveyCreate,
    SurveyResponseCreate,
    SurveyItemResponse,
    SurveyResultsResponse,
    SurveyFeedbackItem,
    SurveyStatusUpdate
)

router = APIRouter(prefix="/surveys", tags=["Engagement Surveys"])

def analyze_sentiment_baseline(text: Optional[str]) -> tuple[float, str]:
    """
    Fast rule-based lexicon scoring for survey feedback sentiment.
    Can be augmented by GenAI LLM in Phase 5.
    """
    if not text or not text.strip():
        return 0.0, "Neutral"

    pos_words = {"great", "good", "excellent", "supportive", "enjoying", "transparent", "helpful", "learning", "growth", "positive", "love", "flexible", "happy", "balanced"}
    neg_words = {"bad", "terrible", "poor", "overtime", "burnout", "micromanagement", "unfair", "undervalued", "delayed", "stress", "worst", "quit", "leaving", "toxic", "demotivated"}

    tokens = [w.strip(".,!?:;").lower() for w in text.split()]
    pos_count = sum(1 for t in tokens if t in pos_words)
    neg_count = sum(1 for t in tokens if t in neg_words)

    total = pos_count + neg_count
    if total == 0:
        return 0.0, "Neutral"

    score = round((pos_count - neg_count) / total, 2)
    if score > 0.2:
        label = "Positive"
    elif score < -0.2:
        label = "Negative"
    else:
        label = "Neutral"

    return score, label

@router.get("", response_model=List[SurveyItemResponse])
def list_surveys(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """List engagement surveys."""
    surveys = db.query(EngagementSurvey).order_by(EngagementSurvey.created_at.desc()).all()
    me = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    answered = set()
    if me:
        answered = {r[0] for r in db.query(SurveyResponse.survey_id).filter(SurveyResponse.employee_id == me.id).all()}
    results = []
    for s in surveys:
        count = db.query(SurveyResponse).filter(SurveyResponse.survey_id == s.id).count()
        results.append(SurveyItemResponse(
            id=s.id,
            title=s.title,
            description=s.description,
            is_active=s.is_active,
            created_by=s.created_by,
            created_at=s.created_at,
            response_count=count,
            has_responded=s.id in answered
        ))
    return results

@router.post("", response_model=SurveyItemResponse, status_code=status.HTTP_201_CREATED)
def create_survey(
    survey_in: SurveyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """Create a new company survey (HR/Admin only)."""
    survey = EngagementSurvey(
        title=survey_in.title,
        description=survey_in.description,
        is_active=survey_in.is_active,
        created_by=current_user.id
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return SurveyItemResponse(
        id=survey.id,
        title=survey.title,
        description=survey.description,
        is_active=survey.is_active,
        created_by=survey.created_by,
        created_at=survey.created_at,
        response_count=0
    )

@router.put("/{id}/status", response_model=SurveyItemResponse)
def set_survey_status(
    id: int,
    body: SurveyStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """Open or close a survey (HR/Admin only). Closed surveys stop accepting answers."""
    survey = db.query(EngagementSurvey).filter(EngagementSurvey.id == id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    survey.is_active = body.is_active
    db.commit()
    count = db.query(SurveyResponse).filter(SurveyResponse.survey_id == id).count()
    return SurveyItemResponse(id=survey.id, title=survey.title, description=survey.description, is_active=survey.is_active,
                              created_by=survey.created_by, created_at=survey.created_at, response_count=count)

@router.post("/{id}/respond", status_code=status.HTTP_201_CREATED)
def respond_to_survey(
    id: int,
    resp_in: SurveyResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    Submit employee response to an engagement survey.
    """
    survey = db.query(EngagementSurvey).filter(EngagementSurvey.id == id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    if not survey.is_active:
        raise HTTPException(status_code=400, detail="This survey is currently closed")

    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=400, detail="User does not have an employee profile")

    # Check if already responded
    existing = db.query(SurveyResponse).filter(
        SurveyResponse.survey_id == id,
        SurveyResponse.employee_id == emp.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already submitted a response for this survey")

    sent_score, sent_label = analyze_sentiment_baseline(resp_in.comments)

    new_resp = SurveyResponse(
        survey_id=id,
        employee_id=emp.id,
        score=resp_in.score,
        comments=resp_in.comments,
        sentiment_score=sent_score,
        sentiment_label=sent_label
    )
    db.add(new_resp)
    db.commit()
    db.refresh(new_resp)

    return {
        "message": "Survey response recorded successfully",
        "response_id": new_resp.id,
        "sentiment_detected": sent_label
    }

@router.get("/{id}/results", response_model=SurveyResultsResponse)
def get_survey_results(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """
    Get aggregated analytics and feedback for a survey (HR/Admin only).
    """
    survey = db.query(EngagementSurvey).filter(EngagementSurvey.id == id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == id).all()
    total = len(responses)

    if total == 0:
        return SurveyResultsResponse(
            survey_id=survey.id,
            title=survey.title,
            description=survey.description,
            is_active=survey.is_active,
            total_responses=0,
            average_score=0.0,
            score_distribution={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            sentiment_distribution={"Positive": 0, "Neutral": 0, "Negative": 0},
            feedback_samples=[]
        )

    avg_score = round(sum(r.score for r in responses) / total, 2)
    score_dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in responses:
        key = str(r.score)
        if key in score_dist:
            score_dist[key] += 1

    sent_dist = {"Positive": 0, "Neutral": 0, "Negative": 0}
    feedback_samples = []
    for r in responses:
        lbl = r.sentiment_label or "Neutral"
        if lbl in sent_dist:
            sent_dist[lbl] += 1
        if r.comments:
            feedback_samples.append(SurveyFeedbackItem(
                id=r.id,
                score=r.score,
                comments=r.comments,
                sentiment_score=r.sentiment_score,
                sentiment_label=r.sentiment_label,
                created_at=r.created_at
            ))

    return SurveyResultsResponse(
        survey_id=survey.id,
        title=survey.title,
        description=survey.description,
        is_active=survey.is_active,
        total_responses=total,
        average_score=avg_score,
        score_distribution=score_dist,
        sentiment_distribution=sent_dist,
        feedback_samples=feedback_samples[:15]
    )

@router.post("/{id}/ai-themes")
def get_survey_ai_themes(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """
    Bonus Feature: GenAI LLM sentiment theme synthesis and leadership recommendations.
    Restricted to HR and Admin.
    """
    from app.services.genai.bonus_service import generate_survey_ai_themes
    return generate_survey_ai_themes(survey_id=id, db=db)
