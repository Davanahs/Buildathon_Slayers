from fastapi import FastAPI
from pydantic import BaseModel
from router import route_prompt

# Initialize FastAPI app
app = FastAPI()


# ============================
# 🔹 Request Schema
# ============================
class PromptRequest(BaseModel):
    prompt: str


# ============================
# 🔹 Health Check Route
# ============================
@app.get("/")
def home():
    print("[API] Health check called")
    return {"status": "Router running 🚀"}


# ============================
# 🔹 Main Router Endpoint
# ============================
@app.post("/route")
def route(req: PromptRequest):
    print("\n[API] Incoming request")
    print("[API] Prompt:", req.prompt)

    try:
        result = route_prompt(req.prompt)

        print("[API] Sending response")

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        print("[API ERROR]:", str(e))

        return {
            "success": False,
            "error": str(e)
        }