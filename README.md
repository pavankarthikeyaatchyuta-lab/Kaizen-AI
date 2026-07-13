# ⚙ Kaizen AI
### Industrial Knowledge Intelligence Platform
*Turning Industrial Documents into Operational Decisions.*

Named after the Japanese philosophy of continuous improvement — Kaizen AI gets smarter with every document your plant uploads.

---

## Architecture

```
Documents (PDF/DOCX/Excel/Images)
        │
        ▼
┌─────────────────────┐
│  Document Ingestion  │  OCR · Section-aware chunking · Entity extraction
│  (ingestion.py)      │  Version detection · Trust scoring
└──────────┬──────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
┌─────────┐  ┌──────────┐
│ Vector  │  │Knowledge │  NetworkX graph · Equipment/Component/Failure
│  Store  │  │  Graph   │  Maintenance/Technician/Document nodes
│(ChromaDB│  │  (KG)    │  Auto-relationship discovery
└────┬────┘  └────┬─────┘
     │             │
     └──────┬──────┘
            │         ┌──────────────┐
            ▼         │  ML Engine   │  XGBoost RUL predictor
     ┌─────────────┐  │  (ml_engine) │  Failure classifier
     │  Industrial │◄─┤              │  Synthetic degradation data
     │  Reasoning  │  └──────────────┘
     │  Engine     │
     └──────┬──────┘
            │  Evidence Fusion · Confidence scoring
            ▼
     ┌─────────────┐
     │  Gemini LLM │  Consumer of intelligence, not the intelligence
     └──────┬──────┘
            │
            ▼
  Explainable Recommendation
  + Citations + Confidence Meter
  + Work Order PDF
```

## Hero Demo Flow

```
1. Upload 10 industrial PDFs (manuals, logs, inspection reports)
2. Knowledge Graph builds visibly
3. Query: "Pump P-104 vibration increased to 7.8 mm/s"
4. System returns:
   - Root cause (bearing degradation)
   - 3 source citations with sections
   - ML prediction: 87% failure probability, 14 days RUL
   - Confidence breakdown: Docs 42% | KG 27% | ML 22% | Rules 9%
   - One-click Work Order PDF
```

## Setup

```bash
# 1. Clone and install
pip install -r requirements.txt

# Also install tesseract (for OCR)
# Ubuntu: sudo apt install tesseract-ocr
# Mac:    brew install tesseract

# 2. Configure
cp .env.example .env
# Add your GEMINI_API_KEY

# 3. Run backend
cd api
python main.py

# 4. API docs
open http://localhost:8000/docs
```

## Core Modules

| File | Purpose |
|------|---------|
| `core/ingestion.py` | Document parsing, OCR, entity extraction, trust scoring |
| `core/knowledge_graph.py` | Industrial ontology, graph traversal, Pyvis visualization |
| `core/ml_engine.py` | XGBoost RUL + failure classifier, synthetic data generator |
| `core/reasoning_engine.py` | Evidence fusion, confidence scoring, LLM explanation |
| `api/main.py` | FastAPI backend, work order PDF generation |

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/ingest` | Upload documents |
| POST | `/query` | Industrial Reasoning Engine |
| POST | `/predict` | ML prediction from sensor data |
| GET | `/kg/visualize` | Interactive KG visualization |
| GET | `/kg/equipment/{id}` | Equipment context |
| GET | `/dashboard` | Executive KPI summary |
| POST | `/workorder` | Generate PDF work order |
| GET | `/health` | Health check |

## Judging Alignment

| Criterion | Implementation |
|-----------|---------------|
| Innovation | 3-source evidence fusion (not just RAG) · KG auto-relationship discovery |
| Business Impact | End-to-end: document → decision → work order in <60 seconds |
| Technical Excellence | Real XGBoost ML · Section-aware RAG · OCR confidence propagation |
| Scalability | FastAPI · ChromaDB · NetworkX → Neo4j in production |
| UX | Confidence meter · Source citations · Explainable AI output |

---
*ET AI Hackathon 2.0 — Problem Statement #8: Industrial Knowledge Intelligence*
