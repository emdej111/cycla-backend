from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    upload_date: datetime
    document_type: str | None
    affects_personalization: bool


class DocumentAnalysis(BaseModel):
    id: int
    filename: str
    claude_analysis: dict | None
    affects_personalization: bool


class DocumentList(BaseModel):
    documents: list[DocumentRead]
