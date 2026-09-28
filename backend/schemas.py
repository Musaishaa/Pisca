from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(max_length=4000)
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    memory_used: bool
    conversation_id: int


class MemoryCreate(BaseModel):
    category: str = Field(default="personal", min_length=1, max_length=80)
    key: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=4000)
    source: str = Field(default="user", max_length=40)


class MemoryUpdate(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    key: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=4000)


class MemoryResponse(MemoryCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    preview: str = ""


class HealthResponse(BaseModel):
    status: str
    provider: str
    model: str
