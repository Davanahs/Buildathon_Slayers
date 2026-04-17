from sqlalchemy.orm import Session
from sqlalchemy import text

def fetch_models(db: Session, category: str, complexity: float):
    print(f"[MODEL_DB] Fetching models for category={category}, complexity={complexity}")

    query = text("""
        SELECT * FROM models
        WHERE category = :category
        AND complexity_min <= :complexity
        AND complexity_max >= :complexity
        AND active = true
    """)

    result = db.execute(query, {
        "category": category,
        "complexity": complexity
    })

    models = result.fetchall()

    print(f"[MODEL_DB] Found {len(models)} models")

    return models