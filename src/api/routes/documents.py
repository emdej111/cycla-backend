import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.security import get_current_user
from src.db.database import get_db
from src.models.document import MedicalDocument
from src.models.user import User
from src.schemas.document import DocumentAnalysis, DocumentList, DocumentRead
from src.services.claude_service import analyze_medical_document

router = APIRouter(prefix="/documents", tags=["documents"])

_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}


def _extract_text(file_path: Path, content_type: str) -> str:
    if content_type == "application/pdf":
        import pdfplumber

        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    # Image OCR is out of scope for this service; store a placeholder so the
    # document is still recorded and can be reviewed manually.
    return ""


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    document_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRead:
    settings = get_settings()
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )

    contents = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb}MB limit",
        )

    upload_dir = Path(settings.upload_dir) / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{file.filename}"
    storage_path = upload_dir / stored_name
    storage_path.write_bytes(contents)

    document = MedicalDocument(
        user_id=current_user.id,
        filename=file.filename or stored_name,
        storage_path=str(storage_path),
        document_type=document_type,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        text = _extract_text(storage_path, file.content_type)
        if text.strip():
            analysis = analyze_medical_document(text, current_user.gynecological_profile)
            document.claude_analysis = analysis
            document.affects_personalization = bool(analysis.get("flags"))
            db.add(document)
            db.commit()
            db.refresh(document)
    except Exception:
        # Upload succeeds even if AI analysis fails; the document is still
        # stored and can be re-analyzed or reviewed manually.
        pass

    return DocumentRead.model_validate(document)


@router.get("/", response_model=DocumentList)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentList:
    stmt = (
        select(MedicalDocument)
        .where(MedicalDocument.user_id == current_user.id)
        .order_by(MedicalDocument.upload_date.desc())
    )
    documents = list(db.execute(stmt).scalars().all())
    return DocumentList(documents=[DocumentRead.model_validate(d) for d in documents])


@router.get("/{document_id}/analysis", response_model=DocumentAnalysis)
def get_document_analysis(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentAnalysis:
    document = db.get(MedicalDocument, document_id)
    if document is None or document.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentAnalysis.model_validate(document)
