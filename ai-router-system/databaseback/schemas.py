"""
Pydantic schemas for the AI Router System API.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# ─── Requests ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The message you want to send to the AI router.")


class FeedbackRequest(BaseModel):
    memory_id: int
    feedback: int = Field(..., description="+1 thumbs-up, -1 thumbs-down")
    notes: Optional[str] = None


class DiscoverRequest(BaseModel):
    provider: Optional[str] = None   # gemini | groq | openrouter | None=all


class DiscoveryStatusResponse(BaseModel):
    provider: str
    status: str
    models_found: int
    message: str


# ─── Responses ────────────────────────────────────────────────

class ChatResponse(BaseModel):
    response: str
    model_used: str
    provider: str
    category: str
    complexity_score: int
    response_time_ms: int
    estimated_cost: float = 0.0
    memory_id: Optional[int] = None
    session_id: Optional[str] = None
    # Routing metadata
    cache_hit: bool = False            # True if response came from prompt_memory
    similarity: Optional[float] = None # cosine similarity score on cache hit
    selector: Optional[str] = None     # 'librarian' | 'bandit' | 'cache'
    confidence: Optional[float] = None # librarian confidence score (0-1)


class FeedbackResponse(BaseModel):
    success: bool
    message: str


class ModelInfo(BaseModel):
    id: int
    model_name: str
    provider: str
    category: str
    tier: int
    sub_tier: Optional[str] = None
    complexity_min: int
    complexity_max: int
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    avg_latency_ms: int = 0
    context_window: int = 0
    is_active: bool = True


class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    total: int


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str = "1.0.0"


class BanditStatsItem(BaseModel):
    model_name: str
    provider: str
    category: str
    total_trials: int
    success_count: int
    failure_count: int
    avg_reward: float
    avg_latency_ms: float


class BanditStatsResponse(BaseModel):
    stats: List[BanditStatsItem]
    total_models: int
