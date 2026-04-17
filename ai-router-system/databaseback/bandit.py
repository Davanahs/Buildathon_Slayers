"""
Thompson Sampling bandit for adaptive model selection.

Standalone module — imports only from db.py.
Each model+category pair is an 'arm' in bandit_model_stats.
"""

import random
from typing import Optional, List, Dict, Any, Tuple

from db import fetch_one, fetch_all, execute


# ─── Config ───────────────────────────────────────────────────

ALPHA_PRIOR = 1.0   # Beta prior (success)
BETA_PRIOR = 1.0    # Beta prior (failure)
EXPLORATION_BONUS = 0.05  # Extra score for under-explored arms

# Reward weights
W_FEEDBACK = 0.5
W_LATENCY = 0.3
W_COST = 0.2


# ─── Reward computation ──────────────────────────────────────

def compute_reward(
    feedback: int,
    response_time_ms: int = 0,
    cost: float = 0.0,
    max_latency: int = 5000,
    max_cost: float = 0.05,
) -> float:
    """
    Composite reward in [0, 1]:
      feedback_score:  1 if thumbs-up, 0 if thumbs-down
      latency_score:   1 if instant → 0 at max_latency
      cost_score:      1 if free → 0 at max_cost
    """
    fb = 1.0 if feedback == 1 else 0.0
    lat = max(0.0, 1.0 - response_time_ms / max_latency)
    cst = max(0.0, 1.0 - cost / max_cost) if max_cost > 0 else 1.0

    return round(max(0.0, min(1.0, W_FEEDBACK * fb + W_LATENCY * lat + W_COST * cst)), 4)


# ─── Arm management ──────────────────────────────────────────

def ensure_arm(model_name: str, provider: str, category: str) -> None:
    """Insert a bandit arm if it doesn't already exist."""
    execute("""
        INSERT INTO bandit_model_stats (model_name, provider, category)
        VALUES (%s, %s, %s)
        ON CONFLICT ON CONSTRAINT uq_bandit_model DO NOTHING;
    """, (model_name, provider, category))


def get_arm_stats(model_name: str, category: str) -> Optional[Dict[str, Any]]:
    """Fetch bandit stats for one arm."""
    return fetch_one("""
        SELECT * FROM bandit_model_stats
        WHERE model_name = %s AND category = %s;
    """, (model_name, category))


def record_outcome(
    model_name: str,
    provider: str,
    category: str,
    feedback: int,
    response_time_ms: int = 0,
    cost: float = 0.0,
) -> float:
    """
    Record the result of a model call. Updates bandit_model_stats.
    Returns the computed reward.
    """
    reward = compute_reward(feedback, response_time_ms, cost)
    ensure_arm(model_name, provider, category)

    is_success = feedback == 1
    execute("""
        UPDATE bandit_model_stats
        SET total_trials  = total_trials + 1,
            success_count = success_count + CASE WHEN %s THEN 1 ELSE 0 END,
            failure_count = failure_count + CASE WHEN %s THEN 0 ELSE 1 END,
            avg_reward    = CASE WHEN total_trials = 0 THEN %s
                            ELSE (avg_reward * total_trials + %s) / (total_trials + 1) END,
            avg_latency_ms = CASE WHEN %s > 0
                             THEN (avg_latency_ms * total_trials + %s) / (total_trials + 1)
                             ELSE avg_latency_ms END,
            avg_cost      = CASE WHEN %s > 0
                            THEN (avg_cost * total_trials + %s) / (total_trials + 1)
                            ELSE avg_cost END,
            updated_at    = CURRENT_TIMESTAMP
        WHERE model_name = %s AND category = %s;
    """, (
        is_success, is_success,
        reward, reward,
        response_time_ms, response_time_ms,
        cost, cost,
        model_name, category,
    ))

    return reward


# ─── Thompson Sampling selection ──────────────────────────────

def _thompson_sample(alpha: float, beta: float) -> float:
    """Draw from Beta(alpha, beta)."""
    try:
        return random.betavariate(alpha, beta)
    except ValueError:
        return 0.5


def select_best(
    candidates: List[Dict[str, Any]],
    category: str,
) -> Dict[str, Any]:
    """
    Pick the best model from candidates using Thompson Sampling.

    Each candidate must have at least 'model_name' key.
    Returns the chosen candidate dict with an added 'bandit_score'.
    """
    if not candidates:
        raise ValueError("No candidates for bandit selection")

    if len(candidates) == 1:
        candidates[0]["bandit_score"] = 0.5
        return candidates[0]

    scored: List[Tuple[float, Dict[str, Any]]] = []

    for model in candidates:
        name = model["model_name"]
        stats = get_arm_stats(name, category)

        if stats and stats["total_trials"] > 0:
            alpha = stats["success_count"] + ALPHA_PRIOR
            beta = stats["failure_count"] + BETA_PRIOR
        else:
            alpha = ALPHA_PRIOR
            beta = BETA_PRIOR

        sample = _thompson_sample(alpha, beta)

        # Exploration bonus for cold-start arms
        trials = stats["total_trials"] if stats else 0
        if trials < 10:
            sample += EXPLORATION_BONUS * (1 - trials / 10)

        model["bandit_score"] = round(sample, 4)
        scored.append((sample, model))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def get_all_stats() -> List[Dict[str, Any]]:
    """Return all bandit stats for the /stats endpoint."""
    return fetch_all("""
        SELECT model_name, provider, category, total_trials,
               success_count, failure_count, avg_reward, avg_latency_ms, avg_cost
        FROM bandit_model_stats
        ORDER BY avg_reward DESC;
    """)
