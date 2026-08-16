from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.models.chat import ChatRole


class ChatMessageCreate(BaseModel):
    message: str
    persist: bool = True
    """Whether to save this exchange to the user's chat history.

    Set to False for one-off/internal prompts (e.g. generating a
    personalized home-screen insight) that shouldn't appear in the
    user-facing Coach conversation history.
    """


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
