from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, Field

app = FastAPI(title="Azure Architecture Assistant Backend")


class GenerateRequest(BaseModel):
    context: str = Field(..., min_length=1, description="Solution context text")


class GenerateResponse(BaseModel):
    summary: str
    components: List[str]
    generated_at: str


class ReviewResponse(BaseModel):
    filename: str
    notes: str
    generated_at: str


@app.post("/generate", response_model=GenerateResponse)
async def generate_architecture(payload: GenerateRequest) -> GenerateResponse:
    summary = (
        "High-level Azure solution: combine a frontend experience, API layer, "
        "data storage, and monitoring. Tailor services to the context provided."
    )
    components = [
        "User-facing UI (Streamlit or web app)",
        "API gateway or service layer",
        "Compute (App Service, Functions, or AKS)",
        "Data storage (Azure SQL, Cosmos DB, or Blob Storage)",
        "Observability (Azure Monitor, Application Insights)",
    ]
    return GenerateResponse(
        summary=summary,
        components=components,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/review", response_model=ReviewResponse)
async def review_document(document: UploadFile = File(...)) -> ReviewResponse:
    notes = (
        "Review completed. Ensure the document covers identity, networking, "
        "security, reliability, and cost management considerations."
    )
    return ReviewResponse(
        filename=document.filename or \"uploaded_document\",
        notes=notes,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
