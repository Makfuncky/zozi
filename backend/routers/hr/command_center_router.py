router = APIRouter()


class CommandCenter:
    def __init__(self, db: Session):
        self.db = db
    
    def get_headcount_metrics(self) -> Dict:
        total = self.db.query(Employee).count()
        active = self.db.query(Employee).filter(
            Employee.employment_status == "active"
        ).count()
        terminated = self.db.query(Employee).filter(
            Employee.employment_status == "terminated"
        ).count()
        
        return {
            "total_employees": total,
            "active_employees": active,
            "terminated_employees": terminated,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_attendance_metrics(self, days: int = 30) -> Dict:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        total = self.db.query(EmployeeAttendance).filter(
            EmployeeAttendance.scan_in_time >= cutoff
        ).count()
        
        unique_employees = self.db.query(
            func.count(distinct(EmployeeAttendance.employee_id))
        ).filter(EmployeeAttendance.scan_in_time >= cutoff).scalar()
        
        return {
            "total_scans": total,
            "unique_employees": unique_employees,
            "period_days": days
        }
    
    def get_treasury_metrics(self) -> Dict:
        total_balance = self.db.query(func.coalesce(func.sum(TreasuryAccount.balance), 0)).scalar()
        
        return {
            "total_treasury_balance": str(total_balance or 0),
            "active_accounts": self.db.query(TreasuryAccount).filter(
                TreasuryAccount.is_active == True
            ).count()
        }
    
    def get_geo_fence_anomalies(self, hours: int = 24) -> Dict:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        anomalies = self.db.query(GeoFenceLog).filter(
            GeoFenceLog.scanned_at >= cutoff,
            GeoFenceLog.is_within_fence == False
        ).count()
        
        return {
            "anomalies_detected": anomalies,
            "period_hours": hours
        }
    
    def get_dashboard(self) -> Dict:
        return {
            "headcount": self.get_headcount_metrics(),
            "attendance": self.get_attendance_metrics(),
            "treasury": self.get_treasury_metrics(),
            "security": self.get_geo_fence_anomalies(),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    cc = CommandCenter(db)
    return cc.get_dashboard()


@router.get("/headcount")
def get_headcount(db: Session = Depends(get_db)):
    cc = CommandCenter(db)
    return cc.get_headcount_metrics()


@router.get("/attendance")
def get_attendance(days: int = 30, db: Session = Depends(get_db)):
    cc = CommandCenter(db)
    return cc.get_attendance_metrics(days)


@router.get("/treasury")
def get_treasury_metrics(db: Session = Depends(get_db)):
    cc = CommandCenter(db)
    return cc.get_treasury_metrics()


@router.get("/security")
def get_security(hours: int = 24, db: Session = Depends(get_db)):
    cc = CommandCenter(db)
    return cc.get_geo_fence_anomalies(hours)


def get_command_center(db: Session) -> CommandCenter:
    return CommandCenter(db)