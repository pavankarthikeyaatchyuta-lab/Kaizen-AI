"""
Kaizen AI — FastAPI Backend
Wires ingestion + KG + ML + reasoning into REST endpoints.

Endpoints:
  POST /ingest          — upload industrial documents
  GET  /kg/stats        — knowledge graph statistics
  GET  /kg/visualize    — export KG as interactive HTML
  GET  /kg/equipment/{id} — equipment context
  POST /query           — Industrial Reasoning Engine (main hero endpoint)
  POST /predict         — ML prediction only (sensor data)
  POST /workorder       — generate PDF work order
  GET  /dashboard       — executive KPI summary
  GET  /health          — health check
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from ingestion import ingest_document, DocumentRegistry
from knowledge_graph import KaizenKnowledgeGraph
from ml_engine import PredictiveMaintenanceModel, train_and_save
from reasoning_engine import IndustrialReasoningEngine, VectorStore

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Kaizen AI",
    description="Industrial Knowledge Intelligence Platform — Turning Documents into Decisions",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Global State (initialized on startup) ────────────────────────────────────

class AppState:
    vector_store: Optional[VectorStore] = None
    knowledge_graph: Optional[KaizenKnowledgeGraph] = None
    ml_model: Optional[PredictiveMaintenanceModel] = None
    reasoning_engine: Optional[IndustrialReasoningEngine] = None
    doc_registry: Optional[DocumentRegistry] = None
    ingested_docs: list = []
    startup_time: str = ""

state = AppState()

UPLOAD_DIR  = Path("./uploads")
MODELS_DIR  = Path("./models")
EXPORTS_DIR = Path("./exports")

for d in [UPLOAD_DIR, MODELS_DIR, EXPORTS_DIR]:
    d.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup():
    logger.info("Initializing Kaizen AI...")
    state.startup_time = datetime.utcnow().isoformat()

    state.doc_registry    = DocumentRegistry()
    state.vector_store    = VectorStore()
    state.knowledge_graph = KaizenKnowledgeGraph()

    # Load or train ML model
    rul_path = MODELS_DIR / "rul_model.pkl"
    state.ml_model = PredictiveMaintenanceModel()
    if rul_path.exists():
        try:
            state.ml_model.load(str(MODELS_DIR))
            logger.info("ML models loaded from disk")
        except Exception as e:
            logger.warning(f"Failed to load models: {e}. Training fresh...")
            state.ml_model.train(n_assets=200)
            state.ml_model.save(str(MODELS_DIR))
    else:
        logger.info("Training ML models (first run)...")
        state.ml_model.train(n_assets=200)
        state.ml_model.save(str(MODELS_DIR))

    state.reasoning_engine = IndustrialReasoningEngine(
        vector_store=state.vector_store,
        knowledge_graph=state.knowledge_graph,
        ml_model=state.ml_model,
        model_name="gemini-1.5-flash",
    )

    # Seed KG with demo equipment if empty
    if state.knowledge_graph.G.number_of_nodes() == 0:
        _seed_demo_kg()

    logger.info("Kaizen AI ready")


def _seed_demo_kg():
    """Seed with realistic demo industrial data."""
    kg = state.knowledge_graph

    # Equipment
    kg.add_equipment("P-104", "Centrifugal Feed Pump",     "pump",       location="Unit-3", criticality="high")
    kg.add_equipment("P-201", "Cooling Water Pump",        "pump",       location="Unit-1", criticality="medium")
    kg.add_equipment("M-104", "Drive Motor (P-104)",       "motor",      location="Unit-3", criticality="high")
    kg.add_equipment("C-10",  "Air Compressor",            "compressor", location="Unit-5", criticality="high")
    kg.add_equipment("HX-03", "Heat Exchanger",            "vessel",     location="Unit-2", criticality="medium")

    # Components
    from knowledge_graph import _nid
    for eq, comps in {
        "P-104": ["Bearing B-2", "Mechanical Seal S-1", "Impeller I-1", "Coupling C-1"],
        "P-201": ["Bearing B-5", "Wear Ring WR-2"],
        "C-10":  ["Piston P-1", "Valve V-3", "Bearing B-8"],
    }.items():
        eq_nid = _nid("equipment", eq)
        for comp in comps:
            c_nid = kg.add_node("component", comp, title=f"Component: {comp}")
            kg.add_edge(eq_nid, c_nid, "HAS_COMPONENT")

    # Motor drives pump
    kg.add_edge(_nid("equipment","M-104"), _nid("equipment","P-104"), "DRIVES")

    # Historical failures
    kg.add_failure_event("P-104", "bearing_degradation", "HIGH",
                          root_cause="Lubrication overdue by 42 hours", source_doc="INC-019")
    kg.add_failure_event("P-104", "seal_failure", "MEDIUM",
                          root_cause="Dry running during startup", source_doc="INC-007")
    kg.add_failure_event("C-10",  "valve_leakage", "HIGH",
                          root_cause="Wear after 3000 hours", source_doc="INC-031")

    # Maintenance records
    kg.add_maintenance_record("P-104", "Bearing replacement",
                               technician="Ravi Kumar",
                               parts=["SKF 6205 Bearing", "Bearing grease 200g"],
                               date="2025-03-12")
    kg.add_maintenance_record("P-104", "Mechanical seal replacement",
                               technician="Suresh Babu",
                               parts=["John Crane Type 1 Seal"],
                               date="2024-11-08")
    kg.add_maintenance_record("P-201", "Scheduled lubrication",
                               technician="Ramesh G.",
                               parts=["Mobil Grease XHP 222"],
                               date="2025-05-20")

    # Standards
    for std in ["OISD-113", "Factory Act Section 7A", "ISO 10816-3"]:
        std_nid = kg.add_node("standard", std, title=f"Standard: {std}")
        kg.add_edge(_nid("equipment","P-104"), std_nid, "COMPLIES_WITH")

    # Current prediction
    kg.add_prediction("P-104",
                       failure_prob=0.87, rul_days=14,
                       risk_level="CRITICAL",
                       top_causes=["Bearing degradation", "Lubrication overdue"])

    logger.info(f"Demo KG seeded: {kg.stats()}")


# ─── Request / Response Models ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    sensor_data: Optional[dict] = None
    n_doc_results: int = 4

class PredictRequest(BaseModel):
    equipment_id: str
    vibration_mm_s: float
    temperature_c: float
    pressure_bar: float
    rpm: float
    flow_rate_m3h: float
    lubrication_hours_since: float
    runtime_hours: float

class WorkOrderRequest(BaseModel):
    equipment_id: str
    equipment_name: str
    priority: str                  # CRITICAL / HIGH / MEDIUM / LOW
    failure_type: str
    description: str
    recommended_actions: list[str]
    spare_parts: Optional[list[str]] = None
    assigned_to: Optional[str] = None
    estimated_hours: Optional[float] = None
    due_within_hours: Optional[float] = None
    safety_precautions: Optional[list[str]] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "startup_time": state.startup_time,
        "chunks_indexed": state.vector_store.count(),
        "kg_nodes": state.knowledge_graph.G.number_of_nodes(),
        "kg_edges": state.knowledge_graph.G.number_of_edges(),
        "ml_trained": state.ml_model.is_trained,
        "docs_ingested": len(state.ingested_docs),
    }


@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...),
                 background_tasks: BackgroundTasks = None):
    """Upload and ingest industrial documents into KG + vector store."""
    results = []

    for upload in files:
        # Save to disk
        ext = Path(upload.filename).suffix
        tmp = UPLOAD_DIR / f"{upload.filename}"
        content = await upload.read()
        tmp.write_bytes(content)

        try:
            result = ingest_document(str(tmp), registry=state.doc_registry)

            if result.success:
                # Add to vector store
                state.vector_store.add_chunks(result.chunks)
                # Add to knowledge graph
                state.knowledge_graph.ingest_result(result)
                state.ingested_docs.append({
                    "filename":    result.filename,
                    "doc_type":    result.doc_type,
                    "chunks":      len(result.chunks),
                    "entities":    len(result.entities),
                    "trust_score": result.doc_meta.trust_score if result.doc_meta else None,
                    "revision":    result.doc_meta.revision if result.doc_meta else None,
                    "timestamp":   datetime.utcnow().isoformat(),
                })

            results.append({
                "filename": result.filename,
                "success":  result.success,
                "doc_type": result.doc_type,
                "chunks":   len(result.chunks),
                "entities": len(result.entities),
                "trust_score": result.doc_meta.trust_score if result.doc_meta else None,
                "revision":    result.doc_meta.revision if result.doc_meta else None,
                "is_duplicate": result.doc_meta.is_duplicate if result.doc_meta else False,
                "error":    result.error,
            })

        except Exception as e:
            logger.error(f"Ingestion failed for {upload.filename}: {e}")
            results.append({"filename": upload.filename, "success": False, "error": str(e)})

    return {
        "ingested": len([r for r in results if r["success"]]),
        "failed":   len([r for r in results if not r["success"]]),
        "total_chunks_indexed": state.vector_store.count(),
        "kg_nodes": state.knowledge_graph.G.number_of_nodes(),
        "results": results,
    }


@app.post("/query")
async def query(req: QueryRequest):
    """Main hero endpoint — Industrial Reasoning Engine."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = state.reasoning_engine.query(
            user_query=req.query,
            sensor_data=req.sensor_data,
            n_doc_results=req.n_doc_results,
        )
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict")
async def predict(req: PredictRequest):
    """ML-only prediction from sensor readings."""
    sensor_data = {
        "vibration_mm_s":          req.vibration_mm_s,
        "temperature_c":           req.temperature_c,
        "pressure_bar":            req.pressure_bar,
        "rpm":                     req.rpm,
        "flow_rate_m3h":           req.flow_rate_m3h,
        "lubrication_hours_since": req.lubrication_hours_since,
        "runtime_hours":           req.runtime_hours,
    }
    try:
        result = state.ml_model.predict(req.equipment_id, sensor_data)
        return {
            "equipment_id":          result.equipment_id,
            "failure_probability":   result.failure_probability,
            "rul_days":              result.rul_days,
            "risk_level":            result.risk_level,
            "predicted_failure_type": result.predicted_failure_type,
            "health_score":          result.health_score,
            "feature_contributions": result.feature_contributions,
            "confidence":            result.confidence,
            "recommendation":        result.recommendation,
            "urgency_hours":         result.urgency_hours,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/kg/stats")
def kg_stats():
    return state.knowledge_graph.stats()


@app.get("/kg/visualize", response_class=HTMLResponse)
def kg_visualize(equipment_id: Optional[str] = None):
    """Return interactive KG visualization as HTML."""
    out = EXPORTS_DIR / "kg_viz.html"
    state.knowledge_graph.visualize(
        output_path=str(out),
        focus_equipment=equipment_id,
    )
    return HTMLResponse(content=out.read_text(), status_code=200)


@app.get("/kg/graph-data")
def kg_graph_data():
    """Return KG as JSON for D3/custom frontend rendering."""
    return state.knowledge_graph.to_json()


@app.get("/kg/equipment/{equipment_id}")
def kg_equipment(equipment_id: str):
    ctx = state.knowledge_graph.get_equipment_context(equipment_id.upper(), depth=2)
    if not ctx.get("found"):
        raise HTTPException(status_code=404,
                            detail=f"Equipment {equipment_id} not found in knowledge graph")
    return {
        **ctx,
        "maintenance_history": state.knowledge_graph.get_maintenance_history(equipment_id.upper()),
        "component_chain":     state.knowledge_graph.get_component_chain(equipment_id.upper()),
    }


@app.get("/dashboard")
def dashboard():
    """Executive KPI summary."""
    kg = state.knowledge_graph
    stats = kg.stats()

    # Count risk levels from predictions in graph
    risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for _, attrs in kg.G.nodes(data=True):
        if attrs.get("node_type") == "prediction":
            rl = attrs.get("risk_level", "LOW")
            risk_counts[rl] = risk_counts.get(rl, 0) + 1

    equipment_count = stats.get("node_types", {}).get("equipment", 0)
    healthy = max(0, equipment_count - risk_counts["CRITICAL"] - risk_counts["HIGH"])

    return {
        "summary": {
            "total_assets":        equipment_count,
            "healthy_assets":      healthy,
            "critical_alerts":     risk_counts["CRITICAL"],
            "high_alerts":         risk_counts["HIGH"],
            "docs_ingested":       len(state.ingested_docs),
            "chunks_indexed":      state.vector_store.count(),
            "kg_nodes":            stats["total_nodes"],
            "kg_edges":            stats["total_edges"],
            "failure_events_logged": stats.get("failure_events", 0),
            "compliance_score":    94,  # demo value
        },
        "risk_distribution": risk_counts,
        "recent_docs":  state.ingested_docs[-5:],
        "kg_breakdown": stats.get("node_types", {}),
        "timestamp":    datetime.utcnow().isoformat(),
    }


@app.get("/docs-list")
def docs_list():
    return {"documents": state.ingested_docs, "total": len(state.ingested_docs)}


@app.post("/workorder")
async def generate_work_order(req: WorkOrderRequest):
    """Generate a PDF work order from recommendation."""
    wo_number = f"KAI-WO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    filename  = f"{wo_number}.pdf"
    out_path  = EXPORTS_DIR / filename

    _generate_work_order_pdf(req, wo_number, str(out_path))
    return FileResponse(
        path=str(out_path),
        filename=filename,
        media_type="application/pdf",
    )


def _generate_work_order_pdf(req: WorkOrderRequest, wo_number: str, out_path: str):
    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    KAIZEN_ORANGE = colors.HexColor("#FF6B35")
    DARK          = colors.HexColor("#1a1a2e")

    title_style = ParagraphStyle("title", parent=styles["Title"],
                                  textColor=DARK, fontSize=20, spaceAfter=4)
    subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"],
                                     textColor=KAIZEN_ORANGE, fontSize=11,
                                     spaceAfter=12)
    section_style = ParagraphStyle("section", parent=styles["Heading2"],
                                    textColor=KAIZEN_ORANGE, fontSize=12,
                                    spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("body", parent=styles["Normal"],
                                 fontSize=10, spaceAfter=4, leading=15)

    # Header
    story.append(Paragraph("⚙ KAIZEN AI", title_style))
    story.append(Paragraph("Industrial Knowledge Intelligence Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=KAIZEN_ORANGE))
    story.append(Spacer(1, 0.4*cm))

    # Work Order Info Table
    priority_color = {
        "CRITICAL": colors.HexColor("#E74C3C"),
        "HIGH":     colors.HexColor("#E67E22"),
        "MEDIUM":   colors.HexColor("#F39C12"),
        "LOW":      colors.HexColor("#27AE60"),
    }.get(req.priority.upper(), colors.grey)

    info_data = [
        ["WORK ORDER",     wo_number,         "DATE",      datetime.utcnow().strftime("%d %b %Y")],
        ["EQUIPMENT ID",   req.equipment_id,  "NAME",      req.equipment_name],
        ["PRIORITY",       req.priority,      "FAILURE",   req.failure_type],
        ["ASSIGNED TO",    req.assigned_to or "TBD",
         "EST. DURATION",  f"{req.estimated_hours or 'TBD'} hrs"],
        ["DUE WITHIN",     f"{req.due_within_hours or 'TBD'} hrs",
         "GENERATED BY",   "Kaizen AI"],
    ]

    info_table = Table(info_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), DARK),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",     (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",     (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("BACKGROUND",   (0,1), (-1,-1), colors.HexColor("#f8f9fa")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f8f9fa")]),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#dee2e6")),
        ("PADDING",      (0,0), (-1,-1), 6),
        ("BACKGROUND",   (1,2), (1,2), priority_color),
        ("TEXTCOLOR",    (1,2), (1,2), colors.white),
        ("FONTNAME",     (1,2), (1,2), "Helvetica-Bold"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    # Description
    story.append(Paragraph("PROBLEM DESCRIPTION", section_style))
    story.append(Paragraph(req.description, body_style))

    # Recommended Actions
    story.append(Paragraph("RECOMMENDED ACTIONS", section_style))
    for i, action in enumerate(req.recommended_actions, 1):
        story.append(Paragraph(f"{i}. {action}", body_style))

    # Spare Parts
    if req.spare_parts:
        story.append(Paragraph("SPARE PARTS REQUIRED", section_style))
        parts_data = [["#", "Part Description", "Status"]]
        for i, part in enumerate(req.spare_parts, 1):
            parts_data.append([str(i), part, "To be sourced"])
        parts_table = Table(parts_data, colWidths=[1.2*cm, 12*cm, 4.5*cm])
        parts_table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), DARK),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 9),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f8f9fa")]),
            ("PADDING",     (0,0), (-1,-1), 6),
        ]))
        story.append(parts_table)

    # Safety Precautions
    if req.safety_precautions:
        story.append(Paragraph("SAFETY PRECAUTIONS", section_style))
        for precaution in req.safety_precautions:
            story.append(Paragraph(f"⚠ {precaution}", body_style))

    # Sign-off
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")))
    story.append(Spacer(1, 0.4*cm))
    signoff_data = [
        ["Raised By (AI)", "Reviewed By", "Approved By", "Completed By"],
        ["Kaizen AI", "________________", "________________", "________________"],
        [datetime.utcnow().strftime("%d %b %Y %H:%M"), "Date: ______", "Date: ______", "Date: ______"],
    ]
    signoff_table = Table(signoff_data, colWidths=[4.4*cm]*4)
    signoff_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 8),
        ("ALIGN",     (0,0), (-1,-1), "CENTER"),
        ("GRID",      (0,0), (-1,-1), 0.5, colors.HexColor("#dee2e6")),
        ("PADDING",   (0,0), (-1,-1), 8),
        ("BACKGROUND",(0,0), (-1,0), colors.HexColor("#f8f9fa")),
    ]))
    story.append(signoff_table)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"Generated by Kaizen AI Industrial Knowledge Intelligence Platform | {wo_number}",
        ParagraphStyle("footer", parent=styles["Normal"],
                        fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    logger.info(f"Work order PDF generated: {out_path}")


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
