"""
Core AI Router — full pipeline as designed.

Step 1:  classify_category()         → code | chat | image | reasoning | ...
Step 2:  score_complexity()          → 1-10
Step 3:  generate_embedding()        → 768-dim vector via Gemini embedding model
Step 4:  check_memory_cache()        → search prompt_memory for similar past prompt
Step 5a: [Cache HIT]  return cached response immediately
Step 5b: [Cache MISS] get_candidates() → query model_registry
Step 6:  compute_confidence()        → how sure librarian is about best model
Step 7a: [High confidence] pick top model by priority_rank (librarian decides)
Step 7b: [Low confidence]  consult bandit → select_best() (Thompson Sampling)
Step 8:  call_model()                → Gemini | OpenRouter | Groq API
Step 9:  store_memory()              → save prompt + response + embedding + tokens + cost
Step 10: return response to user
"""

import os
import time
import uuid
from typing import Optional, Dict, Any, List, Tuple

import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from db import fetch_all, fetch_one
from bandit import select_best, ensure_arm
from vector_db import store_memory, search_similar

load_dotenv(override=True)

# ─── API key accessors (lazy — never at import time) ─────────

def _gemini_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY")

def _groq_key() -> Optional[str]:
    return os.getenv("GROQ_API_KEY")

def _openrouter_key() -> Optional[str]:
    return os.getenv("OPENROUTER_API_KEY")

def _sarvam_key() -> Optional[str]:
    return os.getenv("SARVAM_API_KEY")


# ─── Endpoints & Local Models ────────────────────────────────

GEMINI_GENERATE_URL  = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
OPENROUTER_CHAT_URL  = "https://openrouter.ai/api/v1/chat/completions"
GROQ_CHAT_URL        = "https://api.groq.com/openai/v1/chat/completions"
SARVAM_CHAT_URL      = "https://api.sarvam.ai/v1/chat/completions"

REQUEST_TIMEOUT      = 60

# Load embedding model once in memory (384-dimensional vectors)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ─── Thresholds ──────────────────────────────────────────────

SIMILARITY_THRESHOLD    = 0.92   # cosine similarity to reuse cached response
CONFIDENCE_THRESHOLD    = 0.70   # librarian confidence below this → use bandit


# ─── Category + complexity keywords ──────────────────────────

CODE_KEYWORDS = [
    "code", "function", "class", "implement", "debug", "compile",
    "syntax", "error", "exception", "api", "endpoint", "database",
    "sql", "python", "javascript", "typescript", "java", "rust",
    "react", "fastapi", "html", "css", "git", "docker", "test",
    "refactor", "bug", "deploy",
]
REASONING_KEYWORDS = [
    "reason", "think step by step", "logic", "proof", "prove",
    "mathematical", "theorem", "derive", "deduce", "infer",
    "chain of thought", "analyze deeply", "compare and contrast",
]
HIGH_COMPLEXITY = [
    "explain in detail", "analyze", "compare and contrast", "write a full",
    "implement", "refactor", "debug", "optimize", "architecture",
    "design pattern", "algorithm", "data structure", "machine learning",
    "security audit", "performance tuning", "prove that", "derive",
]
LOW_COMPLEXITY = [
    "hello", "hi", "hey", "thanks", "yes", "no",
    "what is", "define", "who is", "when was", "translate",
    "summarize briefly", "tldr", "list", "name",
]


# ═══════════════════════════════════════════════════════════════
# STEP 1: Classify category
# ═══════════════════════════════════════════════════════════════

def classify_category(prompt: str) -> str:
    """Map prompt strictly to one of: code, agent, chat, image, general."""
    text = prompt.lower().strip()
    
    if sum(1 for kw in CODE_KEYWORDS if kw in text) >= 2:
        return "code"
    
    if any(kw in text for kw in ["agent", "bot", "auto", "scrape", "tool"]):
        return "agent"

    if any(kw in text for kw in ["image", "picture", "photo", "draw", "visualize"]):
        return "image"
    
    if any(kw in text for kw in ["hello", "hi", "hey", "how are you", "thanks"]):
        return "chat"
        
    return "general"


# ═══════════════════════════════════════════════════════════════
# STEP 2: Score complexity
# ═══════════════════════════════════════════════════════════════

