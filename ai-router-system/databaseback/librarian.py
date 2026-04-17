"""
Librarian — the brain that discovers, analyzes, and catalogs AI models.

Flow:
    API keys → fetch available models from provider → analyze each model
    → assign category + tier + complexity → store in model_registry

This module ONLY writes to model_registry. No extra tables.
Uses db.py for all database access.
"""

import os
import sys
import time
import json
import hashlib
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Ensure Windows terminals don't crash when printing emojis
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

from db import fetch_one, fetch_all, execute

load_dotenv(override=True)

# ─── Config ───────────────────────────────────────────────────

REQUEST_TIMEOUT = 30

# Hard cap — free Neon DB tier limit
MAX_REGISTRY_ROWS = 50

# Discovery runs only on key change or after this many days
DISCOVERY_INTERVAL_DAYS = 30

# State file: tracks key hash + last run time per provider (no extra DB table needed)
# Named with a leading dot so uvicorn --reload ignores it and doesn't infinitely restart.
STATE_FILE = Path(__file__).parent / ".discovery_state.json"

GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"

# Standardized categories (lowercase)
VALID_CATEGORIES = {"code", "chat", "image", "video", "audio", "embedding", "reasoning"}


def _gemini_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY")

def _groq_key() -> Optional[str]:
    return os.getenv("GROQ_API_KEY")

def _openrouter_key() -> Optional[str]:
    return os.getenv("OPENROUTER_API_KEY")

def _sarvam_key() -> Optional[str]:
    return os.getenv("SARVAM_API_KEY")


# ─── Discovery state helpers ──────────────────────────────────

def _hash_key(value: Optional[str]) -> str:
    """SHA-256 hash of an API key (never store the key itself)."""
    return hashlib.sha256((value or "").encode()).hexdigest()


