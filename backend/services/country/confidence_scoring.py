import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class ConfidenceScoringEngine:
    """Engine for calculating and displaying confidence scores for country data."""
    
    SCORE_RANGES = {
        "high": {"min": 0.8, "color": "green", "label": "High Confidence"},
        "medium": {"min": 0.6, "color": "yellow", "label": "Medium Confidence"},
        "low": {"min": 0.0, "color": "red", "label": "Low Confidence"},
    }
    
    DATA_POINTS = [
        "name", "currencies", "capital", "latitude", "longitude",
        "languages", "gdp_per_capita_usd", "population", "internet_penetration_pct",
        "region", "flag_url", "phone_code"
    ]
    
    @staticmethod
    def calculate_confidence_score(
        rest_data: Optional[dict],
        wb_data: Optional[dict],
        cities: list,
        holidays: list = None,
    ) -> Dict[str, Any]:
        if not rest_data:
            return {
                "score": 0.0,
                "percentage": 0,
                "tier": "low",
                "color": "red",
                "label": "Low Confidence",
                "missing_fields": ConfidenceScoringEngine.DATA_POINTS,
                "details": []
            }
        
        score = 0.0
        total_checks = 10
        details = []
        missing_fields = []
        
        if rest_data.get("name"):
            score += 1
        else:
            missing_fields.append("name")
        details.append({"field": "name", "present": bool(rest_data.get("name"))})
        
        if rest_data.get("currencies"):
            score += 1
        else:
            missing_fields.append("currencies")
        details.append({"field": "currencies", "present": bool(rest_data.get("currencies"))})
        
        if rest_data.get("capital"):
            score += 1
        else:
            missing_fields.append("capital")
        details.append({"field": "capital", "present": bool(rest_data.get("capital"))})
        
        if rest_data.get("latitude") and rest_data.get("longitude"):
            score += 1
        else:
            missing_fields.extend(["latitude", "longitude"])
        details.append({"field": "coordinates", "present": bool(rest_data.get("latitude") and rest_data.get("longitude"))})
        
        if rest_data.get("languages"):
            score += 1
        else:
            missing_fields.append("languages")
        details.append({"field": "languages", "present": bool(rest_data.get("languages"))})
        
        if wb_data and wb_data.get("gdp_per_capita_usd"):
            score += 1
        else:
            missing_fields.append("gdp_per_capita_usd")
        details.append({"field": "gdp_data", "present": bool(wb_data and wb_data.get("gdp_per_capita_usd"))})
        
        if cities and len(cities) > 0:
            score += 1
        else:
            missing_fields.append("cities")
        details.append({"field": "cities", "present": bool(cities and len(cities) > 0)})
        
        if rest_data.get("region"):
            score += 1
        else:
            missing_fields.append("region")
        details.append({"field": "region", "present": bool(rest_data.get("region"))})
        
        if rest_data.get("flag_url"):
            score += 1
        else:
            missing_fields.append("flag_url")
        details.append({"field": "flag_url", "present": bool(rest_data.get("flag_url"))})
        
        if rest_data.get("phone_code"):
            score += 1
        else:
            missing_fields.append("phone_code")
        details.append({"field": "phone_code", "present": bool(rest_data.get("phone_code"))})
        
        percentage = round((score / total_checks) * 100, 1)
        tier = "high" if score >= 8 else "medium" if score >= 6 else "low"
        color = ConfidenceScoringEngine.SCORE_RANGES[tier]["color"]
        label = ConfidenceScoringEngine.SCORE_RANGES[tier]["label"]
        
        return {
            "score": round(score / total_checks, 4),
            "percentage": percentage,
            "tier": tier,
            "color": color,
            "label": label,
            "missing_fields": list(set(missing_fields)),
            "details": details
        }
    
    @staticmethod
    def get_score_badge(score: float) -> Dict[str, str]:
        """Get visual badge for score display."""
        tier = "high" if score >= 0.8 else "medium" if score >= 0.6 else "low"
        return {
            "text": f"{int(score * 100)}%",
            "tier": tier,
            "color": ConfidenceScoringEngine.SCORE_RANGES[tier]["color"],
            "label": ConfidenceScoringEngine.SCORE_RANGES[tier]["label"]
        }
    
    @staticmethod
    def get_recommendation(score: float, missing_fields: List[str]) -> str:
        """Get recommendation based on score."""
        if score >= 0.8:
            return "Data is complete and ready for production use"
        elif score >= 0.6:
            return f"Consider enriching: {', '.join(missing_fields[:3])}"
        else:
            return "Manual review required before production deployment"