def score_complexity(prompt: str) -> int:
    """Heuristic complexity score 1-10."""
    text = prompt.lower().strip()
    score = 5
    words = len(text.split())
    if words < 10:     score -= 2
    elif words < 30:   score -= 1
    elif words > 100:  score += 1
    elif words > 250:  score += 2
    score += min(sum(1 for kw in HIGH_COMPLEXITY if kw in text), 3)
    score -= min(sum(1 for kw in LOW_COMPLEXITY  if kw in text), 2)
    if any(kw in text for kw in CODE_KEYWORDS):  score += 1
    if text.count("?") > 2:                       score += 1
    return max(1, min(10, score))


# ═══════════════════════════════════════════════════════════════
# STEP 3: Generate embedding vector
# ═══════════════════════════════════════════════════════════════

def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Convert text to a 384-dim embedding vector using local sentence-transformers.
    Returns None if generation fails.
    """
    try:
        # Use local model directly (no API key needed)
        vector = embedding_model.encode(text[:8000]).tolist()
        return vector
    except Exception as e:
        print(f"⚠️  Embedding generation failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# STEP 4: Check prompt_memory for a cached similar response
# ═══════════════════════════════════════════════════════════════

def check_memory_cache(
    embedding: Optional[List[float]],
    threshold: float = SIMILARITY_THRESHOLD,
) -> Optional[Dict[str, Any]]:
    """
    Search prompt_memory for a semantically similar past prompt.
    Returns the cached row if cosine similarity >= threshold, else None.
    """
    if not embedding:
        return None     # can't search without a vector

    try:
        results = search_similar(embedding, limit=1)
        if results and float(results[0].get("similarity", 0)) >= threshold:
            return results[0]
    except Exception as e:
        print(f"⚠️  Memory cache search failed: {e}")

    return None


# ═══════════════════════════════════════════════════════════════
# STEP 5: Query model_registry
# ═══════════════════════════════════════════════════════════════

def get_candidates(
    category: str,
    complexity: int,
    max_cost: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Find active models matching category + complexity range."""
    q = """
        SELECT id, model_name, provider, category, tier, sub_tier,
               complexity_min, complexity_max,
               cost_per_1k_input, cost_per_1k_output,
               avg_latency_ms, context_window, priority_rank
        FROM model_registry
        WHERE is_active = TRUE
          AND category = %s
          AND complexity_min <= %s
          AND complexity_max >= %s
    """
    params: list = [category, complexity, complexity]
    if max_cost is not None:
        q += " AND cost_per_1k_input <= %s"
        params.append(max_cost)
    q += " ORDER BY priority_rank ASC, avg_latency_ms ASC LIMIT 20;"
    models = fetch_all(q, tuple(params))

    # Fallback 1: any model in the category
    if not models:
        models = fetch_all("""
            SELECT id, model_name, provider, category, tier, sub_tier,
                   complexity_min, complexity_max,
                   cost_per_1k_input, cost_per_1k_output,
                   avg_latency_ms, context_window, priority_rank
            FROM model_registry
            WHERE is_active = TRUE AND category = %s
            ORDER BY priority_rank ASC LIMIT 10;
        """, (category,))

    # Fallback 2: any active model at all
    if not models:
        models = fetch_all("""
            SELECT id, model_name, provider, category, tier, sub_tier,
                   complexity_min, complexity_max,
                   cost_per_1k_input, cost_per_1k_output,
                   avg_latency_ms, context_window, priority_rank
            FROM model_registry
            WHERE is_active = TRUE
            ORDER BY priority_rank ASC LIMIT 5;
        """)

    if not models:
        raise RuntimeError(
            "No active models in registry. Run POST /discover or start the server "
            "with valid API keys so the librarian can populate the registry."
        )
    return models


# ═══════════════════════════════════════════════════════════════
# STEP 6: Compute librarian confidence
# ═══════════════════════════════════════════════════════════════

