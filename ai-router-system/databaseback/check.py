"""
check.py — Diagnostic script to verify the full backend stack.

Checks:
  1. Database connection
  2. model_registry populated (librarian worked)
  3. bandit_model_stats table exists
  4. prompt_memory table + embedding column
  5. Send a real test prompt and verify it is stored

Run:
    cd backend
    python check.py
"""

import os
import sys

# Make sure sibling imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

SEP = "─" * 55


def section(title: str):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


# ─── 1. DB Connection ─────────────────────────────────────────
section("1. DATABASE CONNECTION")
try:
    from db import get_conn
    conn = get_conn()
    conn.close()
    print("✅ Connected to database")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)


# ─── 2. model_registry ───────────────────────────────────────
section("2. MODEL REGISTRY")
try:
    from db import fetch_one, fetch_all

    count = fetch_one("SELECT COUNT(*) AS cnt FROM model_registry WHERE is_active = TRUE;")
    total = int(count["cnt"]) if count else 0
    print(f"Active models in registry: {total}")

    if total == 0:
        print("⚠️  Registry is empty — librarian may not have run yet.")
        print("   Trigger discovery via:  POST /discover")
    else:
        print("✅ Registry has data\n")
        rows = fetch_all("""
            SELECT provider, category, COUNT(*) AS cnt
            FROM model_registry
            WHERE is_active = TRUE
            GROUP BY provider, category
            ORDER BY provider, category;
        """)
        print(f"  {'Provider':<15} {'Category':<15} {'Models':>6}")
        print(f"  {'-'*15} {'-'*15} {'-'*6}")
        for r in rows:
            print(f"  {r['provider']:<15} {r['category']:<15} {r['cnt']:>6}")
except Exception as e:
    print(f"❌ model_registry check failed: {e}")


# ─── 3. bandit_model_stats ────────────────────────────────────
section("3. BANDIT STATS TABLE")
try:
    count = fetch_one("SELECT COUNT(*) AS cnt FROM bandit_model_stats;")
    total = int(count["cnt"]) if count else 0
    print(f"Bandit arms tracked: {total}")
    if total == 0:
        print("ℹ️  No data yet — arms are created when /chat is first called")
    else:
        print("✅ Bandit has data\n")
        rows = fetch_all("""
            SELECT model_name, category, total_trials, avg_reward
            FROM bandit_model_stats
            ORDER BY avg_reward DESC
            LIMIT 5;
        """)
        print(f"  {'Model':<35} {'Category':<12} {'Trials':>7} {'AvgReward':>10}")
        print(f"  {'-'*35} {'-'*12} {'-'*7} {'-'*10}")
        for r in rows:
            print(f"  {r['model_name'][:34]:<35} {r['category']:<12} {r['total_trials']:>7} {float(r['avg_reward']):>10.4f}")
except Exception as e:
    print(f"❌ bandit_model_stats check failed: {e}")


# ─── 4. prompt_memory + embedding column ──────────────────────
section("4. PROMPT MEMORY + EMBEDDINGS")
try:
    count = fetch_one("SELECT COUNT(*) AS cnt FROM prompt_memory;")
    total = int(count["cnt"]) if count else 0
    print(f"Memories stored: {total}")

    # Check embedding column exists and has vector data
    emb_count = fetch_one(
        "SELECT COUNT(*) AS cnt FROM prompt_memory WHERE embedding IS NOT NULL;"
    )
    emb_total = int(emb_count["cnt"]) if emb_count else 0
    print(f"Memories with embeddings: {emb_total}")

    if total == 0:
        print("ℹ️  No memories yet — stored after first /chat call")
    else:
        print("✅ prompt_memory has data\n")
        rows = fetch_all("""
            SELECT id, model_used, category, complexity_score,
                   response_time_ms, total_tokens, actual_cost, created_at
            FROM prompt_memory
            ORDER BY created_at DESC
            LIMIT 5;
        """)
        for r in rows:
            print(f"  [{r['id']}] {r['model_used']} | {r['category']} | "
                  f"complexity={r['complexity_score']} | "
                  f"{r['response_time_ms']}ms | "
                  f"{r['total_tokens']} tokens | "
                  f"${float(r['actual_cost']):.6f} | "
                  f"{r['created_at']}")
except Exception as e:
    print(f"❌ prompt_memory check failed: {e}")


# ─── 5. Live end-to-end test ──────────────────────────────────
section("5. LIVE ROUTING TEST")

run_live = input("\nRun a live routing test? (sends a real prompt) [y/N]: ").strip().lower()
if run_live == "y":
    try:
        from router import route_prompt

        test_prompt = "Write a Python function that reverses a string."
        print(f"\nPrompt: \"{test_prompt}\"")
        print("Routing...\n")

        result = route_prompt(prompt=test_prompt)

        print(f"  ✅ Response received")
        print(f"  Model :  {result['model_used']} ({result['provider']})")
        print(f"  Category:  {result['category']}")
        print(f"  Complexity: {result['complexity_score']}/10")
        print(f"  Time:   {result['response_time_ms']} ms")
        print(f"  Cost:   ${result['estimated_cost']:.6f}")
        print(f"  Memory ID: {result['memory_id']}")
        print(f"\n  Response preview:\n  {result['response'][:300]}...")
    except Exception as e:
        print(f"❌ Routing test failed: {e}")
else:
    print("Skipped.")


# ─── Summary ─────────────────────────────────────────────────
section("SUMMARY")
print("Run the server with:")
print("  uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
print("\nThen open:")
print("  http://localhost:8000/docs    ← Swagger UI")
print("  http://localhost:8000/health  ← Health check")
print("  http://localhost:8000/models  ← Model registry")
print("  http://localhost:8000/stats   ← Bandit stats")
print()
