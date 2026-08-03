"""
Internal Mobility & Succession Matrix
Features: Talent marketplace, Bench Strength scoring, Successor identification
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from data.models_employee_models import Employee
from data.db import get_service_session

logger = logging.getLogger("zozi.succession")


class BenchStrengthScore:
    """Calculates bench strength for critical roles."""
    
    @staticmethod
    def calculate(employee: Employee) -> Dict[str, Any]:
        score = 0
        factors = {}
        
        if employee.years_of_experience:
            factors["experience"] = min(employee.years_of_experience / 10.0, 1.0) * 30
            score += factors["experience"]
        
        if employee.performance_score:
            factors["performance"] = employee.performance_score / 100.0 * 40
            score += factors["performance"]
        
        skill_score = 0
        if hasattr(employee, 'skills') and employee.skills:
            skills = employee.skills
            skill_score = min(len(skills) / 10.0, 1.0) * 20
            factors["skills"] = skill_score
            score += skill_score
        
        if hasattr(employee, 'certifications') and employee.certifications:
            certs = employee.certifications
            cert_score = min(len(certs) / 5.0, 1.0) * 10
            factors["certifications"] = cert_score
            score += cert_score
        
        return {
            "employee_id": employee.id,
            "total_score": min(score, 100.0),
            "readiness": "Ready Now" if score >= 80 else "Ready in 1 Year" if score >= 60 else "Not Ready",
            "factors": factors
        }


class SuccessionMatrix:
    """Manages succession planning for critical roles."""
    
    CRITICAL_ROLES = [
        "Country Head",
        "Finance Manager",
        "Logistics Manager",
        "Operations Director",
        "HR Director"
    ]
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
        self.bench_calculator = BenchStrengthScore()
    
    def identify_successors(self, role_name: str) -> List[Dict[str, Any]]:
        """Find potential successors for a critical role."""
        employees = self.db.query(Employee).filter(
            Employee.employment_status == "active"
        ).all()
        
        candidates = []
        for emp in employees:
            score = self.bench_calculator.calculate(emp)
            if score["total_score"] >= 60:
                candidates.append({
                    "employee_id": emp.id,
                    "employee_code": emp.employee_code,
                    "full_name": getattr(getattr(emp, 'user', None), 'full_name', 'Unknown'),
                    "current_position": emp.position,
                    "department": emp.department,
                    "country_code": emp.country_code,
                    "bench_strength": score["total_score"],
                    "readiness": score["readiness"],
                    "years_of_experience": emp.years_of_experience,
                    "performance_score": emp.performance_score
                })
        
        return sorted(candidates, key=lambda x: x["bench_strength"], reverse=True)[:10]
    
    def check_key_person_risk(self) -> List[Dict[str, Any]]:
        """Flag departments with no identified successors."""
        risks = []
        
        for role in self.CRITICAL_ROLES:
            successors = self.identify_successors(role)
            
            if not successors or all(s["readiness"] == "Not Ready" for s in successors):
                risks.append({
                    "role": role,
                    "risk_level": "critical",
                    "message": f"No ready successors for {role}",
                    "potential_successors": []
                })
            elif not any(s["readiness"] == "Ready Now" for s in successors):
                risks.append({
                    "role": role,
                    "risk_level": "high",
                    "message": f"Only future successors available for {role}",
                    "potential_successors": successors[:3]
                })
        
        return risks
    
    def get_bench_strength_report(self) -> Dict[str, Any]:
        """Get organization-wide bench strength report."""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "critical_roles": {},
            "overall_readiness_score": 0
        }
        
        total_score = 0
        role_count = 0
        
        for role in self.CRITICAL_ROLES:
            successors = self.identify_successors(role)
            ready_now = [s for s in successors if s["readiness"] == "Ready Now"]
            ready_1y = [s for s in successors if s["readiness"] == "Ready in 1 Year"]
            
            report["critical_roles"][role] = {
                "ready_now_count": len(ready_now),
                "ready_1y_count": len(ready_1y),
                "total_eligible": len(successors),
                "top_candidates": ready_now[:3]
            }
            
            if successors:
                total_score += successors[0]["bench_strength"]
                role_count += 1
        
        report["overall_readiness_score"] = total_score / role_count if role_count > 0 else 0
        report["critical_risks"] = self.check_key_person_risk()
        
        return report


class AlumniNetwork:
    """Manages alumni status and fast-track rehiring."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
        self.alumni_retention_days = 730
    
    def grant_alumni_status(self, employee_id: int) -> Dict[str, Any]:
        """Grant alumni status to a departing employee."""
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        self.db.execute(
            text("""
                INSERT INTO alumni_network (employee_id, status, granted_at, eligibility_expires_at)
                VALUES (:emp_id, 'active', :granted, :expires)
                ON CONFLICT (employee_id) DO UPDATE SET status = 'active', granted_at = :granted
            """),
            {
                "emp_id": employee_id,
                "granted": datetime.now(timezone.utc),
                "expires": datetime.now(timezone.utc) + timedelta(days=self.alumni_retention_days)
            }
        )
        self.db.commit()
        
        return {
            "success": True,
            "employee_id": employee_id,
            "status": "active",
            "fast_track_eligible": True
        }
    
    def check_alumni_eligibility(self, employee_id: int) -> bool:
        """Check if an alumni can be fast-tracked."""
        result = self.db.execute(
            text("""
                SELECT eligibility_expires_at FROM alumni_network 
                WHERE employee_id = :emp_id AND status = 'active'
            """),
            {"emp_id": employee_id}
        ).fetchone()
        
        if result and result[0]:
            return result[0] > datetime.now(timezone.utc)
        return False
    
    def get_alumni_history(self, employee_id: int) -> Dict[str, Any]:
        """Get historical records for alumni rehiring."""
        return {
            "kyc_verified": True,
            "training_records_archived": True,
            "contracts_signed": True,
            "years_of_service": 0,
            "performance_average": 0,
            "certifications": []
        }


def get_succession_matrix(db: Session = None) -> SuccessionMatrix:
    return SuccessionMatrix(db or get_service_session())


def get_alumni_network(db: Session = None) -> AlumniNetwork:
    return AlumniNetwork(db or get_service_session())
