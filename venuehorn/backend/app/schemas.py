from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentIn(BaseModel):
    text: str = Field(..., min_length=1)
    source: Optional[str] = None


class IngestRequest(BaseModel):
    documents: List[DocumentIn]


class IngestResponse(BaseModel):
    chunks_added: int
    documents_received: int


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = 6


class SearchHit(BaseModel):
    text: str
    source: Optional[str]
    score: float


class SearchResponse(BaseModel):
    hits: List[SearchHit]


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = 6


class ChatResponse(BaseModel):
    answer: str
    hits: List[SearchHit]
