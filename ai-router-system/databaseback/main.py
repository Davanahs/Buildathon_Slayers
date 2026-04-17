"""
FastAPI application — AI Router System.

Startup:
  - Creates all 3 tables (model_registry, bandit_model_stats, prompt_memory)
  - Seeds model_registry with known models

Endpoints:
  POST /chat       — route a prompt through the full pipeline
  POST /feedback   — submit thumbs-up/down (feeds bandit)
  GET  /models     — list registry models (filterable)
  GET  /health     — health + DB status
  GET  /stats      — bandit performance stats
"""

import os
import sys
import traceback
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(override=True)

# Ensure sibling imports work when running `uvicorn main:app` from backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import (
    ChatRequest, ChatResponse,
    FeedbackRequest, FeedbackResponse,
    DiscoverRequest, DiscoveryStatusResponse,
    ModelInfo, ModelListResponse,
    HealthResponse,
    BanditStatsItem, BanditStatsResponse,
)
from db import get_conn, fetch_one, fetch_all
from router import route_prompt
from bandit import record_outcome, get_all_stats
from model_registry_db import create_model_registry_table, get_model_count
from bandit_db import create_bandit_table
from vector_db import create_prompt_memory_table, get_memory_by_id
from librarian import discover_all


# ─── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting AI Router System...")

    try:
        create_model_registry_table()
    except Exception as e:
        print(f"⚠️  model_registry: {e}")

    try:
        create_bandit_table()
    except Exception as e:
        print(f"⚠️  bandit_model_stats: {e}")

    try:
        create_prompt_memory_table()
    except Exception as e:
        print(f"⚠️  prompt_memory: {e}")

    # Check if discovery is needed — only runs when:
    #   1. API key has changed since last run, OR
    #   2. 30 days have passed since last run
    # On normal restarts this is a no-op (just reads discovery_state.json).
    try:
        results = discover_all(use_llm=False)
        ran = {p: c for p, c in results.items() if c > 0}
        if ran:
            print(f"📊 Discovery ran for: {ran}")
        else:
            print("⏭️  Discovery skipped — registry is up to date")
    except Exception as e:
        print(f"⚠️  Discovery check failed: {e}")

    print("✅ AI Router System ready")
    yield
    print("👋 Shutting down")


# ─── App ──────────────────────────────────────────────────────

app = FastAPI(
    title="AI Router System",
    description="Intelligent multi-model router with Thompson Sampling bandit.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── GET /health ──────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    db = "unknown"
    try:
        conn = get_conn()
        conn.close()
        db = "connected"
    except Exception as e:
        db = f"error: {str(e)[:80]}"

    return HealthResponse(
        status="healthy" if db == "connected" else "degraded",
        database=db,
    )


# ─── POST /chat ──────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Full pipeline: classify → complexity → registry → bandit → call → store."""
    try:
        result = route_prompt(
            prompt=req.prompt,
        )
        return ChatResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)[:200])


# ─── POST /feedback ───────────────────────────────────────────

@app.post("/feedback", response_model=FeedbackResponse)
async def feedback(req: FeedbackRequest):
    """Record thumbs-up/down → update bandit_model_stats."""
    if req.feedback not in (-1, 1):
        raise HTTPException(400, "feedback must be 1 or -1")

    memory = get_memory_by_id(req.memory_id)
    if not memory:
        raise HTTPException(404, f"memory_id {req.memory_id} not found")

    try:
        reward = record_outcome(
            model_name=memory["model_used"],
            provider=memory.get("provider", "unknown"),
            category=memory.get("category", "chat"),
            feedback=req.feedback,
            response_time_ms=memory.get("response_time_ms", 0),
            cost=memory.get("actual_cost", 0.0),
        )
        return FeedbackResponse(success=True, message=f"Recorded. Reward={reward:.4f}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e)[:200])


# ─── GET /models ──────────────────────────────────────────────

@app.get("/models", response_model=ModelListResponse)
async def list_models(
    category: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List models in the registry with optional filters."""
    conditions, params = [], []

    if active_only:
        conditions.append("is_active = TRUE")
    if category:
        conditions.append("category = %s")
        params.append(category)
    if provider:
        conditions.append("provider = %s")
        params.append(provider)

    where = " AND ".join(conditions) if conditions else "TRUE"

    total_row = fetch_one(
        f"SELECT COUNT(*) AS cnt FROM model_registry WHERE {where};",
        tuple(params),
    )
    total = total_row["cnt"] if total_row else 0

    rows = fetch_all(
        f"""SELECT id, model_name, provider, category, tier, sub_tier,
                   complexity_min, complexity_max,
                   cost_per_1k_input, cost_per_1k_output,
                   avg_latency_ms, context_window, is_active
            FROM model_registry WHERE {where}
            ORDER BY priority_rank ASC, model_name ASC
            LIMIT %s OFFSET %s;""",
        tuple(params) + (limit, offset),
    )

    models = [
        ModelInfo(
            id=r["id"],
            model_name=r["model_name"],
            provider=r["provider"],
            category=r["category"],
            tier=r["tier"],
            sub_tier=r.get("sub_tier"),
            complexity_min=r["complexity_min"],
            complexity_max=r["complexity_max"],
            cost_per_1k_input=float(r.get("cost_per_1k_input") or 0),
            cost_per_1k_output=float(r.get("cost_per_1k_output") or 0),
            avg_latency_ms=r.get("avg_latency_ms") or 0,
            context_window=r.get("context_window") or 0,
            is_active=r.get("is_active", True),
        )
        for r in rows
    ]
    return ModelListResponse(models=models, total=total)


# ─── POST /discover ──────────────────────────────────────────

@app.post("/discover", response_model=DiscoveryStatusResponse)
async def trigger_discovery(req: DiscoverRequest):
    """
    Trigger the librarian to fetch models and run global categorical curation.
    """
    try:
        results = discover_all(use_llm=False, force=True)
        total = sum(results.values()) if results else 0
        return DiscoveryStatusResponse(
            provider="all",
            status="completed",
            models_found=total,
            message=f"Global catalog discovery complete: {results}",
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e)[:200])


# ─── GET /stats ───────────────────────────────────────────────

@app.get("/stats", response_model=BanditStatsResponse)
async def stats():
    """Bandit performance statistics."""
    rows = get_all_stats()
    items = [
        BanditStatsItem(
            model_name=r["model_name"],
            provider=r.get("provider", ""),
            category=r.get("category", ""),
            total_trials=r.get("total_trials", 0),
            success_count=r.get("success_count", 0),
            failure_count=r.get("failure_count", 0),
            avg_reward=float(r.get("avg_reward", 0)),
            avg_latency_ms=float(r.get("avg_latency_ms", 0)),
        )
        for r in rows
    ]
    return BanditStatsResponse(stats=items, total_models=len(items))


# ─── Direct run ───────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)