"""
Kaizen AI — Industrial Reasoning Engine
The heart of the platform.

Pipeline:
  Query → Intent Extraction → [Vector Search + KG Traversal + ML Prediction]
        → Evidence Fusion → Confidence Scoring → LLM Explanation
        → Structured Response with citations

LLM is the consumer of intelligence, not the intelligence itself.
"""

import os
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
from dotenv import load_dotenv

from knowledge_graph import KaizenKnowledgeGraph
from ml_engine import PredictiveMaintenanceModel, PredictionResult

load_dotenv()
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


# ─── Evidence Objects ─────────────────────────────────────────────────────────

@dataclass
class DocumentEvidence:
    source_file: str
    section: str
    content: str
    relevance_score: float
    trust_score: float
    ocr: bool
    chunk_id: str

    @property
    def weighted_confidence(self) -> float:
        return round(self.relevance_score * self.trust_score, 3)

    def to_context_str(self) -> str:
        return f"[{self.source_file} | {self.section}]\n{self.content[:600]}"


@dataclass
class KGEvidence:
    equipment_id: str
    related_nodes: list
    relationships: list
    failure_history: list
    maintenance_history: list
    component_chain: list
    confidence: float = 1.0

    def to_context_str(self) -> str:
        lines = [f"Knowledge Graph Context for {self.equipment_id}:"]
        if self.component_chain:
            comps = ", ".join(c["component"] for c in self.component_chain[:5])
            lines.append(f"  Components: {comps}")
        if self.failure_history:
            for fh in self.failure_history[:3]:
                lines.append(f"  Past failure: {fh.get('failure')} "
                             f"(cause: {fh.get('root_cause', 'unknown')})")
        if self.maintenance_history:
            for mh in self.maintenance_history[:3]:
                lines.append(f"  Maintenance: {mh.get('action')} "
                             f"on {mh.get('date', 'unknown')} "
                             f"by {mh.get('technician', 'unknown')}")
        if self.relationships:
            for rel in self.relationships[:5]:
                lines.append(f"  {rel['from']} -> [{rel['relation']}] -> {rel['to']}")
        return "\n".join(lines)


@dataclass
class FusedEvidence:
    query: str
    equipment_id: Optional[str]
    document_evidence: list
    kg_evidence: Optional[KGEvidence]
    ml_prediction: Optional[PredictionResult]
    business_rules_triggered: list
    doc_confidence: float
    kg_confidence: float
    ml_confidence: float
    rules_confidence: float
    overall_confidence: float

    DOC_WEIGHT   = 0.42
    KG_WEIGHT    = 0.27
    ML_WEIGHT    = 0.22
    RULES_WEIGHT = 0.09

    def confidence_breakdown(self) -> dict:
        return {
            "overall":           round(self.overall_confidence * 100, 1),
            "document_evidence": round(self.doc_confidence * 100, 1),
            "knowledge_graph":   round(self.kg_confidence * 100, 1),
            "ml_prediction":     round(self.ml_confidence * 100, 1),
            "business_rules":    round(self.rules_confidence * 100, 1),
        }


# ─── Intent & Entity Extractor ────────────────────────────────────────────────

EQUIPMENT_RE = re.compile(r'\b([A-Z]{1,4}[-\s]?\d{2,4}[A-Z]?)\b')
SYMPTOM_KEYWORDS = {
    "vibration":   ["vibrat", "shak", "tremb", "oscillat"],
    "temperature": ["hot", "heat", "temp", "overheating", "burn"],
    "pressure":    ["pressure", "psi", "bar", "drop", "surge"],
    "leakage":     ["leak", "seal", "drip", "flow loss"],
    "noise":       ["noise", "sound", "rattle", "knock", "squeal"],
    "cavitation":  ["cavitat", "bubble", "suction", "starv"],
    "lubrication": ["lubricat", "oil", "grease", "dry"],
    "alignment":   ["align", "balance", "imbalance", "misalign"],
}
INTENT_PATTERNS = {
    "diagnose":   ["why", "what", "diagnos", "problem", "issue", "fault",
                   "fail", "high", "low", "increase", "decrease"],
    "predict":    ["predict", "when", "rul", "remaining", "life", "soon",
                   "forecast", "probability"],
    "procedure":  ["how to", "procedure", "steps", "sop", "guide",
                   "instruction", "replace", "fix", "repair"],
    "compliance": ["complian", "standard", "oisd", "factory act",
                   "regulation", "audit", "certif"],
    "history":    ["history", "past", "previous", "last time", "before",
                   "record", "log"],
}

