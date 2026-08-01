"""
Impossible Travel Detection
Detects physically impossible travel patterns using geo-fence logs
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from math import radians, sin, cos, sqrt, atan2

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models.employee_models import GeoFenceLog, Employee

logger = logging.getLogger("zozi.travel")


class ImpossibleTravelDetector:
    def __init__(self, db: Session):
        self.db = db
        self.EARTH_RADIUS_M = 6371000
    
    def calculate_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * sqrt(a) * atan2(sqrt(a), sqrt(1-a))
        return self.EARTH_RADIUS_M * c
    
    def max_travel_speed_mps(self, hours: float) -> float:
        fastest_known = 900
        safety_factor = 0.8
        return fastest_known * safety_factor * hours * 3600
    
    def detect_impossible_travel(self, employee_id: int, 
                                  hours_window: int = 24) -> List[dict]:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=hours_window)
        
        logs = self.db.query(GeoFenceLog).filter(
            GeoFenceLog.employee_id == employee_id,
            GeoFenceLog.scanned_at >= window_start
        ).order_by(GeoFenceLog.scanned_at).all()
        
        if len(logs) < 2:
            return []
        
        anomalies = []
        for i in range(1, len(logs)):
            prev_log = logs[i-1]
            curr_log = logs[i]
            
            time_diff = (curr_log.scanned_at - prev_log.scanned_at).total_seconds() / 3600
            if time_diff == 0:
                continue
            
            distance = self.calculate_distance(
                prev_log.latitude, prev_log.longitude,
                curr_log.latitude, curr_log.longitude
            )
            
            max_distance = self.max_travel_speed_mps(time_diff)
            
            if distance > max_distance:
                anomalies.append({
                    "employee_id": employee_id,
                    "previous_location": {
                        "lat": prev_log.latitude,
                        "lon": prev_log.longitude,
                        "timestamp": prev_log.scanned_at.isoformat()
                    },
                    "current_location": {
                        "lat": curr_log.latitude,
                        "lon": curr_log.longitude,
                        "timestamp": curr_log.scanned_at.isoformat()
                    },
                    "distance_meters": distance,
                    "time_hours": time_diff,
                    "max_possible_meters": max_distance,
                    "speed_ms": distance / (time_diff * 3600),
                    "detected_at": now.isoformat()
                })
        
        return anomalies
    
    def scan_all_employees(self, hours_window: int = 24) -> dict:
        employees = self.db.query(Employee).filter(
            Employee.employment_status == "active"
        ).all()
        
        all_anomalies = []
        for emp in employees:
            anomalies = self.detect_impossible_travel(emp.id, hours_window)
            all_anomalies.extend(anomalies)
        
        return {
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_employees_scanned": len(employees),
            "anomalies_found": len(all_anomalies),
            "anomalies": all_anomalies
        }


def get_travel_detector(db: Session) -> ImpossibleTravelDetector:
    return ImpossibleTravelDetector(db)

