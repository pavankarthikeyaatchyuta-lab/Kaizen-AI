"""
Kaizen AI — Knowledge Graph Builder
Transforms IngestionResult entities into a connected industrial ontology.

Nodes:  Equipment, Component, Failure, Maintenance, Technician,
        Document, Standard, Measurement, Procedure
Edges:  HAS_COMPONENT, MONITORED_BY, HAS_MAINTENANCE, HAS_FAILURE,
        PERFORMED_BY, DOCUMENTED_IN, REFERENCES, CAUSED_BY,
        RESOLVED_BY, MATCHES, COMPLIES_WITH, GENERATED
"""

import json
import hashlib
import logging
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict

import networkx as nx
from pyvis.network import Network

logger = logging.getLogger(__name__)


# ─── Node & Edge Type Definitions ─────────────────────────────────────────────

NODE_STYLES = {
    "equipment":    {"color": "#E74C3C", "size": 35, "shape": "dot"},
    "component":    {"color": "#E67E22", "size": 25, "shape": "dot"},
    "failure":      {"color": "#C0392B", "size": 22, "shape": "triangle"},
    "maintenance":  {"color": "#27AE60", "size": 22, "shape": "square"},
    "technician":   {"color": "#2980B9", "size": 20, "shape": "dot"},
    "document":     {"color": "#8E44AD", "size": 20, "shape": "diamond"},
    "standard":     {"color": "#16A085", "size": 18, "shape": "dot"},
    "measurement":  {"color": "#F39C12", "size": 15, "shape": "dot"},
    "prediction":   {"color": "#1ABC9C", "size": 28, "shape": "star"},
    "work_order":   {"color": "#3498DB", "size": 22, "shape": "square"},
}

EDGE_COLORS = {
    "HAS_COMPONENT":   "#E67E22",
    "HAS_FAILURE":     "#E74C3C",
    "HAS_MAINTENANCE": "#27AE60",
    "PERFORMED_BY":    "#2980B9",
    "DOCUMENTED_IN":   "#8E44AD",
    "CAUSED_BY":       "#C0392B",
    "RESOLVED_BY":     "#27AE60",
    "MATCHES":         "#F39C12",
    "COMPLIES_WITH":   "#16A085",
    "REFERENCES":      "#95A5A6",
    "HAS_PREDICTION":  "#1ABC9C",
    "GENERATED":       "#3498DB",
    "MONITORED_BY":    "#F39C12",
}


# ─── Node ID helpers ──────────────────────────────────────────────────────────

def _nid(node_type: str, value: str) -> str:
    """Stable node ID from type + value."""
    return f"{node_type}::{value.strip().upper()}"


# ─── Knowledge Graph ──────────────────────────────────────────────────────────