def compute_confidence(
    candidates: List[Dict[str, Any]],
    category: str,
    complexity: int,
) -> float:
    """
    Estimate how confident the librarian is about its top-choice model.

    Factors:
      - Number of matching candidates (more = less certain which one)
      - Whether the top model's complexity range tightly fits
      - Whether the top model has Tier 1 sub_tier A (clearest signal)

    Returns a float in [0, 1].
    """
    if not candidates:
        return 0.0

    top = candidates[0]
    score = 0.5   # baseline

    # Tight complexity fit → more confident
    cmin = top.get("complexity_min", 1)
    cmax = top.get("complexity_max", 10)
    range_size = max(1, cmax - cmin)
    if range_size <= 2:
        score += 0.2   # very specific model
    elif range_size <= 4:
        score += 0.1

    # Tier 1A = highest quality signal
    if top.get("tier") == 1 and top.get("sub_tier") == "A":
        score += 0.2
    elif top.get("tier") == 1:
        score += 0.1

    # Many candidates = more ambiguity
    n = len(candidates)
    if n == 1:
        score += 0.1   # only one option — clear
    elif n > 10:
        score -= 0.1   # too many candidates

    return round(max(0.0, min(1.0, score)), 3)


# ═══════════════════════════════════════════════════════════════
# STEP 7: Pick model — librarian or bandit
# ═══════════════════════════════════════════════════════════════

def pick_model(
    category: str,
    complexity: int,
    max_cost: Optional[float] = None,
) -> Tuple[Dict[str, Any], float, str]:
    """
    Returns (selected_model, confidence, selector_used).
    selector_used = 'librarian' | 'bandit'
    """
    candidates = get_candidates(category, complexity, max_cost)
    confidence = compute_confidence(candidates, category, complexity)

    if confidence >= CONFIDENCE_THRESHOLD:
        # Librarian is confident — pick top model by priority_rank
        selected = candidates[0]
        selected["bandit_score"] = None
        return selected, confidence, "librarian"
    else:
        # Confidence is low — let the bandit decide
        selected = select_best(candidates, category)
        return selected, confidence, "bandit"


# ═══════════════════════════════════════════════════════════════
# STEP 8: Call model API
# ═══════════════════════════════════════════════════════════════

def _call_gemini(model_name: str, prompt: str) -> Tuple[str, int, int]:
    key = _gemini_key()
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    url = GEMINI_GENERATE_URL.format(model=model_name)
    resp = requests.post(
        url,
        params={"key": key},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
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
    usage = data.get("usageMetadata", {})
    return text, usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0)


