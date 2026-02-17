"""
VenueHorn AI — FastAPI application entry point.

Endpoint summary
----------------
GET  /health          — liveness probe
GET  /status          — index stats (chunk count, sources)
POST /ingest          — add venue documents to the vector index
POST /search          — raw vector similarity search
POST /chat            — conversational AI with full session memory
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError

from .config import settings
from .conversation import conversation_store
from .exceptions import (
    openai_api_handler,
    openai_connection_handler,
    openai_rate_limit_handler,
)
from .schemas import (
    ChatRequest,
    ChatResponse,
    IngestRequest,
    IngestResponse,
    SearchHit,
    SearchRequest,
    SearchResponse,
)
from .vector_store import vector_store

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("venuehorn")

# ---------------------------------------------------------------------------
# Lifespan — clean startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "VenueHorn starting up | env=%s | chunks=%d | sources=%d",
        settings.environment,
        vector_store.total_chunks,
        vector_store.total_sources,
    )
    yield
    logger.info("VenueHorn shutting down — flushing vector store…")
    vector_store.flush()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VenueHorn AI",
    description="Conversational venue-discovery API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Register OpenAI error handlers so they return clean JSON instead of 500
app.add_exception_handler(RateLimitError, openai_rate_limit_handler)
app.add_exception_handler(APIStatusError, openai_api_handler)
app.add_exception_handler(APIConnectionError, openai_connection_handler)

# Shared async OpenAI client (one connection pool for the whole process)
_openai = AsyncOpenAI(
    api_key=settings.openai_api_key,
    max_retries=settings.openai_max_retries,
)

# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s → %d  (%.0f ms)", request.method, request.url.path, response.status_code, ms)
    return response

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are VenueHorn, an expert event-venue concierge for the United States.
Your job is to help customers find and book the ideal venue or vendor for their event.

Guidelines:
- Be warm, professional, and specific. Never give vague answers.
- When venues are provided in the context, recommend them by name, location, and relevant details.
- If multiple venues fit, compare them briefly (capacity, style, price tier, standout features).
- If no venue in the context matches well, say so honestly and ask one targeted clarifying question.
- Remember details the customer has shared earlier in the conversation.
- Never make up venue names, phone numbers, addresses, or prices.
- Keep responses concise: 3–6 sentences unless the customer explicitly asks for more detail.
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_context(hits: list[SearchHit]) -> str:
    if not hits:
        return "No venue information available for this query."
    parts = []
    for i, hit in enumerate(hits, 1):
        source = hit.source or "Unknown"
        parts.append(f"[{i}] {source}\n{hit.text}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Ops"])
async def health() -> dict:
    return {"status": "ok"}


@app.get("/status", tags=["Ops"])
async def status() -> dict:
    return {
        "total_chunks": vector_store.total_chunks,
        "total_sources": vector_store.total_sources,
        "model": settings.openai_model,
        "embedding_model": settings.openai_embedding_model,
        "environment": settings.environment,
    }


@app.post("/ingest", response_model=IngestResponse, tags=["Data"])
async def ingest(request: IngestRequest) -> IngestResponse:
    docs = [(doc.text, doc.source) for doc in request.documents]
    chunks_added = await vector_store.add_documents(docs)
    vector_store.flush()
    logger.info("Ingested %d docs → %d new chunks", len(docs), chunks_added)
    return IngestResponse(chunks_added=chunks_added, documents_received=len(docs))


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest) -> SearchResponse:
    hits_raw = await vector_store.search(request.query, request.k)
    return SearchResponse(
        hits=[SearchHit(text=c.text, source=c.source, score=s) for c, s in hits_raw]
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    # 1. Resolve or create conversation
    conversation = conversation_store.get_or_create(request.conversation_id)

    # 2. Retrieve relevant venue context
    hits_raw = await vector_store.search(request.query, request.k)
    hits = [SearchHit(text=c.text, source=c.source, score=s) for c, s in hits_raw]
    context = _format_context(hits)

    # 3. Build message list: system + history + new user turn
    user_message = (
        f"{request.query}\n\n"
        f"--- Relevant Venues ---\n{context}"
    )
    messages = (
        [{"role": "system", "content": _SYSTEM_PROMPT}]
        + conversation.messages
        + [{"role": "user", "content": user_message}]
    )

    # 4. Call LLM
    response = await _openai.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        temperature=settings.chat_temperature,
        max_tokens=settings.chat_max_tokens,
    )
    answer = response.choices[0].message.content or ""

    # 5. Persist both turns to conversation history
    conversation.append("user", request.query)   # store clean query, not venue context
    conversation.append("assistant", answer)
    conversation_store.save(conversation)

    logger.info(
        "chat cid=%s turn=%d tokens_used=%d",
        conversation.id,
        conversation.turn,
        response.usage.total_tokens if response.usage else 0,
    )

    return ChatResponse(
        answer=answer,
        conversation_id=conversation.id,
        hits=hits,
        turn=conversation.turn,
    )
