🚀 AI Router System

An intelligent AI routing system that reduces cost, improves efficiency, and selects the best model dynamically using embeddings and smart routing.

🎯 Problem Statement

Modern AI systems face key inefficiencies:

❌ High-end models are used for simple tasks
❌ Leads to waste of API credits
❌ No intelligent model selection
❌ Repeated queries are recomputed

👉 Result: High cost + poor efficiency

💡 Our Solution

We built an AI Router System that:

Uses Sentence Transformers for embeddings
Stores vectors in PGVector (PostgreSQL)
Performs semantic similarity search
Uses a Router Model (Gemini + fallback)
Dynamically selects the best model based on:
Category
Complexity
Confidence

👉 Goal: Efficient + Cost-Optimized AI

🏗️ System Flow
User Prompt
   ↓
Embedding Model (Sentence Transformer)
   ↓
Vector DB (PGVector)

IF MATCH → Return Stored Response
IF MISS →
   ↓
Router Model (Gemini → Groq/OpenRouter fallback)
   ↓
Category + Complexity + Confidence
   ↓
Fetch Models from DB
   ↓
Select Best Model
   ↓
Generate Response
   ↓
Store in DB
⚙️ Features
✅ Embedding-based caching
✅ Smart model routing
✅ Multi-model fallback (Gemini → Groq/OpenRouter)
✅ Cost optimization
✅ Scalable architecture
🛠️ Tech Stack
FastAPI (Backend)
Sentence Transformers (Embeddings)
PostgreSQL + PGVector
Gemini API
Groq API
OpenRouter API
Python
📦 Installation
1️⃣ Clone the repo
git clone <your-repo-url>
cd ai-router-system
2️⃣ Backend Setup
cd backend
pip install -r requirements.txt
3️⃣ Create .env file
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
OPENROUTER_API_KEY=your_key
DATABASE_URL=your_db_url
▶️ Run Backend
cd backend
uvicorn main:app --reload

👉 Open Swagger UI:

http://127.0.0.1:8000/docs
💻 Frontend Setup (if available)
cd frontend
npm install
npm run dev

👉 Open:

http://localhost:3000
🧪 Example API
POST /route
{
  "prompt": "Write a Python function to reverse a string"
}
🔄 Router Logic
Default → Gemini
If fails → Groq
If fails → OpenRouter

👉 Returns:

Category
Complexity
Confidence
🔮 Future Work
🧠 Bandit system (learning from feedback)
⚡ Advanced caching system
🤖 Replace LLM router with lightweight models
🔁 Cascading fallback system
📊 Model performance tracking
🎯 Impact
⚡ Faster responses
💸 Reduced cost
🧠 Smarter model selection
📈 Scalable system
🧑‍💻 Quick Run Commands
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
🏁 Conclusion

This system ensures:

👉 Right model for the right task
👉 Reduced API cost
👉 Improved efficiency over time