def _call_openrouter(model_name: str, prompt: str) -> Tuple[str, int, int]:
    key = _openrouter_key()
    if not key:
        raise ValueError("OPENROUTER_API_KEY not set")
    resp = requests.post(
        OPENROUTER_CHAT_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048,
            "temperature": 0.7,
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _call_groq(model_name: str, prompt: str) -> Tuple[str, int, int]:
    key = _groq_key()
    if not key:
        raise ValueError("GROQ_API_KEY not set")
    resp = requests.post(
        GROQ_CHAT_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048,
            "temperature": 0.7,
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _call_sarvam(model_name: str, prompt: str) -> Tuple[str, int, int]:
    key = _sarvam_key()
    if not key:
        raise ValueError("SARVAM_API_KEY not set")
    resp = requests.post(
        SARVAM_CHAT_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)

def call_model(provider: str, model_name: str, prompt: str) -> Tuple[str, int, int]:
    """Dispatch to the correct provider. Returns (text, prompt_tokens, completion_tokens)."""
    callers = {
        "gemini": _call_gemini, 
        "openrouter": _call_openrouter, 
        "groq": _call_groq,
        "sarvam": _call_sarvam
    }
    fn = callers.get(provider)
    if not fn:
        raise ValueError(f"Unknown provider: {provider!r}")
    return fn(model_name, prompt)


# ═══════════════════════════════════════════════════════════════
# MAIN: Full routing pipeline
# ═══════════════════════════════════════════════════════════════

def route_prompt(
    prompt: str,
    user_id: Optional[str] = None,
    preferred_category: Optional[str] = None,
    max_cost: Optional[float] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete routing pipeline — Steps 1-10.
    """
    # Step 1: Category
    category = preferred_category or classify_category(prompt)

    # Step 2: Complexity
    complexity = score_complexity(prompt)

    # Step 3: Embedding
    embedding = generate_embedding(prompt)

    # Step 4: Cache check
    cached = check_memory_cache(embedding)
    if cached:
        return {
            "response":        cached["response"],
            "model_used":      cached["model_used"],
            "provider":        "cache",
            "category":        cached.get("category", category),
            "complexity_score": cached.get("complexity_score", complexity),
            "response_time_ms": 0,
            "estimated_cost":   0.0,
            "memory_id":        cached["id"],
            "session_id":       session_id or str(uuid.uuid4())[:8],
            "cache_hit":        True,
            "similarity":       round(float(cached.get("similarity", 1.0)), 4),
            "selector":         "cache",
            "confidence":       1.0,
        }

    # Step 7a: Get candidates + compute confidence
    candidates = get_candidates(category, complexity, max_cost)
    confidence = compute_confidence(candidates, category, complexity)

    # Step 7b: Librarian or bandit picks the primary model
    if confidence >= CONFIDENCE_THRESHOLD:
        primary_model = candidates[0]
        selector = "librarian"
    else:
        primary_model = select_best(candidates, category)
        selector = "bandit"

    primary_model_name = primary_model["model_name"]
    primary_provider = primary_model["provider"]
    ensure_arm(primary_model_name, primary_provider, category)

    # ─── 8. CASCADING FALLBACK EXECUTION ───
    # The Never-Fail Routing System
    
    overall_best = fetch_one("SELECT * FROM model_registry WHERE is_active = TRUE ORDER BY priority_rank ASC LIMIT 1;")
    
    fallback_sequence = [
        # Attempt 1: Target primary model
        (primary_provider, primary_model_name, primary_model),
        
        # Attempt 2: Next best in category
        (candidates[1]["provider"], candidates[1]["model_name"], candidates[1]) if len(candidates) > 1 else None,
        
        # Attempt 3: Overall best model in registry
        (overall_best["provider"], overall_best["model_name"], overall_best) if overall_best else None,
        
        # Attempt 4: Gemini (Default Main Router/Librarian)
        ("gemini", "gemini-2.5-flash", {"cost_per_1k_input": 0.0, "cost_per_1k_output": 0.0}),
        
        # Attempt 5: OpenRouter (Fallback Librarian)
        ("openrouter", "meta-llama/llama-3-8b-instruct", {"cost_per_1k_input": 0.0, "cost_per_1k_output": 0.0})
    ]

    response_text = None
    prompt_tokens = completion_tokens = 0
    final_model_name = final_provider = None
    applied_model_metadata = None
    
    start = time.time()
    
    for attempt in fallback_sequence:
        if not attempt: continue
        
        prov, m_name, m_data = attempt
        try:
            print(f"🔄 Routing Attempt: {prov} / {m_name}")
            response_text, prompt_tokens, completion_tokens = call_model(prov, m_name, prompt)
            
            # If successful, break out of loop
            final_provider = prov
            final_model_name = m_name
            applied_model_metadata = m_data
            break
            
        except Exception as e:
            print(f"⚠️  Model call {prov}/{m_name} failed: {e}. Falling back...")
            continue
            
    if not response_text:
        raise RuntimeError("All fallback routing attempts completely failed.")

    elapsed_ms = int((time.time() - start) * 1000)

    # Estimate cost
    in_rate  = float(applied_model_metadata.get("cost_per_1k_input",  0) or 0)
    out_rate = float(applied_model_metadata.get("cost_per_1k_output", 0) or 0)
    cost = round(
        (prompt_tokens * in_rate / 1000) + (completion_tokens * out_rate / 1000), 6
    )

    # Step 9: Store in prompt_memory (with embedding)
    memory_id = store_memory(
        prompt=prompt,
        response=response_text,
        model_used=final_model_name,
        provider=final_provider,
        category=category,
        complexity_score=complexity,
        response_time_ms=elapsed_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        actual_cost=cost,
        user_id=user_id,
        embedding=embedding,
    )

    # Step 10: Return
    return {
        "response":         response_text,
        "model_used":       model_name,
        "provider":         provider,
        "category":         category,
        "complexity_score": complexity,
        "response_time_ms": elapsed_ms,
        "estimated_cost":   cost,
        "memory_id":        memory_id,
        "session_id":       session_id or str(uuid.uuid4())[:8],
        "cache_hit":        False,
        "similarity":       None,
        "selector":         selector,
        "confidence":       confidence,
    }