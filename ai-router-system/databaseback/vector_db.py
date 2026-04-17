"""
prompt_memory table — single source of truth.

Stores every prompt-response pair with metadata:
prompt, response, model_used, category, complexity,
embedding, response_time_ms, prompt_tokens, completion_tokens,
total_tokens, actual_cost.

Also provides insert and similarity-search utilities.
"""

from typing import Optional, Dict, Any, List

from db import get_conn, fetch_one, fetch_all, execute


def create_prompt_memory_table():
    """Create the prompt_memory table (with pgvector) if it does not exist."""
    conn = get_conn()
    cur = conn.cursor()

    # Enable pgvector extension (no-op if already enabled)
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prompt_memory (
        id                  SERIAL PRIMARY KEY,
        user_id             VARCHAR(100),
        prompt              TEXT NOT NULL,
        response            TEXT NOT NULL,
        model_used          VARCHAR(200),
        provider            VARCHAR(100),
        category            VARCHAR(50),
        complexity_score    INTEGER CHECK (complexity_score >= 1 AND complexity_score <= 10),
        embedding           VECTOR(384),
        response_time_ms    INTEGER DEFAULT 0,
        prompt_tokens       INTEGER DEFAULT 0,
        completion_tokens   INTEGER DEFAULT 0,
        total_tokens        INTEGER DEFAULT 0,
        actual_cost         DOUBLE PRECISION DEFAULT 0,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Indexes for common queries
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_memory_category ON prompt_memory(category);
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_memory_model ON prompt_memory(model_used);
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_memory_user ON prompt_memory(user_id);
    """)

    # IVFFlat vector index for fast similarity search (requires rows to exist first time)
    # We use a partial approach: create the index only if the table has rows.
    # For an empty table, the basic sequential scan is fine.
    try:
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_memory_embedding
        ON prompt_memory USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10);
        """)
    except Exception:
        # IVFFlat needs at least some rows to build; skip on empty table
        conn.rollback()
        cur = conn.cursor()

    conn.commit()
    cur.close()
    conn.close()
    print("✅ prompt_memory table ready")


# ─── Insert utility ──────────────────────────────────────────

def store_memory(
    prompt: str,
    response: str,
    model_used: str,
    provider: str,
    category: str,
    complexity_score: int,
    response_time_ms: int = 0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    actual_cost: float = 0.0,
    user_id: Optional[str] = None,
    embedding: Optional[List[float]] = None,
) -> Optional[int]:
    """
    Insert a prompt-response pair into prompt_memory.
    Returns the new row id, or None on failure.
    """
    total_tokens = prompt_tokens + completion_tokens

    try:
        if embedding:
            row = fetch_one("""
                INSERT INTO prompt_memory
                    (user_id, prompt, response, model_used, provider, category,
                     complexity_score, embedding, response_time_ms,
                     prompt_tokens, completion_tokens, total_tokens, actual_cost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (user_id, prompt, response, model_used, provider, category,
                  complexity_score, str(embedding), response_time_ms,
                  prompt_tokens, completion_tokens, total_tokens, actual_cost))
        else:
            row = fetch_one("""
                INSERT INTO prompt_memory
                    (user_id, prompt, response, model_used, provider, category,
                     complexity_score, response_time_ms,
                     prompt_tokens, completion_tokens, total_tokens, actual_cost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (user_id, prompt, response, model_used, provider, category,
                  complexity_score, response_time_ms,
                  prompt_tokens, completion_tokens, total_tokens, actual_cost))

        return row["id"] if row else None
    except Exception as e:
        print(f"⚠️  Failed to store memory: {e}")
        return None


# ─── Retrieval utilities ──────────────────────────────────────

def get_memory_by_id(memory_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single memory entry by ID."""
    return fetch_one("SELECT * FROM prompt_memory WHERE id = %s;", (memory_id,))


def search_similar(embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Find the most similar past prompts by cosine distance.
    Requires the embedding column to be populated.
    """
    return fetch_all("""
        SELECT id, prompt, response, model_used, category, complexity_score,
               1 - (embedding <=> %s::vector) AS similarity
        FROM prompt_memory
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (str(embedding), str(embedding), limit))


def get_recent_memories(limit: int = 20, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get recent prompt-response pairs, optionally filtered by category."""
    if category:
        return fetch_all("""
            SELECT id, prompt, response, model_used, provider, category,
                   complexity_score, response_time_ms, total_tokens, actual_cost, created_at
            FROM prompt_memory
            WHERE category = %s
            ORDER BY created_at DESC
            LIMIT %s;
        """, (category, limit))
    else:
        return fetch_all("""
            SELECT id, prompt, response, model_used, provider, category,
                   complexity_score, response_time_ms, total_tokens, actual_cost, created_at
            FROM prompt_memory
            ORDER BY created_at DESC
            LIMIT %s;
        """, (limit,))


if __name__ == "__main__":
    create_prompt_memory_table()