def _load_state() -> Dict[str, Any]:
    """Load discovery state from the JSON file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_state(state: Dict[str, Any]) -> None:
    """Persist discovery state to the JSON file."""
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def should_discover(provider: str, api_key: Optional[str]) -> tuple[bool, str]:
    """
    Decide whether discovery should run for this provider.

    Returns (should_run: bool, reason: str).

    Skips if:
      - API key is missing
      - Key hash matches AND last run was within DISCOVERY_INTERVAL_DAYS
    Runs if:
      - First time ever (no state recorded)
      - API key hash changed
      - Last run was more than DISCOVERY_INTERVAL_DAYS ago
    """
    if not api_key:
        return False, "no_api_key"

    state = _load_state()
    entry = state.get(provider, {})
    new_hash = _hash_key(api_key)

    if not entry:
        return True, "first_run"

    if entry.get("key_hash") != new_hash:
        print(f"[{provider}] Debug Hash Mismatch: Expected {entry.get('key_hash')} but got {new_hash}")
        return True, "key_changed"

    last_run_str = entry.get("last_run_at")
    if not last_run_str:
        return True, "never_ran"

    try:
        last_run = datetime.datetime.fromisoformat(last_run_str)
        elapsed = datetime.datetime.utcnow() - last_run
        if elapsed >= datetime.timedelta(days=DISCOVERY_INTERVAL_DAYS):
            return True, f"{DISCOVERY_INTERVAL_DAYS}_day_refresh"
    except Exception:
        return True, "invalid_state"

    return False, "up_to_date"


def mark_discovered(provider: str, api_key: Optional[str]) -> None:
    """Record a successful discovery run in the state file."""
    state = _load_state()
    state[provider] = {
        "key_hash": _hash_key(api_key),
        "last_run_at": datetime.datetime.utcnow().isoformat(),
    }
    _save_state(state)


# ═══════════════════════════════════════════════════════════════
# STEP 1: FETCH available models from each provider
# ═══════════════════════════════════════════════════════════════

def fetch_gemini_models() -> List[Dict[str, Any]]:
    """Fetch all available models from Google Gemini API."""
    key = _gemini_key()
    if not key:
        print("  ⚠️  GEMINI_API_KEY not set, skipping")
        return []

    resp = requests.get(
        GEMINI_MODELS_URL,
        params={"key": key},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("models", [])


def fetch_openrouter_models() -> List[Dict[str, Any]]:
    """Fetch all available models from OpenRouter API."""
    key = _openrouter_key()
    if not key:
        print("  ⚠️  OPENROUTER_API_KEY not set, skipping")
        return []

    resp = requests.get(
        OPENROUTER_MODELS_URL,
        headers={"Authorization": f"Bearer {key}"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def fetch_groq_models() -> List[Dict[str, Any]]:
    """Fetch all available models from Groq API."""
    key = _groq_key()
    if not key:
        print("  ⚠️  GROQ_API_KEY not set, skipping")
        return []

    resp = requests.get(
        GROQ_MODELS_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


# ═══════════════════════════════════════════════════════════════
# STEP 2: ANALYZE each model — assign category, tier, complexity
# ═══════════════════════════════════════════════════════════════

def infer_category(model_name: str) -> str:
    """Determine category from the model name using keyword heuristics."""
    name = model_name.lower()

    if any(kw in name for kw in ["code", "coder", "codestral", "sql", "python"]):
        return "code"
    
    if any(kw in name for kw in ["agent", "tool", "call", "func"]):
        return "agent"

    if any(kw in name for kw in ["image", "vision", "vl", "multimodal", "gpt-image", "dall-e", "stable-diffusion"]):
        return "image"
        
    if any(kw in name for kw in ["chat", "instruct", "convers", "dialog"]):
        return "chat"
    
    return "general"


def estimate_context_window(raw: Dict[str, Any]) -> int:
    """Extract context window size from raw model metadata."""
    for key in ["context_window", "context_length", "input_token_limit",
                "max_input_tokens", "inputTokenLimit"]:
        val = raw.get(key)
        if isinstance(val, (int, float)):
            return int(val)

    # OpenRouter nests it under architecture
    arch = raw.get("architecture", {})
    if isinstance(arch, dict):
        cl = arch.get("context_length")
        if isinstance(cl, (int, float)):
            return int(cl)

    return 0


def score_complexity(model_name: str, context_window: int, category: str) -> Tuple[int, int]:
    """
    Assign a complexity range [min, max] based on model characteristics.
    Returns (complexity_min, complexity_max).
    """
    base = 5
    name = model_name.lower()

    # Light models → lower complexity
    if any(kw in name for kw in ["flash", "lite", "mini", "instant", "8b", "7b", "nano"]):
        base -= 2
    # Heavy models → higher complexity
    if any(kw in name for kw in ["pro", "70b", "advanced", "405b", "reason", "r1", "o3", "o4"]):
        base += 2
    # Category boost
    if category in ("reasoning", "code", "video"):
        base += 1
    # Context window boost
    if context_window >= 100000:
        base += 2
    elif context_window >= 32000:
        base += 1

    base = max(1, min(10, base))

    # Create a range around the base score
    cmin = max(1, base - 2)
    cmax = min(10, base + 2)
    return cmin, cmax


def assign_tier(complexity_max: int) -> Tuple[int, Optional[str]]:
    """
    Map complexity to tier:
      Tier 1 (best) → complexity_max >= 8
      Tier 2 (mid)  → complexity_max 4-7
      Tier 3 (fast) → complexity_max <= 3
    """
    if complexity_max >= 9:
        return 1, "A"
    if complexity_max >= 8:
        return 1, "B"
    if complexity_max >= 4:
        return 2, None
    return 3, None


def estimate_latency(provider: str, model_name: str) -> int:
    """Heuristic latency in ms based on provider and model name."""
    name = model_name.lower()
    if provider == "groq":
        return 400  # Groq is consistently fast
    if "flash" in name or "instant" in name or "lite" in name or "mini" in name:
        return 600
    if "pro" in name or "70b" in name:
        return 1800
    if "reason" in name or "advanced" in name or "r1" in name or "o3" in name:
        return 2200
    return 1200


def extract_costs(raw: Dict[str, Any]) -> Tuple[float, float]:
    """Extract input/output cost per 1K tokens from raw metadata."""
    in_cost = 0.0
    out_cost = 0.0

    # OpenRouter puts pricing in a nested dict
    pricing = raw.get("pricing", {})
    if isinstance(pricing, dict):
        try:
            if "prompt" in pricing:
                in_cost = float(pricing["prompt"])
            if "completion" in pricing:
                out_cost = float(pricing["completion"])
        except (ValueError, TypeError):
            pass

    # Direct fields
    for key in ["input_cost_per_1k", "prompt_cost", "input_cost"]:
        val = raw.get(key)
        if val is not None:
            try:
                in_cost = float(val)
                break
            except (ValueError, TypeError):
                pass

    for key in ["output_cost_per_1k", "completion_cost", "output_cost"]:
        val = raw.get(key)
        if val is not None:
            try:
                out_cost = float(val)
                break
            except (ValueError, TypeError):
                pass

    return in_cost, out_cost


def priority_rank(tier: int, sub_tier: Optional[str]) -> int:
    """Map tier+sub_tier to a numeric priority (lower = better)."""
    if tier == 1 and sub_tier == "A":
        return 1
    if tier == 1 and sub_tier == "B":
        return 2
    if tier == 2:
        return 3
    return 4


# ═══════════════════════════════════════════════════════════════
# STEP 2b (OPTIONAL): Use Gemini as a smart librarian
# ═══════════════════════════════════════════════════════════════

def classify_with_gemini(model_name: str, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Ask Gemini to classify a model into category + complexity.
    Falls back to heuristics if this fails.
    """
    key = _gemini_key()
    if not key:
        return None

    prompt = f"""You are an AI model librarian.
Classify this model. Return ONLY valid JSON with keys: category, complexity

Allowed categories: code, chat, image, video, audio, embedding, reasoning

Model name: {model_name}
Metadata: {json.dumps(raw)[:4000]}"""

    try:
        url = GEMINI_GENERATE_URL.format(model="gemini-2.0-flash")
        resp = requests.post(
            url,
            params={"key": key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        parsed = json.loads(text)
        cat = parsed.get("category", "").lower()
        comp = parsed.get("complexity", 5)

        if cat in VALID_CATEGORIES:
            return {"category": cat, "complexity": max(1, min(10, int(comp)))}
    except Exception:
        pass  # Fall through to heuristics

    return None


# ═══════════════════════════════════════════════════════════════
# STEP 3: Full analysis pipeline for one model
# ═══════════════════════════════════════════════════════════════

def analyze_model(provider: str, model_name: str, raw: Dict[str, Any], use_llm: bool = False) -> Dict[str, Any]:
    """
    Analyze a single model and return all fields needed for model_registry.

    If use_llm=True, tries Gemini classification first, then falls back to heuristics.
    """
    # Try LLM classification
    llm_result = None
    if use_llm:
        llm_result = classify_with_gemini(model_name, raw)

    if llm_result:
        category = llm_result["category"]
        comp = llm_result["complexity"]
        cmin = max(1, comp - 2)
        cmax = min(10, comp + 2)
    else:
        category = infer_category(model_name)
        context_window = estimate_context_window(raw)
        cmin, cmax = score_complexity(model_name, context_window, category)

    context_window = estimate_context_window(raw)
    tier, sub_tier = assign_tier(cmax)
    latency = estimate_latency(provider, model_name)
    in_cost, out_cost = extract_costs(raw)

    return {
        "model_name": model_name,
        "provider": provider,
        "category": category,
        "tier": tier,
        "sub_tier": sub_tier,
        "complexity_min": cmin,
        "complexity_max": cmax,
        "cost_per_1k_input": in_cost,
        "cost_per_1k_output": out_cost,
        "avg_latency_ms": latency,
        "context_window": context_window,
        "priority_rank": priority_rank(tier, sub_tier),
    }


# ═══════════════════════════════════════════════════════════════
# STEP 4: STORE in model_registry
# ═══════════════════════════════════════════════════════════════

def _registry_row_count() -> int:
    """Return current number of rows in model_registry."""
    row = fetch_one("SELECT COUNT(*) AS cnt FROM model_registry;")
    return int(row["cnt"]) if row else 0


def upsert_model(info: Dict[str, Any]) -> bool:
    """
    Insert or update a model in model_registry.

    - If the model already exists (conflict on model_name+provider) → UPDATE always allowed.
    - If it is a new row → only insert when total rows < MAX_REGISTRY_ROWS.

    Returns True if the row was written, False if skipped due to cap.
    """
    # Check if this model already exists (update is always safe)
    existing = fetch_one(
        "SELECT id FROM model_registry WHERE model_name = %s AND provider = %s;",
        (info["model_name"], info["provider"]),
    )

    if not existing and _registry_row_count() >= MAX_REGISTRY_ROWS:
        return False   # cap reached, skip new insert

    execute("""
        INSERT INTO model_registry
            (model_name, provider, category, tier, sub_tier,
             complexity_min, complexity_max,
             cost_per_1k_input, cost_per_1k_output,
             avg_latency_ms, context_window,
             is_active, priority_rank, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (model_name, provider) DO UPDATE SET
            category = EXCLUDED.category,
            tier = EXCLUDED.tier,
            sub_tier = EXCLUDED.sub_tier,
            complexity_min = EXCLUDED.complexity_min,
            complexity_max = EXCLUDED.complexity_max,
            cost_per_1k_input = EXCLUDED.cost_per_1k_input,
            cost_per_1k_output = EXCLUDED.cost_per_1k_output,
            avg_latency_ms = EXCLUDED.avg_latency_ms,
            context_window = EXCLUDED.context_window,
            is_active = TRUE,
            priority_rank = EXCLUDED.priority_rank,
            updated_at = CURRENT_TIMESTAMP;
    """, (
        info["model_name"], info["provider"], info["category"],
        info["tier"], info["sub_tier"],
        info["complexity_min"], info["complexity_max"],
        info["cost_per_1k_input"], info["cost_per_1k_output"],
        info["avg_latency_ms"], info["context_window"],
        info["priority_rank"],
    ))
    return True


def deactivate_stale_models(provider: str, alive_names: List[str]) -> None:
    """Mark models as inactive if they are no longer returned by the provider API."""
    if not alive_names:
        return
    execute("""
        UPDATE model_registry
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE provider = %s
          AND model_name NOT IN (SELECT unnest(%s::text[]));
    """, (provider, alive_names))


# ═══════════════════════════════════════════════════════════════
# STEP 5: NORMALIZERS — extract model_name from raw API response
# ═══════════════════════════════════════════════════════════════

def normalize_gemini(row: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Extract model name and metadata from Gemini API response."""
    name = row.get("name", "")
    model_name = name.split("/")[-1] if name else None
    if not model_name:
        return None

    # Skip non-generative models
    methods = row.get("supportedGenerationMethods", [])
    if methods and "generateContent" not in methods:
        return None

    return model_name, {
        "display_name": row.get("displayName"),
        "description": row.get("description"),
        "inputTokenLimit": row.get("inputTokenLimit"),
        "outputTokenLimit": row.get("outputTokenLimit"),
        "supportedGenerationMethods": methods,
    }


def normalize_openrouter(row: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Extract model name and metadata from OpenRouter API response."""
    model_name = row.get("id")
    if not model_name:
        return None

    return model_name, {
        "name": row.get("name"),
        "description": row.get("description"),
        "pricing": row.get("pricing", {}),
        "context_length": row.get("context_length"),
        "architecture": row.get("architecture", {}),
    }


def normalize_groq(row: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Extract model name and metadata from Groq API response."""
    model_name = row.get("id")
    if not model_name:
        return None

    return model_name, {
        "owned_by": row.get("owned_by"),
        "context_window": row.get("context_window"),
    }


# ═══════════════════════════════════════════════════════════════
# MAIN: Discover all models for a provider
# ═══════════════════════════════════════════════════════════════

PROVIDERS = {
    "gemini": {
        "fetcher": fetch_gemini_models,
        "normalizer": normalize_gemini,
    },
    "openrouter": {
        "fetcher": fetch_openrouter_models,
        "normalizer": normalize_openrouter,
    },
    "groq": {
        "fetcher": fetch_groq_models,
        "normalizer": normalize_groq,
    },
}


def fetch_provider_models(provider: str) -> List[Dict[str, Any]]:
    """Fetch and analyze models for a single provider."""
    print(f"[{provider}] 🔍 Fetching and analyzing raw models...")
    cfg = PROVIDERS[provider]
    try:
        raw_models = cfg["fetcher"]()
    except Exception as e:
        print(f"[{provider}] ❌ Fetch failed: {e}")
        return []

    processed = []
    for item in raw_models:
        normalized = cfg["normalizer"](item)
        if not normalized: continue
        
        model_name, meta = normalized
        info = analyze_model(provider, model_name, meta, use_llm=False)
        processed.append(info)
        
    return processed

def _bulk_upsert(models_to_keep: List[Dict[str, Any]]) -> None:
    """Wipe the model_registry and insert exactly the optimized global final list."""
    execute("TRUNCATE TABLE model_registry;")
    
    for info in models_to_keep:
        execute("""
            INSERT INTO model_registry
                (model_name, provider, category, tier, sub_tier,
                 complexity_min, complexity_max,
                 cost_per_1k_input, cost_per_1k_output,
                 avg_latency_ms, context_window,
                 is_active, priority_rank, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, CURRENT_TIMESTAMP)
        """, (
            info["model_name"], info["provider"], info["category"],
            info["tier"], info["sub_tier"],
            info["complexity_min"], info["complexity_max"],
            info["cost_per_1k_input"], info["cost_per_1k_output"],
            info["avg_latency_ms"], info["context_window"],
            info["priority_rank"],
        ))

def discover_all(use_llm: bool = False, force: bool = False) -> Dict[str, int]:
    """Run global discovery: aggregates all models, ranks them, caps at 10 per category, and saves."""
    api_keys = {"gemini": _gemini_key(), "openrouter": _openrouter_key(), "groq": _groq_key(), "sarvam": _sarvam_key()}
    
    # 1. Determine if a global run is needed
    run_needed = force
    if not force:
        for prov, key in api_keys.items():
            if prov == "sarvam": continue # Sarvam isn't discovered, just used
            run, reason = should_discover(prov, key)
            if run:
                print(f"⚠️ Global discovery triggered by: {prov} ({reason})")
                run_needed = True
                break

    if not run_needed:
        print("⏭️  Skipping global discovery (model registry is up to date)")
        return {}

    print("🚀 Starting global catalog assembly...")

    # 2. Fetch all models from all providers
    all_models = []
    for prov in ["gemini", "openrouter", "groq"]:
        if not api_keys[prov]: continue
        all_models.extend(fetch_provider_models(prov))

    # 3. Bucket strictly by category
    buckets = {"code": [], "agent": [], "chat": [], "image": [], "general": []}
    for m in all_models:
        cat = m["category"]
        if cat in buckets:
            buckets[cat].append(m)

    # 4. Rank and cut at Top 10 per category
    final_roster = []
    category_counts = {}
    
    for cat, models in buckets.items():
        # Sort by tier (1 is best), sub_tier (A is best), priority_rank (lower is best)
        sorted_models = sorted(models, key=lambda x: (x["tier"], getattr(x, "sub_tier", "Z"), x["priority_rank"]))
        top_10 = sorted_models[:10]
        final_roster.extend(top_10)
        category_counts[cat] = len(top_10)

    # 5. Save to DB
    _bulk_upsert(final_roster)
    
    # 6. Mark successful state
    for prov in ["gemini", "openrouter", "groq"]:
        if api_keys[prov]:
            mark_discovered(prov, api_keys[prov])
            
    print(f"✅ Global Discovery Finished. Cap enforced. Stats: {category_counts}")
    return category_counts


if __name__ == "__main__":
    print("🔍 Running model discovery...")
    results = discover_all(use_llm=False)
    print(f"\n📊 Results: {results}")
    total = sum(results.values())
    print(f"Total models cataloged: {total}")
