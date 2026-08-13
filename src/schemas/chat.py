from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.models.chat import ChatRole


class ChatMessageCreate(BaseModel):
    message: str


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: ChatRole
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    reply: str
    disclaimer: str


class ChatHistory(BaseModel):
    messages: list[ChatMessageRead]
