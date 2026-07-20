<div align="center">
  <h1>🏭⚙️ Kaizen AI 🧠</h1>
  <h3>Industrial Knowledge Intelligence Platform</h3>
  <i>Turning Industrial Documents into Operational Decisions.</i>
</div>

---

**Kaizen AI** is an advanced Industrial Intelligence Agent designed to prevent catastrophic equipment failures. Traditional maintenance relies on static schedules or simple threshold alerts. Kaizen AI fuses **Live Sensor Telemetry 📡**, **Predictive Machine Learning 📈 (XGBoost)**, and an **Agentic RAG Pipeline 🔍** (powered by Upstash Vector & Knowledge Graphs) to reason over your plant's technical manuals in real-time. 

Named after the Japanese philosophy of continuous improvement — Kaizen AI gets smarter with every document your plant uploads.

## 🏗 Architecture 

Unlike standard chatbots, Kaizen AI uses a multi-layered Intelligence architecture where the LLM is the *consumer* of intelligence, not the intelligence itself.

```text
📄 Documents (PDF/Excel) & 📡 Live Sensor Data
         │
         ▼
┌─────────────────────────────────┐
│ 🔍 Multi-Modal Extraction       │ OCR · Section-aware chunking
│  (PyMuPDF, Tesseract)           │ Trust scoring · Entity extraction
└───────────┬─────────────────────┘
            │
      ┌─────┴──────┐
      ▼            ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│ 🗄️ Vector │  │🕸️Knowledge│  │ 📈 ML Engine  │ XGBoost RUL predictor
│  Store  │  │  Graph   │  │  (Scikit)    │ Failure classifier
│(Upstash)│  │(NetworkX)│  │              │ Synthetic degradation data
└────┬────┘  └────┬─────┘  └──────┬───────┘
     │            │               │
     └──────┬─────┴───────────────┘
            │  Evidence Fusion & Confidence Scoring
            ▼
┌───────────────────────────┐
│ 🤖 Industrial Reasoner    │ (Primary: Gemini 1.5 Flash)
│ Dual-LLM Redundancy       │ (Fallback: Groq / LLaMA 3)
└───────────┬───────────────┘
            │
            ▼
 📝 Explainable Recommendation
 + 🔗 Citations + 📊 Confidence Meter
 + 🛠️ Work Order PDF Generation
```

## 🚀 Hero Demo Flow (What to show the judges)

1. **Ingest 📂:** Upload an industrial manual (PDF). Watch the Knowledge Graph build visibly as entities are extracted.
2. **Simulate 🌡️:** Go to the Query Engine and simulate a failing pump (e.g., Vibration > 7.8 mm/s, Temp > 85°C).
3. **Reason 🧠:** Ask the agent what is happening.
4. **Result 📊:** The system returns:
   - Root cause (e.g., Bearing Degradation) via XGBoost prediction.
   - Source citations linking exactly to the uploaded manual via Upstash Vector.
   - A transparent Confidence Breakdown: (e.g., Docs 42% | KG 27% | ML 22% | Rules 9%)
5. **Action 🛠️:** Click **Generate Work Order** to instantly create a PDF maintenance ticket.

## 🛠️ Local Setup & How to Run ⚡

Kaizen AI is designed to run locally with lightning-fast Vite and FastAPI. **Follow these steps exactly to run the app on your machine:**

### 1️⃣ Prerequisites
- **Python 3.10+** 🐍
- **Node.js 18+** 🟩

### 2️⃣ Environment Variables 🔐
Create a `.env` file in the root directory:
```env
# Primary LLM
GEMINI_API_KEY=your_gemini_key

# Fallback LLM (High-Availability Redundancy)
GROQ_API_KEY=your_groq_key

# Serverless Vector Database
UPSTASH_VECTOR_REST_URL=your_upstash_url
UPSTASH_VECTOR_REST_TOKEN=your_upstash_token
```

### 3️⃣ Start the Backend (FastAPI + ML Engine) 🖥️
Open your terminal and run:
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server (Runs on port 8000)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4️⃣ Start the Frontend (React + Vite) 🌐
Open a **second** terminal window:
```bash
cd frontend
npm install
npm run dev
```
**🎉 Navigate to `http://localhost:3000` in your browser to interact with Kaizen AI!**

## ☁️ Cloud Deployment (Vercel Monorepo) 🚀

The repository is configured for a **zero-config Serverless Vercel deployment**:
1. Import this repository into Vercel.
2. Add your `.env` variables to the Vercel Dashboard.
3. Add `VITE_API_URL=/api` to route the React frontend to the Serverless Python backend.
4. Deploy! Vercel will automatically build the Vite frontend and serve the FastAPI backend as Serverless Functions using the `vercel.json` rewrite rules.

## 🎯 Judging Alignment 🏆

| Criterion | Implementation |
|-----------|---------------|
| **Innovation 💡** | 3-source evidence fusion (Vector + Graph + ML) instead of basic RAG. |
| **Business Impact 📈** | End-to-end automation: document → telemetry → decision → PDF work order. |
| **Technical Excellence ⚙️** | Real XGBoost ML models · Serverless Upstash Vector DB · Dual-LLM Groq/Gemini failover. |
| **Scalability 🧱** | Stateless FastAPI · React/Vite · Serverless-ready architecture. |
| **UX ✨** | Transparent "Confidence Meter", specific source citations, and actionable UI. |

---
*Built for ET AI Hackathon 2.0 — Problem Statement #8: Industrial Knowledge Intelligence* 🏭