class KaizenKnowledgeGraph:
    """
    Industrial knowledge graph built from ingested documents.
    Nodes are typed entities; edges are semantic relationships.
    Supports graph traversal for the Industrial Reasoning Engine.
    """

    def __init__(self):
        self.G = nx.DiGraph()
        self._equipment_registry: dict[str, dict] = {}   # equipment_id → attributes
        self._failure_history: list[dict] = []
        self._doc_registry: dict[str, dict] = {}

    # ── Node Management ───────────────────────────────────────────────────────

    def add_node(self, node_type: str, value: str, **attrs) -> str:
        nid = _nid(node_type, value)
        if not self.G.has_node(nid):
            style = NODE_STYLES.get(node_type, {"color": "#95A5A6", "size": 18, "shape": "dot"})
            self.G.add_node(nid,
                label=value,
                node_type=node_type,
                created_at=datetime.utcnow().isoformat(),
                **style,
                **attrs)
        else:
            # Update existing node with new attributes
            self.G.nodes[nid].update(attrs)
        return nid

    def add_edge(self, src_id: str, tgt_id: str, relation: str, **attrs):
        if not self.G.has_edge(src_id, tgt_id):
            self.G.add_edge(src_id, tgt_id,
                relation=relation,
                color=EDGE_COLORS.get(relation, "#95A5A6"),
                title=relation,
                **attrs)

    # ── Build from IngestionResult ────────────────────────────────────────────

    def ingest_result(self, result) -> int:
        """
        Add all entities from an IngestionResult into the graph.
        Returns count of new nodes added.
        """
        if not result.success:
            return 0

        before = self.G.number_of_nodes()

        # Document node
        doc_nid = self.add_node("document",
            result.filename,
            doc_id=result.doc_id,
            doc_type=result.doc_type,
            trust_score=result.doc_meta.trust_score if result.doc_meta else 1.0,
            revision=result.doc_meta.revision if result.doc_meta else None,
            title=f"📄 {result.filename}\nType: {result.doc_type}\n"
                  f"Trust: {result.doc_meta.trust_score:.0%}" if result.doc_meta else result.filename,
        )
        self._doc_registry[result.doc_id] = {"nid": doc_nid, "filename": result.filename}

        # Compliance standard links
        if result.doc_type == "compliance":
            std_nid = self.add_node("standard", f"Compliance: {result.filename}")
            self.add_edge(doc_nid, std_nid, "REFERENCES")

        # Equipment from doc metadata
        equipment_nid = None
        if result.doc_meta and result.doc_meta.equipment_id:
            eid = result.doc_meta.equipment_id
            equipment_nid = self.add_node("equipment", eid,
                equipment_id=eid,
                title=f"⚙ Equipment: {eid}")
            self.add_edge(equipment_nid, doc_nid, "DOCUMENTED_IN")
            self._equipment_registry[eid] = {"nid": equipment_nid}

        # Process extracted entities
        seen_pairs = set()  # avoid duplicate edges
        for entity in result.entities:
            self._process_entity(entity, doc_nid, equipment_nid, seen_pairs)

        added = self.G.number_of_nodes() - before
        logger.info(f"KG: +{added} nodes from {result.filename} "
                    f"(total: {self.G.number_of_nodes()} nodes, "
                    f"{self.G.number_of_edges()} edges)")
        return added

    def _process_entity(self, entity, doc_nid: str,
                         equipment_nid: Optional[str], seen: set):
        val = entity.value.strip()
        if not val or len(val) < 2:
            return

        etype = entity.entity_type

        if etype == "equipment":
            nid = self.add_node("equipment", val,
                title=f"⚙ {val}\nSource: {entity.context[:80]}")
            self.add_edge(nid, doc_nid, "DOCUMENTED_IN")
            if equipment_nid and nid != equipment_nid:
                key = (nid, equipment_nid, "REFERENCES")
                if key not in seen:
                    seen.add(key)

        elif etype == "component":
            nid = self.add_node("component", val,
                title=f"🔩 Component: {val}\n{entity.context[:80]}")
            if equipment_nid:
                key = (equipment_nid, nid, "HAS_COMPONENT")
                if key not in seen:
                    seen.add(key)
                    self.add_edge(equipment_nid, nid, "HAS_COMPONENT",
                                  confidence=entity.confidence)

        elif etype == "failure_type":
            nid = self.add_node("failure", val,
                title=f"⚠ Failure: {val}\n{entity.context[:80]}")
            if equipment_nid:
                key = (equipment_nid, nid, "HAS_FAILURE")
                if key not in seen:
                    seen.add(key)
                    self.add_edge(equipment_nid, nid, "HAS_FAILURE",
                                  confidence=entity.confidence)
                    self._failure_history.append({
                        "equipment": equipment_nid,
                        "failure": val,
                        "source_doc": doc_nid,
                        "confidence": entity.confidence,
                        "context": entity.context[:200],
                    })

        elif etype == "standard":
            nid = self.add_node("standard", val,
                title=f"📋 Standard: {val}")
            self.add_edge(doc_nid, nid, "COMPLIES_WITH")

        elif etype == "technician":
            nid = self.add_node("technician", val,
                title=f"👷 Technician: {val}")
            # Will be linked to maintenance records when added
            self.add_edge(nid, doc_nid, "REFERENCED_IN")

        elif etype == "maintenance_action":
            nid = self.add_node("maintenance", val,
                title=f"🔧 Maintenance: {val}\n{entity.context[:80]}")
            if equipment_nid:
                key = (equipment_nid, nid, "HAS_MAINTENANCE")
                if key not in seen:
                    seen.add(key)
                    self.add_edge(equipment_nid, nid, "HAS_MAINTENANCE")

        elif etype == "measurement":
            nid = self.add_node("measurement", val,
                title=f"📊 {val}\n{entity.context[:80]}")
            if equipment_nid:
                key = (equipment_nid, nid, "MONITORED_BY")
                if key not in seen:
                    seen.add(key)
                    self.add_edge(equipment_nid, nid, "MONITORED_BY")

    # ── Manual Node Addition (for runtime events) ─────────────────────────────

    def add_equipment(self, equipment_id: str, name: str,
                       equipment_type: str = "unknown", **attrs) -> str:
        nid = self.add_node("equipment", equipment_id,
            name=name, equipment_type=equipment_type,
            title=f"⚙ {name} ({equipment_id})\nType: {equipment_type}",
            **attrs)
        self._equipment_registry[equipment_id] = {"nid": nid, **attrs}
        return nid

    def add_failure_event(self, equipment_id: str, failure_type: str,
                           severity: str, root_cause: str = "",
                           source_doc: str = "") -> str:
        eq_nid = self._get_or_create_equipment(equipment_id)
        fail_label = f"{failure_type} [{severity}]"
        fail_nid = self.add_node("failure", fail_label,
            failure_type=failure_type,
            severity=severity,
            root_cause=root_cause,
            timestamp=datetime.utcnow().isoformat(),
            title=f"⚠ {failure_type}\nSeverity: {severity}\nCause: {root_cause}")
        self.add_edge(eq_nid, fail_nid, "HAS_FAILURE", severity=severity)
        self._failure_history.append({
            "equipment": equipment_id,
            "failure": failure_type,
            "severity": severity,
            "root_cause": root_cause,
            "source_doc": source_doc,
        })
        return fail_nid

    def add_maintenance_record(self, equipment_id: str, action: str,
                                technician: str = "", parts: list = None,
                                date: str = "") -> str:
        eq_nid = self._get_or_create_equipment(equipment_id)
        maint_label = f"{action} @ {date or 'unknown date'}"
        maint_nid = self.add_node("maintenance", maint_label,
            action=action, technician=technician,
            parts=parts or [], date=date,
            title=f"🔧 {action}\nTechnician: {technician}\nDate: {date}")
        self.add_edge(eq_nid, maint_nid, "HAS_MAINTENANCE", date=date)

        if technician:
            tech_nid = self.add_node("technician", technician,
                title=f"👷 {technician}")
            self.add_edge(tech_nid, maint_nid, "PERFORMED_BY")

        return maint_nid

    def add_prediction(self, equipment_id: str, failure_prob: float,
                        rul_days: float, risk_level: str,
                        top_causes: list) -> str:
        eq_nid = self._get_or_create_equipment(equipment_id)
        pred_label = f"Prediction: {risk_level} ({failure_prob:.0%})"
        pred_nid = self.add_node("prediction", pred_label,
            failure_prob=failure_prob,
            rul_days=rul_days,
            risk_level=risk_level,
            top_causes=top_causes,
            timestamp=datetime.utcnow().isoformat(),
            title=f"🤖 ML Prediction\nFailure Prob: {failure_prob:.0%}\n"
                  f"RUL: {rul_days:.0f} days\nRisk: {risk_level}")
        self.add_edge(eq_nid, pred_nid, "HAS_PREDICTION")
        return pred_nid

    def _get_or_create_equipment(self, equipment_id: str) -> str:
        if equipment_id in self._equipment_registry:
            return self._equipment_registry[equipment_id]["nid"]
        nid = self.add_node("equipment", equipment_id,
            title=f"⚙ {equipment_id}")
        self._equipment_registry[equipment_id] = {"nid": nid}
        return nid

    # ── Graph Traversal (for Reasoning Engine) ────────────────────────────────

    def get_equipment_context(self, equipment_id: str, depth: int = 2) -> dict:
        """
        Return all nodes within `depth` hops of an equipment node.
        Used by the Industrial Reasoning Engine to build KG evidence.
        """
        eq_nid = _nid("equipment", equipment_id)
        if not self.G.has_node(eq_nid):
            # Try partial match
            candidates = [n for n in self.G.nodes
                          if equipment_id.upper() in n.upper()]
            if not candidates:
                return {"found": False, "equipment_id": equipment_id, "nodes": []}
            eq_nid = candidates[0]

        # BFS up to depth hops
        subgraph_nodes = {eq_nid}
        frontier = {eq_nid}
        for _ in range(depth):
            next_frontier = set()
            for node in frontier:
                next_frontier.update(self.G.successors(node))
                next_frontier.update(self.G.predecessors(node))
            subgraph_nodes.update(next_frontier)
            frontier = next_frontier

        context_nodes = []
        for nid in subgraph_nodes:
            attrs = dict(self.G.nodes[nid])
            context_nodes.append({
                "node_id": nid,
                "node_type": attrs.get("node_type"),
                "label": attrs.get("label"),
                "attributes": {k: v for k, v in attrs.items()
                               if k not in ("color", "size", "shape",
                                            "created_at", "title")},
            })

        # Get edges within subgraph
        context_edges = []
        for src, tgt, data in self.G.edges(data=True):
            if src in subgraph_nodes and tgt in subgraph_nodes:
                context_edges.append({
                    "from": self.G.nodes[src].get("label"),
                    "relation": data.get("relation"),
                    "to": self.G.nodes[tgt].get("label"),
                })

        return {
            "found": True,
            "equipment_id": equipment_id,
            "nodes": context_nodes,
            "edges": context_edges,
            "failure_history": [
                f for f in self._failure_history
                if equipment_id.upper() in str(f.get("equipment", "")).upper()
            ],
        }

    def find_similar_failures(self, failure_type: str, limit: int = 5) -> list:
        """Find historical failures matching the given type."""
        results = []
        for record in self._failure_history:
            if failure_type.lower() in str(record.get("failure", "")).lower():
                results.append(record)
        return results[:limit]

    def get_component_chain(self, equipment_id: str) -> list:
        """Return all components connected to equipment, with their relationships."""
        eq_nid = _nid("equipment", equipment_id)
        if not self.G.has_node(eq_nid):
            return []
        return [
            {
                "component": self.G.nodes[tgt].get("label"),
                "relation": data.get("relation"),
            }
            for _, tgt, data in self.G.out_edges(eq_nid, data=True)
            if self.G.nodes[tgt].get("node_type") == "component"
        ]

    def get_maintenance_history(self, equipment_id: str) -> list:
        """Return all maintenance records linked to equipment."""
        eq_nid = _nid("equipment", equipment_id)
        if not self.G.has_node(eq_nid):
            return []
        records = []
        for _, tgt, data in self.G.out_edges(eq_nid, data=True):
            if self.G.nodes[tgt].get("node_type") == "maintenance":
                attrs = dict(self.G.nodes[tgt])
                records.append({
                    "action": attrs.get("label"),
                    "date": attrs.get("date", "unknown"),
                    "technician": attrs.get("technician", "unknown"),
                    "parts": attrs.get("parts", []),
                })
        return sorted(records, key=lambda x: x.get("date", ""), reverse=True)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        node_counts = {}
        for _, attrs in self.G.nodes(data=True):
            nt = attrs.get("node_type", "unknown")
            node_counts[nt] = node_counts.get(nt, 0) + 1
        return {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "node_types": node_counts,
            "equipment_count": len(self._equipment_registry),
            "failure_events": len(self._failure_history),
            "documents_ingested": len(self._doc_registry),
        }

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_json(self) -> dict:
        return {
            "nodes": [
                {"id": nid, **{k: v for k, v in attrs.items()
                               if isinstance(v, (str, int, float, bool, list, type(None)))}}
                for nid, attrs in self.G.nodes(data=True)
            ],
            "edges": [
                {"source": src, "target": tgt, **data}
                for src, tgt, data in self.G.edges(data=True)
            ],
            "stats": self.stats(),
        }

    def save_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_json(), f, indent=2, default=str)
        logger.info(f"KG saved to {path}")

    @classmethod
    def load_json(cls, path: str) -> "KaizenKnowledgeGraph":
        kg = cls()
        with open(path) as f:
            data = json.load(f)
        for node in data["nodes"]:
            nid = node.pop("id")
            kg.G.add_node(nid, **node)
        for edge in data["edges"]:
            src = edge.pop("source")
            tgt = edge.pop("target")
            kg.G.add_edge(src, tgt, **edge)
        logger.info(f"KG loaded: {kg.G.number_of_nodes()} nodes, "
                    f"{kg.G.number_of_edges()} edges")
        return kg

    # ── Visualization ─────────────────────────────────────────────────────────

    def visualize(self, output_path: str = "kaizen_kg.html",
                  focus_equipment: str = None,
                  height: str = "700px") -> str:
        """
        Export interactive Pyvis HTML visualization.
        If focus_equipment given, shows only its subgraph.
        """
        if focus_equipment:
            context = self.get_equipment_context(focus_equipment, depth=2)
            node_ids = {n["node_id"] for n in context["nodes"]}
            subgraph = self.G.subgraph(node_ids)
            G_vis = subgraph
        else:
            G_vis = self.G

        net = Network(height=height, width="100%", bgcolor="#1a1a2e",
                      font_color="#ffffff", directed=True)
        net.set_options("""
        {
          "nodes": {
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "font": {"size": 13, "face": "Inter, Arial"}
          },
          "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.8}},
            "font": {"size": 10, "color": "#aaaaaa"},
            "smooth": {"type": "dynamic"}
          },
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -60,
              "centralGravity": 0.005,
              "springLength": 120,
              "springConstant": 0.08
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 150}
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100
          }
        }
        """)

        for nid, attrs in G_vis.nodes(data=True):
            net.add_node(
                nid,
                label=attrs.get("label", nid.split("::")[-1]),
                color=attrs.get("color", "#95A5A6"),
                size=attrs.get("size", 18),
                shape=attrs.get("shape", "dot"),
                title=attrs.get("title", nid),
            )

        for src, tgt, data in G_vis.edges(data=True):
            net.add_edge(
                src, tgt,
                label=data.get("relation", ""),
                color=data.get("color", "#95A5A6"),
                title=data.get("relation", ""),
            )

        net.save_graph(output_path)
        logger.info(f"KG visualization saved: {output_path} "
                    f"({G_vis.number_of_nodes()} nodes, "
                    f"{G_vis.number_of_edges()} edges)")
        return output_path


