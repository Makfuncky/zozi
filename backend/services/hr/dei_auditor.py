"""
DEI & Pay Equity Auditing
Analyzes compensation data for diversity, equity, and inclusion metrics
"""
import logging
import statistics
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from data.models_employee_models import Employee
from data.models import User

logger = logging.getLogger("zozi.dei")


class _LazyNumpy:
    """Lazy proxy for numpy to avoid top-level import."""
    def __getattr__(self, name):
        import numpy as np
        return getattr(np, name)


np = _LazyNumpy()


@dataclass
class PayEquityResult:
    metric: str
    value: float
    benchmark: float
    flagged: bool


class PayEquityAnalyzer:
    """Advanced pay equity analysis using statistical methods."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_compensation_index(self, salaries: List[float], market_avg: float) -> float:
        """Calculate compensation equity index."""
        if not salaries or market_avg == 0:
            return 1.0
        avg_salary = statistics.mean(salaries) if salaries else 0
        return avg_salary / market_avg if market_avg else 1.0
    
    def detect_disparity(
        self,
        group_a_salaries: List[float],
        group_b_salaries: List[float],
        threshold: float = 0.05
    ) -> Tuple[float, bool]:
        """Detect statistically significant pay disparity."""
        if not group_a_salaries or not group_b_salaries:
            return 0.0, False
        
        mean_a = statistics.mean(group_a_salaries)
        mean_b = statistics.mean(group_b_salaries)
        
        pooled_std = np.sqrt(
            (np.var(group_a_salaries) + np.var(group_b_salaries)) / 2
        )
        
        effect_size = abs(mean_a - mean_b) / pooled_std if pooled_std > 0 else 0
        return effect_size, effect_size > threshold
    
    def regression_analysis(self, employees: List[Employee]) -> Dict[str, float]:
        """Perform regression-based pay equity analysis."""
        data = []
        for emp in employees:
            if emp.salary is not None:
                data.append({
                    "salary": float(emp.salary),
                    "experience": emp.years_of_experience or 0,
                    "performance_score": emp.performance_score or 75,
                    "education_level": {"bachelor": 1, "master": 2, "phd": 3}.get(emp.education_level, 0)
                })
        
        if len(data) < 3:
            return {"r_squared": 0, "coefficients": {}}
        
        X = np.array([[d["experience"], d["performance_score"]] for d in data])
        y = np.array([d["salary"] for d in data])
        
        try:
            coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
            y_pred = X @ coeffs
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            return {"r_squared": r_squared, "coefficients": coeffs.tolist()}
        except Exception:
            return {"r_squared": 0, "coefficients": []}


class DEIAuditor:
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_pay_gap(self, department: Optional[str] = None) -> Dict:
        query = self.db.query(Employee).join(User).filter(Employee.employment_status == "active")
        if department:
            query = query.filter(Employee.department == department)
        
        employees = query.all()
        
        by_gender = {}
        for emp in employees:
            gender = emp.gender or "unknown"
            if gender not in by_gender:
                by_gender[gender] = {"count": 0, "total_salary": Decimal("0")}
            by_gender[gender]["count"] += 1
            by_gender[gender]["total_salary"] += emp.salary or Decimal("0")
        
        avg_by_gender = {g: data["total_salary"] / data["count"] if data["count"] > 0 else 0 
                         for g, data in by_gender.items()}
        
        return {
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "department": department,
            "gender_distribution": {g: d["count"] for g, d in by_gender.items()},
            "average_salary_by_gender": {g: str(s) for g, s in avg_by_gender.items()},
            "pay_gap": str(max(avg_by_gender.values()) - min(avg_by_gender.values())) if len(avg_by_gender) > 1 else "0"
        }
    
    def analyze_leadership_diversity(self) -> Dict:
        managers = self.db.query(Employee).filter(
            Employee.reporting_manager_id != None
        ).all()
        
        manager_ids = set(e.reporting_manager_id for e in managers)
        
        leadership_stats = {
            "total_managers": len(manager_ids),
            "male_managers": 0,
            "female_managers": 0,
            "other_managers": 0
        }
        
        for emp in self.db.query(Employee).filter(Employee.id.in_(manager_ids)).all():
            gender = emp.gender or "other"
            if gender == "male":
                leadership_stats["male_managers"] += 1
            elif gender == "female":
                leadership_stats["female_managers"] += 1
            else:
                leadership_stats["other_managers"] += 1
        
        total = leadership_stats["total_managers"] or 1
        return {
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "leadership_diversity": leadership_stats,
            "male_percentage": round(leadership_stats["male_managers"] / total * 100, 2),
            "female_percentage": round(leadership_stats["female_managers"] / total * 100, 2)
        }
    
    def generate_equity_report(self) -> Dict:
        return {
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "pay_gap_analysis": self.analyze_pay_gap(),
            "leadership_diversity": self.analyze_leadership_diversity()
        }


def get_dei_auditor(db: Session) -> DEIAuditor:
    return DEIAuditor(db)

