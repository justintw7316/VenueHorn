from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from .config import settings


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

class DocumentIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)
    source: Optional[str] = Field(default=None, max_length=500)


class IngestRequest(BaseModel):
    documents: List[DocumentIn] = Field(..., min_length=1, max_length=500)


class IngestResponse(BaseModel):
    chunks_added: int
    documents_received: int


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=settings.max_input_length)
    k: int = Field(default=6, ge=1, le=20)


class SearchHit(BaseModel):
    text: str
    source: Optional[str]
    score: float


class SearchResponse(BaseModel):
    hits: List[SearchHit]


# ---------------------------------------------------------------------------
# Chat (stateful conversation)
# ---------------------------------------------------------------------------

class Message(BaseModel):
    """A single turn in the conversation."""
    role: str          # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=settings.max_input_length)
    conversation_id: Optional[str] = Field(
        default=None,
        description="Omit on first message; include on follow-ups to continue the conversation.",
    )
    k: int = Field(default=6, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    hits: List[SearchHit]
    turn: int = Field(description="Which turn of the conversation this is (1-indexed).")
