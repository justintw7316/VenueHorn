from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import (
    ChatRequest,
    ChatResponse,
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
    SearchHit,
)
from .vector_store import vector_store
from openai import OpenAI

app = FastAPI(title="VenueHorn AI Search")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=settings.openai_api_key)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest) -> IngestResponse:
    docs = [(doc.text, doc.source) for doc in request.documents]
    chunks_added = vector_store.add_documents(docs)
    return IngestResponse(
        chunks_added=chunks_added,
        documents_received=len(request.documents),
    )


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    hits = vector_store.search(request.query, request.k)
    return SearchResponse(
        hits=[
            SearchHit(text=chunk.text, source=chunk.source, score=score)
            for chunk, score in hits
        ]
    )


def _format_context(hits: list[SearchHit]) -> str:
    sections = []
    for idx, hit in enumerate(hits, start=1):
        source = hit.source or "unknown"
        sections.append(f"[{idx}] ({source}) {hit.text}")
    return "\n\n".join(sections)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    hits_raw = vector_store.search(request.query, request.k)
    hits = [
        SearchHit(text=chunk.text, source=chunk.source, score=score)
        for chunk, score in hits_raw
    ]

    context = _format_context(hits)
    system_prompt = (
        "You are VenueHorn AI, a helpful assistant specializing in finding the perfect venues "
        "and vendors for events like weddings, corporate events, and celebrations. "
        "Use the provided venue information to answer user questions accurately. "
        "If the context doesn't contain enough information to answer, say so politely and "
        "ask clarifying questions to help narrow down their search."
    )
    user_message = f"Question: {request.query}\n\nAvailable Venues:\n{context}"

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=1000,
    )
    answer = response.choices[0].message.content
    return ChatResponse(answer=answer, hits=hits)
