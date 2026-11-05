import os
import re
import uuid
import json
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pypdf import PdfReader

from app.db.session import get_db
from app.core.config import settings
from app.core.dependencies import require_authenticated, require_hr_or_admin
from app.models.policy import PolicyDocument
from app.models.user import User
from app.schemas.policy import PolicyResponse, PolicyDetailResponse, PolicyCreate

router = APIRouter(prefix="/policies", tags=["Policy Helpdesk"])

def chunk_text(text: str, target_words: int = 350) -> List[str]:
    """
    Chunks text into roughly 300-500 word passages preserving paragraph structure.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current_chunk = []
    current_word_count = 0

    for para in paragraphs:
        words = para.split()
        if current_word_count + len(words) > target_words and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_word_count = len(words)
        else:
            current_chunk.append(para)
            current_word_count += len(words)

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks if chunks else [text]

def map_policy_summary(doc: PolicyDocument, include_text: bool = True) -> PolicyResponse:
    chunks = []
    try:
        chunks = json.loads(doc.chunks_json) if doc.chunks_json else []
    except Exception:
        pass
    return PolicyResponse(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        file_path=doc.file_path,
        extracted_text=doc.extracted_text if include_text else "",
        chunk_count=len(chunks),
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )

@router.get("", response_model=List[PolicyResponse])
def list_policies(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    List all uploaded company policies. Accessible by all authenticated employees.
    """
    query = db.query(PolicyDocument)
    if category:
        query = query.filter(PolicyDocument.category.ilike(f"%{category.strip()}%"))
    policies = query.order_by(PolicyDocument.created_at.desc()).all()
    return [map_policy_summary(p, include_text=False) for p in policies]  # list stays light; GET /{id} has the text

@router.get("/{id}", response_model=PolicyDetailResponse)
def get_policy(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """Get single policy document with chunks."""
    doc = db.query(PolicyDocument).filter(PolicyDocument.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Policy document not found")
    
    chunks = []
    try:
        chunks = json.loads(doc.chunks_json) if doc.chunks_json else []
    except Exception:
        pass

    summary = map_policy_summary(doc)
    return PolicyDetailResponse(
        **summary.model_dump(),
        chunks=chunks
    )

@router.post("/upload", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def upload_policy_pdf(
    title: str = Form(...),
    category: str = Form(...),
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """
    Upload and index an HR policy document (PDF or Text). HR/Admin only.
    Extracts text, segments into 300-500 word passages, and prepares TF-IDF chunks.
    """
    title = title.strip()
    category = category.strip()
    if len(title) < 3 or len(title) > 255:
        raise HTTPException(status_code=422, detail="Title must be 3-255 characters.")
    if not category or len(category) > 100:
        raise HTTPException(status_code=422, detail="Category is required (max 100 characters).")

    extracted_text = ""
    saved_file_path = None
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024

    if file and file.filename:
        ext = os.path.splitext(os.path.basename(file.filename))[1].lower()
        if ext not in (".pdf", ".txt", ".md"):
            raise HTTPException(status_code=415, detail="Only .pdf, .txt and .md files are supported.")
        file_bytes = await file.read(max_bytes + 1)
        if len(file_bytes) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File is larger than {settings.MAX_UPLOAD_MB} MB.")

        if ext == ".pdf":
            if not file_bytes.startswith(b"%PDF"):
                raise HTTPException(status_code=422, detail="That file is not a valid PDF.")
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                extracted_text = "\n\n".join(t for t in (p.extract_text() for p in reader.pages) if t)
            except Exception:
                raise HTTPException(status_code=422, detail="Could not read this PDF (it may be encrypted or corrupt).")
            if not extracted_text.strip():
                raise HTTPException(status_code=422, detail="No text found in this PDF. Scanned images need OCR first.")
        else:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")

        # Never trust the client's filename: a random name stops path traversal ("../../x") and collisions.
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", os.path.splitext(os.path.basename(file.filename))[0])[:40] or "policy"
        saved_file_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex[:12]}_{safe_stem}{ext}")
        with open(saved_file_path, "wb") as f:
            f.write(file_bytes)
    elif raw_text and raw_text.strip():
        if len(raw_text) > 200_000:
            raise HTTPException(status_code=413, detail="Pasted text is too long (200,000 characters max).")
        extracted_text = raw_text.strip()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide a PDF/text file or paste the policy text.")

    if len(extracted_text.strip()) < 30:
        raise HTTPException(status_code=422, detail="The policy text is too short to be useful (30 characters minimum).")

    # Chunk into 300-500 word passages
    text_chunks = chunk_text(extracted_text, target_words=350)
    chunk_objs = []
    for idx, c_text in enumerate(text_chunks):
        chunk_objs.append({
            "chunk_id": idx + 1,
            "title": title,
            "category": category,
            "text": c_text
        })

    new_doc = PolicyDocument(
        title=title,
        category=category,
        file_path=saved_file_path,
        extracted_text=extracted_text,
        chunks_json=json.dumps(chunk_objs),
        uploaded_by=current_user.id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return map_policy_summary(new_doc)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """Remove a policy from the library (HR/Admin). The helpdesk stops citing it immediately."""
    doc = db.query(PolicyDocument).filter(PolicyDocument.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Policy document not found")
    if doc.file_path:
        try:
            upload_root = os.path.realpath(settings.UPLOAD_DIR)
            target = os.path.realpath(doc.file_path)
            if target.startswith(upload_root + os.sep) and os.path.exists(target):
                os.remove(target)
        except OSError:
            pass
    db.delete(doc)
    db.commit()
    return None
