"""
Advanced Treasury Service
Features: EOSB accrual, Contractor disbursement, Payroll integration, Double-Entry Accounting
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text

from models.employee_models import Employee
from models import User, TreasuryAccount, TreasuryTransaction, JournalEntry, JournalEntryLine, Account
from db.database import get_service_session

logger = logging.getLogger("zozi.treasury")


class EOSBAccrualEngine:
    """Calculates End-of-Service Benefits for GCC compliance."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_eosb(
        self,
        employee: Employee,
        as_of_date: datetime = None
    ) -> Decimal:
        """Calculate EOSB based on GCC labor law formulas."""
        if not as_of_date:
            as_of_date = datetime.now(timezone.utc)
        
        if not employee.hire_date:
            return Decimal("0")
        
        years_of_service = (as_of_date - employee.hire_date).days / 365.25
        
        if years_of_service < 1:
            return Decimal("0")
        
        monthly_salary = employee.salary or Decimal("0")
        
        if years_of_service < 5:
            eosb = monthly_salary * Decimal(str(years_of_service * 0.5 / 12))
        else:
            eosb = (monthly_salary * 12) + (monthly_salary * Decimal("0.5") * (years_of_service - 5))
        
        return eosb.quantize(Decimal("0.01"))


class ContractorDisbursementEngine:
    """Handles contractor milestone-based payouts."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_milestone(
        self,
        contractor_id: int,
        milestone_proof: str,
        entity_type: str
    ) -> bool:
        """Verify milestone completion against operational databases."""
        if entity_type == "logistics":
            shipment = self.db.execute(
                text("SELECT * FROM shipments WHERE assigned_partner_id = :cid AND status = 'delivered'"),
                {"cid": contractor_id}
            ).fetchone()
            return shipment is not None
        
        return True
    
    def calculate_milestone_payment(
        self,
        milestone_data: Dict[str, Any]
    ) -> Decimal:
        """Calculate payment for completed milestone."""
        base_amount = Decimal(str(milestone_data.get("amount", 0)))
        bonus = Decimal(str(milestone_data.get("bonus", 0)))
        return base_amount + bonus


class PayEquityAnalyzer:
    """Analyzes pay equity for DEI compliance."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_pay_equity(
        self,
        department: Optional[str] = None,
        country_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze pay equity across demographics."""
        query = self.db.query(Employee).join(User).filter(
            Employee.employment_status == "active"
        )
        
        if department:
            query = query.filter(Employee.department == department)
        if country_code:
            query = query.filter(Employee.country_code == country_code)
        
        employees = query.all()
        
        by_role = {}
        for emp in employees:
            role = emp.position or "unassigned"
            if role not in by_role:
                by_role[role] = []
            if emp.salary:
                by_role[role].append(float(emp.salary))
        
        disparities = []
        for role, salaries in by_role.items():
            if len(salaries) >= 2:
                avg = sum(salaries) / len(salaries)
                variance = max(salaries) - min(salaries)
                if variance / avg > 0.1:
                    disparities.append({
                        "role": role,
                        "average": avg,
                        "variance": variance,
                        "flagged": True
                    })
        
        return {
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "department": department,
            "roles_analyzed": len(by_role),
            "disparities": disparities,
            "equity_score": 1.0 - (len(disparities) / max(1, len(by_role)))
        }


class GeneralLedgerService:
    """Double-Entry Accounting Service for the Treasury."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_account_by_code(self, code: str) -> Optional[Account]:
        """Get account by GL code."""
        return self.db.query(Account).filter(Account.code == code).first()
    
    def create_journal_entry(
        self,
        reference_number: str,
        description: Optional[str],
        source: Optional[str],
        country_code: Optional[str],
        lines: List[Dict[str, Any]]
    ) -> JournalEntry:
        """Create a double-entry journal entry with validation."""
        total_debits = Decimal("0")
        total_credits = Decimal("0")
        
        for line in lines:
            amount = Decimal(str(line.get("amount", 0)))
            side = line.get("side", "").lower()
            if side == "debit":
                total_debits += amount
            elif side == "credit":
                total_credits += amount
            else:
                raise ValueError(f"Invalid side '{side}' for line")
        
        if total_debits != total_credits:
            raise ValueError(
                f"Debits ({total_debits}) must equal credits ({total_credits})"
            )
        
        entry = JournalEntry(
            reference_number=reference_number,
            description=description,
            source=source,
            country_code=country_code,
            entry_date=datetime.utcnow(),
        )
        self.db.add(entry)
        self.db.commit()
        
        for line in lines:
            jel = JournalEntryLine(
                entry_id=entry.id,
                account_id=line["account_id"],
                amount=Decimal(str(line["amount"])),
                side=line["side"].lower(),
                description=line.get("description"),
                country_code=country_code,
            )
            self.db.add(jel)
        
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def get_account_balance(self, account_id: int) -> Decimal:
        """Calculate account balance from journal entries."""
        result = self.db.execute(text("""
            SELECT 
                COALESCE(SUM(CASE WHEN side = 'credit' THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN side = 'debit' THEN amount ELSE 0 END), 0) as balance
            FROM journal_entry_lines jel
            WHERE jel.account_id = :account_id
        """), {"account_id": account_id}).scalar()
        return result or Decimal("0")
    
    def get_trial_balance(self) -> List[Dict[str, Any]]:
        """Generate trial balance for all accounts."""
        results = self.db.execute(text("""
            SELECT 
                a.code,
                a.name,
                ag.code as group_code,
                COALESCE(SUM(CASE WHEN jel.side = 'credit' THEN jel.amount ELSE 0 END), 0) as credits,
                COALESCE(SUM(CASE WHEN jel.side = 'debit' THEN jel.amount ELSE 0 END), 0) as debits,
                COALESCE(SUM(CASE WHEN jel.side = 'credit' THEN jel.amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN jel.side = 'debit' THEN jel.amount ELSE 0 END), 0) as balance
            FROM accounts a
            LEFT JOIN account_groups ag ON a.group_id = ag.id
            LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
            GROUP BY a.id, a.code, a.name, ag.code
            ORDER BY a.code
        """)).fetchall()
        
        return [
            {
                "account_code": r[0],
                "account_name": r[1],
                "group_code": r[2],
                "credits": float(r[3]),
                "debits": float(r[4]),
                "balance": float(r[5])
            }
            for r in results
        ]


