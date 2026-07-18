"""
EOSB & Treasury Integration Service
End-of-Service Bonus calculation and treasury management
"""
import logging
from decimal import Decimal
from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.employee_models import Employee
from models import TreasuryAccount, TreasuryTransaction

logger = logging.getLogger("zozi.treasury")


class Treasurer:
    def __init__(self, db: Session):
        self.db = db
    
    def create_treasury_account(self, employee_id: int, name: str,
                               account_type: str, currency: str = "OMR",
                               initial_balance: Decimal = Decimal("0.00")) -> TreasuryAccount:
        account = TreasuryAccount(
            employee_id=employee_id,
            slug=f"emp_{employee_id}_{account_type}",
            name=name,
            account_type=account_type,
            currency=currency,
            balance=initial_balance
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def record_transaction(self, from_account_id: int, to_account_id: int,
                           amount: Decimal, currency: str, 
                           transaction_type: str, description: str = None) -> TreasuryTransaction:
        tx = TreasuryTransaction(
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount,
            currency=currency,
            transaction_type=transaction_type,
            description=description
        )
        self.db.add(tx)
        
        if from_account_id:
            from_acc = self.db.query(TreasuryAccount).get(from_account_id)
            if from_acc:
                from_acc.balance -= amount
        
        if to_account_id:
            to_acc = self.db.query(TreasuryAccount).get(to_account_id)
            if to_acc:
                to_acc.balance += amount
        
        self.db.commit()
        self.db.refresh(tx)
        return tx
    
    def get_employee_balance(self, employee_id: int) -> Decimal:
        account = self.db.query(TreasuryAccount).filter(
            TreasuryAccount.employee_id == employee_id,
            TreasuryAccount.is_active
        ).first()
        return account.balance if account else Decimal("0.00")
    
    def calculate_eosb(self, employee_id: int, years_of_service: int,
                       base_salary: Decimal) -> Decimal:
        if years_of_service < 5:
            return Decimal("0.00")
        
        if years_of_service < 10:
            multiplier = Decimal("0.5")
        elif years_of_service < 20:
            multiplier = Decimal("1.0")
        else:
            multiplier = Decimal("2.0")
        
        eosb = base_salary * multiplier
        return eosb
    
    def process_eosb_payment(self, employee_id: int, years_of_service: int,
                             base_salary: Decimal) -> dict:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        eosb_amount = self.calculate_eosb(employee_id, years_of_service, base_salary)
        
        if eosb_amount <= 0:
            return {"success": False, "error": "Not eligible for EOSB"}
        
        treasury_acc = self.db.query(TreasuryAccount).filter(
            TreasuryAccount.account_type == "cash",
            TreasuryAccount.is_active
        ).first()
        
        if not treasury_acc:
            return {"success": False, "error": "No cash account available"}
        
        emp_treasury = self.db.query(TreasuryAccount).filter(
            TreasuryAccount.employee_id == employee_id
        ).first()
        
        if not emp_treasury:
            emp_treasury = self.create_treasury_account(
                employee_id=employee_id,
                name=f"Payroll Account - {employee.employee_code}",
                account_type="receivable"
            )
        
        tx = self.record_transaction(
            from_account_id=treasury_acc.id,
            to_account_id=emp_treasury.id,
            amount=eosb_amount,
            currency="OMR",
            transaction_type="eosb_payment"
        )
        
        return {
            "success": True,
            "employee_id": employee_id,
            "amount": str(eosb_amount),
            "transaction_id": tx.id
        }
    
    def get_treasury_ledger(self, account_id: int, limit: int = 100) -> List[dict]:
        transactions = self.db.query(TreasuryTransaction).filter(
            or_(
                TreasuryTransaction.from_account_id == account_id,
                TreasuryTransaction.to_account_id == account_id
            )
        ).order_by(TreasuryTransaction.created_at.desc()).limit(limit).all()
        
        return [{
            "id": tx.id,
            "from_account": tx.from_account_id,
            "to_account": tx.to_account_id,
            "amount": str(tx.amount),
            "currency": tx.currency,
            "type": tx.transaction_type,
            "description": tx.description,
            "created_at": tx.created_at.isoformat()
        } for tx in transactions]


def get_treasury(db: Session) -> Treasurer:
    return Treasurer(db)

