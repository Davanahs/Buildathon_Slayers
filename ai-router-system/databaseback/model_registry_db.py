"""
model_registry_db.py — Table definition and CRUD helpers.

This file ONLY:
  1. Creates the model_registry table
  2. Provides query/update helpers

It does NOT hardcode any model data.
All model population is done by librarian.py via the provider APIs.
"""

from typing import Optional, List, Dict, Any
from db import get_conn, fetch_one, fetch_all, execute


# ─── Standardized categories (single source of truth) ────────

VALID_CATEGORIES = ("code", "chat", "image", "video", "audio", "embedding", "reasoning")


# ─── Table creation ───────────────────────────────────────────

def create_model_registry_table():
    """Create the model_registry table and indexes if they don't exist."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS model_registry (
        id                  SERIAL PRIMARY KEY,
        model_name          VARCHAR(200) NOT NULL,
        provider            VARCHAR(100) NOT NULL,
        category            VARCHAR(50)  NOT NULL
                                CHECK (category IN ('code','chat','image','video','audio','embedding','reasoning')),
        tier                INTEGER      NOT NULL CHECK (tier IN (1, 2, 3)),
        sub_tier            VARCHAR(10),
        complexity_min      INTEGER      NOT NULL CHECK (complexity_min >= 1 AND complexity_min <= 10),
        complexity_max      INTEGER      NOT NULL CHECK (complexity_max >= 1 AND complexity_max <= 10),
        cost_per_1k_input   DOUBLE PRECISION DEFAULT 0,
        cost_per_1k_output  DOUBLE PRECISION DEFAULT 0,
        avg_latency_ms      INTEGER DEFAULT 0,
        context_window      INTEGER DEFAULT 0,
        is_active           BOOLEAN DEFAULT TRUE,
        priority_rank       INTEGER DEFAULT 999,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_model_provider UNIQUE (model_name, provider),
        CONSTRAINT valid_complexity   CHECK (complexity_min <= complexity_max)
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_registry_category   ON model_registry(category);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_registry_active     ON model_registry(is_active);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_registry_complexity ON model_registry(complexity_min, complexity_max);")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ model_registry table ready")


# ─── Query helpers ────────────────────────────────────────────

def get_model_count() -> int:
    """Return how many active models are in the registry."""
    row = fetch_one("SELECT COUNT(*) AS cnt FROM model_registry WHERE is_active = TRUE;")
    return int(row["cnt"]) if row else 0


def get_model_by_name(model_name: str, provider: str) -> Optional[Dict[str, Any]]:
    """Fetch a single model entry by name + provider."""
    return fetch_one("""
        SELECT * FROM model_registry
        WHERE model_name = %s AND provider = %s;
    """, (model_name, provider))


def get_active_models(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all active models, optionally filtered by category."""
    if category:
        return fetch_all("""
            SELECT * FROM model_registry
            WHERE is_active = TRUE AND category = %s
            ORDER BY priority_rank ASC;
        """, (category,))
    return fetch_all("""
        SELECT * FROM model_registry
        WHERE is_active = TRUE
        ORDER BY priority_rank ASC;
    """)


def deactivate_model(model_name: str, provider: str) -> None:
    """Mark a specific model as inactive."""
    execute("""
        UPDATE model_registry
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE model_name = %s AND provider = %s;
    """, (model_name, provider))


def activate_model(model_name: str, provider: str) -> None:
    """Re-activate a previously deactivated model."""
    execute("""
        UPDATE model_registry
        SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP
        WHERE model_name = %s AND provider = %s;
    """, (model_name, provider))


if __name__ == "__main__":
    create_model_registry_table()
    print(f"Active models in registry: {get_model_count()}")