class TreasuryService:
    """Main treasury service orchestrating payroll, EOSB, and disbursements."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
        self.eosb_engine = EOSBAccrualEngine(self.db)
        self.contractor_engine = ContractorDisbursementEngine(self.db)
        self.pay_equity_analyzer = PayEquityAnalyzer(self.db)
        self.ledger = GeneralLedgerService(self.db)
    
    def create_payroll_journal_entry(
        self,
        employee_id: int,
        gross_salary: Decimal,
        tax_withheld: Decimal,
        net_pay: Decimal,
        eosb_accrual: Decimal
    ) -> Dict[str, Any]:
        """Create double-entry journal entry for payroll."""
        entry = {
            "debit": {
                "account": "OperatingExpenses.Salaries",
                "amount": gross_salary
            },
            "credit": [
                {"account": "Liabilities.TaxPayable", "amount": tax_withheld},
                {"account": "Liabilities.NetPayPayable", "amount": net_pay},
                {"account": "Liabilities.EOSBPayable", "amount": eosb_accrual}
            ],
            "employee_id": employee_id,
            "journal_date": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Created payroll journal: {entry}")
        return entry
    
    def create_contractor_payment(
        self,
        contractor_id: int,
        milestone_id: int,
        amount: Decimal,
        proof_verified: bool = True
    ) -> Dict[str, Any]:
        """Create AP disbursement for contractor milestone."""
        entry = {
            "debit": {
                "account": "OperatingExpenses.ContractorServices",
                "amount": amount
            },
            "credit": {
                "account": "Liabilities.AccountsPayable",
                "amount": amount
            },
            "contractor_id": contractor_id,
            "milestone_id": milestone_id,
            "proof_verified": proof_verified,
            "disbursement_date": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Created contractor payment: {entry}")
        return entry
    
    def get_payroll_hold_status(self, employee_id: int) -> Dict[str, Any]:
        """Check if payroll hold is active for an employee."""
        employee = self.db.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            return {"status": "not_found"}
        
        return {
            "employee_id": employee_id,
            "hold_active": employee.employment_status == "terminated",
            "hold_reason": "Terminated - awaiting asset return" if employee.employment_status == "terminated" else None
        }
    
    def process_order_ledger_entry(
        self,
        order_id: int,
        amount: Decimal,
        country_code: str,
        gateway_clearing_account: int = 1020,
        deferred_revenue_account: int = 2060
    ) -> JournalEntry:
        """Create journal entry for customer payment via card (Shadow Mode)."""
        return self.ledger.create_journal_entry(
            reference_number=f"ORD-{order_id}",
            description=f"Order payment for order #{order_id}",
            source="checkout",
            country_code=country_code,
            lines=[
                {"account_id": gateway_clearing_account, "amount": amount, "side": "debit", "description": "Gateway clearing"},
                {"account_id": deferred_revenue_account, "amount": amount, "side": "credit", "description": "Deferred revenue"}
            ]
        )
    
    def process_order_delivery_ledger_entry(
        self,
        order_id: int,
        country_code: str,
        supplier_payable: Decimal,
        logistics_payable: Decimal,
        commission_revenue: Decimal,
        vat_payable: Decimal,
        deferred_revenue_account: int = 2060,
        supplier_payable_account: int = 2010,
        logistics_payable_account: int = 2020,
        commission_revenue_account: int = 4010,
        vat_payable_account: int = 2040
    ) -> JournalEntry:
        """Create journal entry for order delivery (Shadow Mode)."""
        total_credits = supplier_payable + logistics_payable + commission_revenue + vat_payable
        
        return self.ledger.create_journal_entry(
            reference_number=f"DEL-{order_id}",
            description=f"Order delivery for order #{order_id}",
            source="order_delivered",
            country_code=country_code,
            lines=[
                {"account_id": deferred_revenue_account, "amount": total_credits, "side": "debit", "description": "Deferred revenue release"},
                {"account_id": supplier_payable_account, "amount": supplier_payable, "side": "credit", "description": "Supplier payable"},
                {"account_id": logistics_payable_account, "amount": logistics_payable, "side": "credit", "description": "Logistics payable"},
                {"account_id": commission_revenue_account, "amount": commission_revenue, "side": "credit", "description": "Commission revenue"},
                {"account_id": vat_payable_account, "amount": vat_payable, "side": "credit", "description": "VAT payable"}
            ]
        )


def get_treasury_service(db: Session = None) -> TreasuryService:
    return TreasuryService(db or get_service_session())
