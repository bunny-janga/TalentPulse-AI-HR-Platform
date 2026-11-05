from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from app.db.session import get_db
from app.core.dependencies import require_authenticated
from app.models.user import User
from app.models.communication import ChatMessage
from app.schemas.policy import ChatAskRequest, ChatAskResponse, ChatSourceCitation
from app.services.genai.llm_client import llm_client
from app.services.genai.rag_service import ask_policy_rag

router = APIRouter(prefix="/chat", tags=["Policy Helpdesk"])

@router.post("/ask", response_model=ChatAskResponse)
def ask_hr_helpdesk(
    chat_in: ChatAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    GenAI 1: HR Policy RAG Helpdesk.
    Retrieves top 3-4 policy chunks using TF-IDF vectors, queries Gemini LLM
    with strict grounded instructions to cite policy document titles or reply
    'not covered in current policy'.
    Persists Q&A into chat_messages table.
    """
    if not chat_in.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = ask_policy_rag(
        query=chat_in.query.strip(),
        user_id=current_user.id,
        db=db
    )
    return ChatAskResponse(**result)

@router.get("/history", response_model=List[ChatAskResponse])
def get_my_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    Get past HR Helpdesk Q&A interactions for current authenticated user.
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(20).all()

    results = []
    for m in messages:
        sources = []
        if m.sources_json:
            try:
                sources = json.loads(m.sources_json)
            except Exception:
                pass
        results.append(ChatAskResponse(
            query=m.query,
            answer=m.response,
            sources=[ChatSourceCitation(**s) for s in sources],
            mode="live" if llm_client.is_configured() else "offline",
            timestamp=m.created_at
        ))
    return results

@router.delete("/history")
def clear_my_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    Clear past HR Helpdesk chat interactions for current authenticated user.
    """
    db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).delete()
    db.commit()
    return {"status": "cleared", "message": "Chat history cleared successfully"}