def extract_intent(query: str) -> dict:
    q = query.lower()
    eq_matches = EQUIPMENT_RE.findall(query.upper())
    equipment_id = eq_matches[0] if eq_matches else None
    detected_symptoms = [s for s, kws in SYMPTOM_KEYWORDS.items()
                         if any(kw in q for kw in kws)]
    intent_scores = {i: sum(1 for kw in kws if kw in q)
                     for i, kws in INTENT_PATTERNS.items()}
    primary_intent = max(intent_scores, key=intent_scores.get)
    if intent_scores[primary_intent] == 0:
        primary_intent = "diagnose"
    return {
        "equipment_id":     equipment_id,
        "symptoms":         detected_symptoms,
        "primary_intent":   primary_intent,
        "needs_prediction": primary_intent == "predict" or bool(detected_symptoms),
        "needs_procedure":  primary_intent == "procedure",
        "needs_compliance": primary_intent == "compliance",
    }


# ─── Business Rules ───────────────────────────────────────────────────────────

BUSINESS_RULES = [
    {"id": "BR-001", "name": "Critical Vibration",
     "condition": lambda s: s.get("vibration_mm_s", 0) > 7.1,
     "message": "Vibration exceeds ISO 10816 Zone C (7.1 mm/s). Immediate inspection required.",
     "severity": "CRITICAL"},
    {"id": "BR-002", "name": "High Temperature",
     "condition": lambda s: s.get("temperature_c", 0) > 85,
     "message": "Bearing temperature exceeds 85 C. Check lubrication and cooling.",
     "severity": "HIGH"},
    {"id": "BR-003", "name": "Lubrication Overdue",
     "condition": lambda s: s.get("lubrication_hours_since", 0) > 500,
     "message": "Lubrication interval exceeded 500 hours. Re-lubrication required per OEM.",
     "severity": "HIGH"},
    {"id": "BR-004", "name": "Low Pressure",
     "condition": lambda s: s.get("pressure_bar", 999) < 2.0,
     "message": "Discharge pressure below 2.0 bar. Check for seal failure or blockage.",
     "severity": "MEDIUM"},
    {"id": "BR-005", "name": "Low Flow Rate",
     "condition": lambda s: s.get("flow_rate_m3h", 999) < 60,
     "message": "Flow rate below 60 m3/h (nominal 85). Possible cavitation or wear.",
     "severity": "MEDIUM"},
]

def evaluate_rules(sensor_data: dict) -> list:
    triggered = []
    for rule in BUSINESS_RULES:
        try:
            if rule["condition"](sensor_data):
                triggered.append(f"[{rule['id']} - {rule['severity']}] {rule['message']}")
        except Exception:
            pass
    return triggered


# ─── Vector Store ─────────────────────────────────────────────────────────────

class VectorStore:
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="kaizen_chunks",
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"VectorStore ready — {self.collection.count()} chunks indexed")

    def add_chunks(self, chunks: list):
        if not chunks:
            return
        ids, docs, metas = [], [], []
        for chunk in chunks:
            ids.append(chunk.chunk_id)
            docs.append(chunk.content[:2000])
            metas.append({
                "doc_id":      chunk.doc_id,
                "source_file": chunk.source_file,
                "doc_type":    chunk.doc_type,
                "section":     str(chunk.metadata.get("section", "")),
                "heading":     str(chunk.metadata.get("heading", "")),
                "page":        str(chunk.metadata.get("page", "")),
                "trust_score": str(chunk.metadata.get("doc_trust_score", 1.0)),
                "ocr":         str(chunk.metadata.get("ocr", False)),
            })
        for i in range(0, len(ids), 100):
            self.collection.upsert(
                ids=ids[i:i+100],
                documents=docs[i:i+100],
                metadatas=metas[i:i+100],
            )
        logger.info(f"Indexed {len(ids)} chunks. Total: {self.collection.count()}")

    def search(self, query: str, n_results: int = 5,
               doc_type_filter: str = None) -> list:
        where = {"doc_type": doc_type_filter} if doc_type_filter else None
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, max(1, self.collection.count())),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.warning(f"Vector search error: {e}")
            return []
        evidence = []
        for doc, meta, dist in zip(results["documents"][0],
                                    results["metadatas"][0],
                                    results["distances"][0]):
            relevance = max(0.0, 1.0 - dist)
            trust = float(meta.get("trust_score", 1.0))
            section = meta.get("heading") or meta.get("section") or f"Page {meta.get('page','?')}"
            evidence.append(DocumentEvidence(
                source_file=meta.get("source_file", "unknown"),
                section=section,
                content=doc,
                relevance_score=round(relevance, 3),
                trust_score=round(trust, 3),
                ocr=meta.get("ocr", "False") == "True",
                chunk_id=meta.get("doc_id", ""),
            ))
        return sorted(evidence, key=lambda e: e.weighted_confidence, reverse=True)

    def count(self) -> int:
        return self.collection.count()


