import os
import json
import requests
from google import genai
from dotenv import load_dotenv

# ============================
# 🔹 LOAD ENV
# ============================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Configure Gemini
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"[WARNING] Failed to initialize Gemini client: {e}")
    client = None

# ============================
# 🔹 COMMON PROMPT
# ============================
def build_prompt(user_prompt):
    return f"""
You are an AI router.

Analyze the user prompt and return:

- category: CODE, TEXT, IMAGE, VIDEO, OTHER
- complexity: number from 1 to 10
- confidence: number from 0 to 1

Return ONLY JSON:

{{
    "category": "...",
    "complexity": number,
    "confidence": number
}}

USER PROMPT:
{user_prompt}
"""


# ============================
# 🔹 GEMINI
# ============================
def gemini_analyze(prompt):
    if client is None:
        raise Exception("Gemini client not initialized")

    print("[ROUTER] Using Gemini")

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=build_prompt(prompt)
    )

    if not response.text:
        raise Exception("Empty response from Gemini")

    return parse_json(response.text)


# ============================
# 🔹 GROQ (BACKUP)
# ============================
def groq_analyze(prompt):
    print("[ROUTER] Using Groq (backup)")

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "Return JSON only"},
            {"role": "user", "content": build_prompt(prompt)}
        ]
    }

    res = requests.post(url, headers=headers, json=data)
    response_json = res.json()

    print("[GROQ RAW RESPONSE]:", response_json)

    if "choices" not in response_json:
        raise Exception(f"Groq API Error: {response_json}")

    output = response_json["choices"][0]["message"]["content"]

    return parse_json(output)


# ============================
# 🔹 OPENROUTER (BACKUP)
# ============================
def openrouter_analyze(prompt):
    print("[ROUTER] Using OpenRouter (backup)")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        # safer model
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": build_prompt(prompt)}
        ]
    }

    res = requests.post(url, headers=headers, json=data)
    response_json = res.json()

    print("[OPENROUTER RAW RESPONSE]:", response_json)

    if "choices" not in response_json:
        raise Exception(f"OpenRouter API Error: {response_json}")

    output = response_json["choices"][0]["message"]["content"]

    return parse_json(output)


# ============================
# 🔹 JSON PARSER
# ============================
def parse_json(text):
    print("[RAW OUTPUT]:", text)

    try:
        cleaned = text.strip()

        if "```" in cleaned:
            cleaned = cleaned.replace("```json", "").replace("```", "")

        return json.loads(cleaned)

    except Exception as e:
        print("[ERROR] JSON parse failed:", e)
        raise


# ============================
# 🔹 MAIN ROUTER
# ============================
def route_prompt(prompt):
    print("\n========== ROUTER START ==========")
    print("[INPUT]:", prompt)

    # Step 1: Try Gemini
    try:
        result = gemini_analyze(prompt)
        router_used = "gemini"

    except Exception as e:
        print("[FAIL] Gemini failed:", e)

        # Step 2: Try Groq
        try:
            result = groq_analyze(prompt)
            router_used = "groq"

        except Exception as e:
            print("[FAIL] Groq failed:", e)

            # Step 3: Try OpenRouter
            try:
                result = openrouter_analyze(prompt)
                router_used = "openrouter"

            except Exception as e:
                print("[FAIL] OpenRouter failed:", e)
                raise Exception("All router models failed")

    print("[FINAL RESULT]:", result)
    print("[ROUTER USED]:", router_used)
    print("========== ROUTER END ==========\n")

    return {
        "category": result.get("category"),
        "complexity": result.get("complexity"),
        "confidence": result.get("confidence"),
        "router_used": router_used
    }