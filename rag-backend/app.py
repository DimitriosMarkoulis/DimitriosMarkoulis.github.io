import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

from prompts import ANSWER_TEMPLATE, SYSTEM_PROMPT
from retriever import format_context, rebuild_index, retrieve

load_dotenv()

client = OpenAI()
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "https://dimitriosmarkoulis.github.io,http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="Dimitrios Markoulis Portfolio RAG Assistant",
    version="1.0.0",
    description="RAG backend that answers questions from Dimitrios' GitHub project documentation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1200)
    top_k: int = Field(default=5, ge=1, le=8)


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "portfolio-rag-assistant"}


@app.post("/api/reindex")
async def reindex() -> dict[str, Any]:
    try:
        return await rebuild_index()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        retrieved = retrieve(request.message, top_k=request.top_k)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Vector index not built yet. Run POST /api/reindex before chatting.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    context = format_context(retrieved)
    response = client.responses.create(
        model=CHAT_MODEL,
        instructions=SYSTEM_PROMPT,
        input=ANSWER_TEMPLATE.format(context=context, question=request.message),
        max_output_tokens=650,
    )

    source_summaries = [
        {
            "project": item.get("project"),
            "repo": item.get("repo"),
            "url": item.get("url"),
            "source_path": item.get("source_path"),
            "score": round(float(item.get("score", 0)), 4),
        }
        for item in retrieved
    ]

    return ChatResponse(answer=response.output_text, sources=source_summaries)