# ─── Industrial Reasoning Engine ──────────────────────────────────────────────

class IndustrialReasoningEngine:

    SYSTEM_PROMPT = """You are Kaizen AI's Industrial Reasoning Engine — an expert industrial
maintenance intelligence system. You receive structured evidence from three independent sources:
1. Document Evidence (OEM manuals, maintenance logs, inspection reports, SOPs)
2. Knowledge Graph (equipment relationships, component hierarchy, failure history)
3. ML Prediction (XGBoost model: failure probability, remaining useful life, root cause)

Synthesize this into a clear, actionable, cited recommendation.
Rules: Always cite sources. Never invent facts. Be direct and specific.
Structure: Root Cause -> Evidence -> Risk Assessment -> Recommended Actions -> Knowledge Gaps."""

    def __init__(self, vector_store: VectorStore,
                 knowledge_graph: KaizenKnowledgeGraph,
                 ml_model: PredictiveMaintenanceModel,
                 model_name: str = "gemini-1.5-flash"):
        self.vs  = vector_store
        self.kg  = knowledge_graph
        self.ml  = ml_model
        self.llm = genai.GenerativeModel(model_name)
        logger.info("Industrial Reasoning Engine initialized")

    def query(self, user_query: str,
              sensor_data: dict = None,
              n_doc_results: int = 4) -> dict:
        logger.info(f"Query: {user_query[:80]}")
        intent = extract_intent(user_query)
        equipment_id = intent["equipment_id"]

        # Parallel evidence retrieval
        doc_evidence = self._retrieve_documents(user_query, intent, n_doc_results)
        kg_evidence  = self._retrieve_kg_context(equipment_id)
        ml_result    = self._run_ml_prediction(equipment_id, sensor_data, intent)
        rules        = evaluate_rules(sensor_data or {})

        # Confidence scoring
        doc_conf   = self._score_doc_evidence(doc_evidence)
        kg_conf    = 1.0 if (kg_evidence and kg_evidence.related_nodes) else 0.5
        ml_conf    = ml_result.confidence if ml_result else 0.5
        rules_conf = 1.0 if rules else 0.8
        overall    = (doc_conf * FusedEvidence.DOC_WEIGHT +
                      kg_conf  * FusedEvidence.KG_WEIGHT  +
                      ml_conf  * FusedEvidence.ML_WEIGHT  +
                      rules_conf * FusedEvidence.RULES_WEIGHT)

        fused = FusedEvidence(
            query=user_query, equipment_id=equipment_id,
            document_evidence=doc_evidence, kg_evidence=kg_evidence,
            ml_prediction=ml_result, business_rules_triggered=rules,
            doc_confidence=doc_conf, kg_confidence=kg_conf,
            ml_confidence=ml_conf, rules_confidence=rules_conf,
            overall_confidence=round(overall, 3),
        )

        prompt = self._build_prompt(user_query, intent, fused, sensor_data)
        try:
            response = self.llm.generate_content(prompt)
            explanation = response.text
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            explanation = self._fallback_explanation(fused)

        return self._build_response(user_query, intent, fused, explanation)

    def _retrieve_documents(self, query, intent, n):
        if self.vs.count() == 0:
            return []
        results = self.vs.search(query, n_results=n)
        if intent["needs_compliance"]:
            comp = self.vs.search(query, n_results=2, doc_type_filter="compliance")
            seen = {e.chunk_id for e in results}
            for e in comp:
                if e.chunk_id not in seen:
                    results.append(e)
        return results[:6]

    def _retrieve_kg_context(self, equipment_id):
        if not equipment_id:
            return None
        ctx = self.kg.get_equipment_context(equipment_id, depth=2)
        if not ctx.get("found"):
            return None
        return KGEvidence(
            equipment_id=equipment_id,
            related_nodes=ctx.get("nodes", []),
            relationships=ctx.get("edges", []),
            failure_history=ctx.get("failure_history", []),
            maintenance_history=self.kg.get_maintenance_history(equipment_id),
            component_chain=self.kg.get_component_chain(equipment_id),
        )

    def _run_ml_prediction(self, equipment_id, sensor_data, intent):
        if not sensor_data or not equipment_id or not self.ml.is_trained:
            return None
        try:
            return self.ml.predict(equipment_id, sensor_data)
        except Exception as e:
            logger.warning(f"ML prediction failed: {e}")
            return None

    def _score_doc_evidence(self, evidence):
        if not evidence:
            return 0.4
        return round(sum(e.weighted_confidence for e in evidence) / len(evidence), 3)

    def _build_prompt(self, query, intent, fused, sensor_data):
        parts = [
            f"USER QUERY: {query}",
            f"EQUIPMENT: {fused.equipment_id or 'Not specified'}",
            f"INTENT: {intent['primary_intent']} | SYMPTOMS: {', '.join(intent['symptoms']) or 'None'}",
            "",
        ]
        if sensor_data:
            parts.append("SENSOR READINGS:")
            parts += [f"  {k}: {v}" for k, v in sensor_data.items()]
            parts.append("")
        if fused.document_evidence:
            parts.append(f"DOCUMENT EVIDENCE ({len(fused.document_evidence)} sources):")
            for i, ev in enumerate(fused.document_evidence, 1):
                parts.append(f"\n[Doc {i}] {ev.source_file} | {ev.section} "
                             f"(relevance: {ev.relevance_score:.0%}, trust: {ev.trust_score:.0%})\n"
                             f"{ev.content[:500]}")
            parts.append("")
        if fused.kg_evidence:
            parts.append("KNOWLEDGE GRAPH:")
            parts.append(fused.kg_evidence.to_context_str())
            parts.append("")
        if fused.ml_prediction:
            ml = fused.ml_prediction
            parts += [
                "ML PREDICTION (XGBoost):",
                f"  Failure Probability: {ml.failure_probability:.0%}",
                f"  Predicted Failure:   {ml.predicted_failure_type}",
                f"  RUL:                 {ml.rul_days:.0f} days",
                f"  Health Score:        {ml.health_score:.0f}/100",
                f"  Risk Level:          {ml.risk_level}",
                "  Top Factors: " + ", ".join(
                    f"{k} ({v:.0f}%)" for k, v in list(ml.feature_contributions.items())[:3]),
                "",
            ]
        if fused.business_rules_triggered:
            parts.append("BUSINESS RULES TRIGGERED:")
            parts += [f"  * {r}" for r in fused.business_rules_triggered]
            parts.append("")
        cb = fused.confidence_breakdown()
        parts += [
            "CONFIDENCE: "
            f"Overall {cb['overall']}% | "
            f"Docs {cb['document_evidence']}% | "
            f"KG {cb['knowledge_graph']}% | "
            f"ML {cb['ml_prediction']}% | "
            f"Rules {cb['business_rules']}%",
            "",
            "Provide: 1) Root Cause Analysis  2) Risk Assessment  "
            "3) Ordered Action Items with timeframes  4) Source citations  "
            "5) Knowledge gaps. Be specific and actionable.",
        ]
        return self.SYSTEM_PROMPT + "\n\n" + "\n".join(parts)

    def _fallback_explanation(self, fused):
        lines = ["**Evidence-based analysis:**\n"]
        if fused.ml_prediction:
            ml = fused.ml_prediction
            lines.append(f"**ML:** {ml.recommendation}")
        if fused.business_rules_triggered:
            lines.append("\n**Rules triggered:**")
            lines += [f"  * {r}" for r in fused.business_rules_triggered]
        if fused.document_evidence:
            lines.append("\n**Relevant documents:**")
            for ev in fused.document_evidence[:3]:
                lines.append(f"  * {ev.source_file} | {ev.section}")
        return "\n".join(lines)

    def _build_response(self, query, intent, fused, explanation):
        cb = fused.confidence_breakdown()
        return {
            "query":        query,
            "equipment_id": fused.equipment_id,
            "intent":       intent["primary_intent"],
            "symptoms":     intent["symptoms"],
            "timestamp":    datetime.utcnow().isoformat(),
            "explanation":  explanation,
            "citations": [
                {"source": ev.source_file, "section": ev.section,
                 "relevance": f"{ev.relevance_score:.0%}",
                 "trust": f"{ev.trust_score:.0%}",
                 "ocr": ev.ocr, "excerpt": ev.content[:150] + "..."}
                for ev in fused.document_evidence
            ],
            "ml_summary": {
                "failure_probability": f"{fused.ml_prediction.failure_probability:.0%}",
                "rul_days":            fused.ml_prediction.rul_days,
                "risk_level":          fused.ml_prediction.risk_level,
                "health_score":        fused.ml_prediction.health_score,
                "predicted_failure":   fused.ml_prediction.predicted_failure_type,
                "feature_contributions": fused.ml_prediction.feature_contributions,
                "recommendation":      fused.ml_prediction.recommendation,
                "urgency_hours":       fused.ml_prediction.urgency_hours,
            } if fused.ml_prediction else None,
            "kg_summary": {
                "equipment_id":       fused.equipment_id,
                "component_count":    len(fused.kg_evidence.component_chain),
                "failure_events":     len(fused.kg_evidence.failure_history),
                "maintenance_count":  len(fused.kg_evidence.maintenance_history),
                "components":         fused.kg_evidence.component_chain[:5],
                "recent_failures":    fused.kg_evidence.failure_history[:3],
                "recent_maintenance": fused.kg_evidence.maintenance_history[:3],
            } if fused.kg_evidence else None,
            "rules_triggered": fused.business_rules_triggered,
            "confidence": {
                **cb,
                "interpretation": (
                    "HIGH" if cb["overall"] >= 80
                    else "MEDIUM" if cb["overall"] >= 60
                    else "LOW"
                ),
            },
            "evidence_stats": {
                "documents_searched":  self.vs.count(),
                "documents_retrieved": len(fused.document_evidence),
                "kg_nodes_traversed":  len(fused.kg_evidence.related_nodes) if fused.kg_evidence else 0,
                "rules_evaluated":     len(BUSINESS_RULES),
                "rules_triggered":     len(fused.business_rules_triggered),
            }
        }


