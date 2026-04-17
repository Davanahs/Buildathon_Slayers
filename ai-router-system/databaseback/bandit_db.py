"""
bandit_model_stats table — single source of truth.

Tracks Thompson Sampling statistics per model-category pair.
This is the ONLY bandit table. No separate feedback log table.
"""

from db import get_conn


def create_bandit_table():
    """Create the bandit_model_stats table if it does not exist."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bandit_model_stats (
        id              SERIAL PRIMARY KEY,
        model_name      VARCHAR(200) NOT NULL,
        provider        VARCHAR(100),
        category        VARCHAR(50)  NOT NULL,
        total_trials    INTEGER DEFAULT 0,
        success_count   INTEGER DEFAULT 0,
        failure_count   INTEGER DEFAULT 0,
        avg_reward      DOUBLE PRECISION DEFAULT 0,
        avg_latency_ms  DOUBLE PRECISION DEFAULT 0,
        avg_cost        DOUBLE PRECISION DEFAULT 0,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_bandit_model UNIQUE (model_name, category)
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ bandit_model_stats table ready")


if __name__ == "__main__":
    create_bandit_table()