# ─── Quick Demo ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from ingestion import ingest_folder, ingest_document

    kg = KaizenKnowledgeGraph()

    # Seed with some manual data to demo without real docs
    kg.add_equipment("P-104", "Centrifugal Pump", "pump",
                     location="Unit-3", criticality="high")
    kg.add_equipment("M-201", "Drive Motor", "motor",
                     location="Unit-3", criticality="high")

    kg.add_node("component", "Bearing B-2",
                title="🔩 Bearing B-2\nType: Rolling element")
    kg.add_node("component", "Mechanical Seal S-1",
                title="🔩 Mechanical Seal S-1")

    eq_nid  = _nid("equipment", "P-104")
    brg_nid = _nid("component", "Bearing B-2")
    seal_nid = _nid("component", "Mechanical Seal S-1")
    mot_nid = _nid("equipment", "M-201")

    kg.add_edge(eq_nid, brg_nid, "HAS_COMPONENT")
    kg.add_edge(eq_nid, seal_nid, "HAS_COMPONENT")
    kg.add_edge(mot_nid, eq_nid, "DRIVES")

    kg.add_failure_event("P-104", "vibration", "HIGH",
                          root_cause="Bearing wear", source_doc="incident_001")
    kg.add_maintenance_record("P-104", "Bearing replacement",
                               technician="Ravi Kumar",
                               parts=["Bearing SKF-6205"],
                               date="2025-03-12")
    kg.add_prediction("P-104",
                       failure_prob=0.87,
                       rul_days=14,
                       risk_level="CRITICAL",
                       top_causes=["Bearing degradation", "Lubrication overdue"])

    print(json.dumps(kg.stats(), indent=2))

    # Context for reasoning engine
    ctx = kg.get_equipment_context("P-104")
    print(f"\nContext nodes for P-104: {len(ctx['nodes'])}")
    print(f"Failure history: {ctx['failure_history']}")

    # Export visualization
    kg.visualize("kaizen_kg_demo.html", focus_equipment="P-104")
    print("\n✓ Open kaizen_kg_demo.html in browser to see the graph")