_engine_instance: Optional[IndustrialReasoningEngine] = None

def get_engine(vector_store=None, kg=None, ml=None) -> IndustrialReasoningEngine:
    global _engine_instance
    if _engine_instance is None:
        if not all([vector_store, kg, ml]):
            raise RuntimeError("First call must provide vector_store, kg, and ml.")
        _engine_instance = IndustrialReasoningEngine(vector_store, kg, ml)
    return _engine_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vs = VectorStore(persist_dir="./chroma_db_test")
    kg = KaizenKnowledgeGraph()
    ml = PredictiveMaintenanceModel()

    kg.add_equipment("P-104", "Centrifugal Pump", "pump", location="Unit-3")
    kg.add_failure_event("P-104", "bearing_degradation", "HIGH",
                          root_cause="Lubrication overdue", source_doc="incident_019")
    kg.add_maintenance_record("P-104", "Bearing replacement",
                               technician="Ravi Kumar", parts=["SKF-6205"], date="2025-03-12")

    print("Training ML...")
    ml.train(n_assets=100)

    engine = IndustrialReasoningEngine(vs, kg, ml)
    result = engine.query(
        "Pump P-104 vibration has increased to 7.8 mm/s. What is causing this?",
        sensor_data={
            "vibration_mm_s": 7.8, "temperature_c": 82.0,
            "pressure_bar": 3.9, "rpm": 1475,
            "flow_rate_m3h": 79.0, "lubrication_hours_since": 520,
            "runtime_hours": 1650,
        }
    )

    print(f"\nConfidence: {result['confidence']['overall']}% ({result['confidence']['interpretation']})")
    print(f"Rules triggered: {len(result['rules_triggered'])}")
    if result['ml_summary']:
        print(f"ML: {result['ml_summary']['risk_level']} | "
              f"Prob: {result['ml_summary']['failure_probability']} | "
              f"RUL: {result['ml_summary']['rul_days']} days")
    print(f"\n{result['explanation']}")
