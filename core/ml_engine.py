"""
Kaizen AI — Predictive Maintenance Engine (Serverless Mock)
Rule-based heuristic engine for Vercel deployment without heavy ML dependencies.
"""
import logging
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

@dataclass
class PredictionResult:
    equipment_id: str
    failure_probability: float
    rul_days: float
    risk_level: str
    predicted_failure_type: str
    health_score: float
    feature_contributions: dict
    confidence: float
    recommendation: str
    urgency_hours: Optional[float] = None

class PredictiveMaintenanceModel:
    def __init__(self):
        self.is_trained = True

    def train(self, dataset=None, n_assets=200):
        return {"rul_mae_days": 2.1, "rul_r2": 0.89, "classifier_macro_f1": 0.92, "training_samples": 1200}

    def save(self, directory=None):
        pass

    def load(self, directory=None):
        pass

    def predict(self, equipment_id: str, sensor_reading: dict) -> PredictionResult:
        # Heuristic rules
        vibration = sensor_reading.get("vibration_mm_s", 0.0)
        temperature = sensor_reading.get("temperature_c", 0.0)
        pressure = sensor_reading.get("pressure_bar", 4.0)

        risk_level = "LOW"
        failure_prob = 0.1
        rul_days = 120.0
        failure_name = "normal_wear"
        urgency_hours = None
        contributions = {}

        if vibration > 7.0 or temperature > 90.0:
            risk_level = "CRITICAL"
            failure_prob = 0.88
            rul_days = 2.0
            urgency_hours = 24.0
            if vibration > 7.0:
                failure_name = "bearing_degradation"
                contributions = {"vibration_mm_s": 65.0, "temperature_c": 20.0, "rpm": 15.0}
            else:
                failure_name = "lubrication_failure"
                contributions = {"temperature_c": 70.0, "vibration_mm_s": 20.0, "rpm": 10.0}
        elif vibration > 4.5 or temperature > 75.0:
            risk_level = "HIGH"
            failure_prob = 0.65
            rul_days = 14.0
            urgency_hours = 72.0
            failure_name = "seal_failure"
            contributions = {"vibration_mm_s": 45.0, "temperature_c": 35.0, "pressure_bar": 20.0}
        elif pressure < 2.5:
            risk_level = "MEDIUM"
            failure_prob = 0.45
            rul_days = 30.0
            urgency_hours = 168.0
            failure_name = "cavitation"
            contributions = {"pressure_bar": 55.0, "flow_rate_m3h": 35.0, "vibration_mm_s": 10.0}

        health_score = max(0.0, min(100.0, rul_days / 1.25))
        
        recommendation = self._build_recommendation(risk_level, failure_name, rul_days, urgency_hours, contributions)

        return PredictionResult(
            equipment_id=equipment_id,
            failure_probability=failure_prob,
            rul_days=rul_days,
            risk_level=risk_level,
            predicted_failure_type=failure_name,
            health_score=round(health_score, 1),
            feature_contributions=contributions,
            confidence=0.88,
            recommendation=recommendation,
            urgency_hours=urgency_hours,
        )

    def _build_recommendation(self, risk: str, failure: str, rul: float, urgency: Optional[float], contributions: dict) -> str:
        top_factor = max(contributions, key=contributions.get) if contributions else "sensor readings"
        top_factor_clean = top_factor.replace("_", " ")

        templates = {
            "CRITICAL": f"⚠ CRITICAL: Schedule immediate maintenance for {failure.replace('_',' ')}. Estimated {rul:.0f} days to failure. Primary risk factor: {top_factor_clean}. Recommended action within {urgency:.0f} hours.",
            "HIGH": f"HIGH RISK: Plan {failure.replace('_',' ')} maintenance within {urgency:.0f} hours ({rul:.0f} days remaining). Monitor {top_factor_clean} closely.",
            "MEDIUM": f"MEDIUM RISK: Schedule {failure.replace('_',' ')} inspection within next {rul:.0f} days. Elevated {top_factor_clean} detected.",
            "LOW": f"LOW RISK: Continue normal monitoring. Next inspection due in {rul:.0f} days. Current {top_factor_clean} within acceptable range.",
        }
        return templates.get(risk, "Review sensor readings.")

def train_and_save(n_assets: int = 300) -> dict:
    return PredictiveMaintenanceModel().train()

def load_model() -> PredictiveMaintenanceModel:
    return PredictiveMaintenanceModel()
