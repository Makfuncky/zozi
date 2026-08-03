from __future__ import annotations

import logging
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from data.models import (
    ImportShipment, ImportShipmentLine, LandedCostAllocation,
    CustomsEntry, ImportCostTemplate,
    PurchaseOrder, PurchaseOrderLine,
    Warehouse, Vendor, Product,
    Account, AccountGroup, AccountBalance,
    JournalEntry, JournalEntryLine,
)
from data.schemas import JournalEntryCreate, JournalLineInput
from services import general_ledger_service as gl
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

GOODS_IN_TRANSIT = "1410"
INVENTORY = "1060"
AP_ACCOUNT = "2010"
CASH_ACCOUNT = "1010"
CUSTOMS_DUTY_PAYABLE = "2095"
FX_GAIN_LOSS = "6060"


def _ensure_import_accounts(db: Session) -> None:
    existing = {a.code for a in db.query(Account).all()}
    groups = {g.code: g.id for g in db.query(AccountGroup).all()}
    asset_group = groups.get("1.1")
    liability_group = groups.get("2.1")
    expense_group = groups.get("5.2")
    to_create = []
    if "1410" not in existing and asset_group:
        to_create.append(Account(code="1410", name="Goods in Transit", group_id=asset_group,
                                 normal_side="debit", currency="OMR"))
    if "2095" not in existing and liability_group:
        to_create.append(Account(code="2095", name="Customs Duty Payable", group_id=liability_group,
                                 normal_side="credit", currency="OMR"))
    if "6060" not in existing and expense_group:
        to_create.append(Account(code="6060", name="Unrealized FX Gain/Loss", group_id=expense_group,
                                 normal_side="debit", currency="OMR"))
    for acct in to_create:
        db.add(acct)
        db.flush()
        db.add(AccountBalance(account_id=acct.id, currency="OMR", balance=Decimal("0.00")))
    if to_create:
        db.commit()
        logger.info("Created import GL accounts: %s", [a.code for a in to_create])


def _next_number(db: Session, prefix: str, table_column) -> str:
    last = db.query(func.max(table_column)).filter(
        table_column.like(f"{prefix}-%")
    ).scalar()
    seq = 1
    if last:
        try:
            seq = int(last.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}-{seq:05d}"


def _get_cost_template(db: Session, country_code: str = None) -> Optional[ImportCostTemplate]:
    q = db.query(ImportCostTemplate).filter(ImportCostTemplate.is_active == True)
    if country_code:
        q = q.filter(ImportCostTemplate.country_code == country_code)
    return q.first()


# ── Shipment ──


def create_import_shipment(
    db: Session, *, po_id: int = None, supplier_id: int = None,
    origin_country: str = None, port_of_loading: str = None,
    port_of_discharge: str = None, vessel_name: str = None,
    bill_of_lading: str = None, container_number: str = None,
    shipment_date: datetime = None, estimated_arrival: datetime = None,
    currency: str = "OMR", exchange_rate: Decimal = Decimal("1"),
    warehouse_id: int = None, country_code: str = None,
    notes: str = None, created_by: int = None,
    lines: list[dict] = None,
) -> ImportShipment:
    _ensure_import_accounts(db)
    shipment_ref = _next_number(db, "SHIP", ImportShipment.shipment_ref)
    po = None
    if po_id:
        po = db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.lines)
        ).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError("Purchase order not found")
        if not supplier_id:
            supplier_id = po.supplier_id
        if not warehouse_id:
            warehouse_id = po.warehouse_id
        if not country_code:
            country_code = po.country_code
        if not currency:
            currency = po.currency
        if not lines:
            lines = [
                {
                    "po_line_id": pl.id, "product_id": pl.product_id,
                    "product_name": pl.product_name, "sku": pl.sku,
                    "quantity": float(pl.quantity_ordered),
                    "unit_cost_fx": float(pl.unit_price),
                    "weight_kg": float(pl.weight) if pl.weight else None,
                    "volume_cbm": float(pl.volume) if pl.volume else None,
                }
                for pl in po.lines if pl.quantity_ordered > 0
            ]
    supplier = db.query(Vendor).filter(Vendor.id == supplier_id).first() if supplier_id else None
    shipment = ImportShipment(
        shipment_ref=shipment_ref, po_id=po_id,
        supplier_id=supplier_id, supplier_name=supplier.name if supplier else None,
        origin_country=origin_country, port_of_loading=port_of_loading,
        port_of_discharge=port_of_discharge, vessel_name=vessel_name,
        bill_of_lading=bill_of_lading, container_number=container_number,
        shipment_date=shipment_date or _utcnow(),
        estimated_arrival=estimated_arrival,
        currency=currency, exchange_rate=Decimal(str(exchange_rate)),
        warehouse_id=warehouse_id, country_code=country_code,
        notes=notes, created_by=created_by, status="draft",
    )
    db.add(shipment)
    db.flush()
    product_cost_total = Decimal("0")
    for ld in (lines or []):
        qty = Decimal(str(ld.get("quantity", 0)))
        cost_fx = Decimal(str(ld.get("unit_cost_fx", 0)))
        cost_local = cost_fx * Decimal(str(exchange_rate))
        line_total = qty * cost_fx
        product_cost_total += line_total
        sl = ImportShipmentLine(
            shipment_id=shipment.id,
            po_line_id=ld.get("po_line_id"),
            product_id=ld.get("product_id"),
            product_name=ld.get("product_name"), sku=ld.get("sku"),
            hs_code=ld.get("hs_code"),
            quantity=qty, unit_cost_fx=cost_fx, unit_cost_local=cost_local,
            line_total_fx=line_total,
            weight_kg=Decimal(str(ld.get("weight_kg", 0))) if ld.get("weight_kg") else None,
            volume_cbm=Decimal(str(ld.get("volume_cbm", 0))) if ld.get("volume_cbm") else None,
            country_code=country_code,
        )
        db.add(sl)
    shipment.product_cost_total = product_cost_total
    db.commit()
    db.refresh(shipment)
    return shipment


def confirm_shipment(db: Session, shipment_id: int, actual_arrival: datetime = None) -> ImportShipment:
    shipment = db.query(ImportShipment).options(
        joinedload(ImportShipment.lines)
    ).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    if shipment.status != "draft":
        raise ValueError(f"Cannot confirm shipment in status '{shipment.status}'")
    shipment.status = "in_transit"
    if actual_arrival:
        shipment.actual_arrival = actual_arrival
    _post_goods_in_transit_journal(db, shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


def _post_goods_in_transit_journal(db: Session, shipment: ImportShipment) -> None:
    total = Decimal("0")
    lines_by_product = {}
    for sl in shipment.lines:
        cost = (sl.unit_cost_local or sl.unit_cost_fx) * sl.quantity
        total += cost
        lines_by_product[sl.product_id] = cost
    if total <= 0:
        return
    if not db.query(Account).filter(Account.code == GOODS_IN_TRANSIT).first():
        logger.warning("Goods in Transit account (%s) not found — skipping journal", GOODS_IN_TRANSIT)
        return
    try:
        gl.create_journal_entry(db, JournalEntryCreate(
            entry_date=shipment.shipment_date or _utcnow(),
            reference_type="import_shipment", reference_id=shipment.id,
            description=f"Goods in transit — {shipment.shipment_ref}",
            currency=shipment.currency, country_code=shipment.country_code,
            lines=[
                JournalLineInput(
                    account_code=GOODS_IN_TRANSIT, side="debit",
                    amount=total,
                    description=f"Goods in transit {shipment.shipment_ref}",
                    entity_type="import_shipment", entity_id=shipment.id,
                ),
                JournalLineInput(
                    account_code=AP_ACCOUNT, side="credit",
                    amount=total,
                    description=f"AP accrual — {shipment.shipment_ref}",
                    entity_type="import_shipment", entity_id=shipment.id,
                ),
            ],
        ))
    except Exception as e:
        logger.warning("Goods in transit journal post failed: %s", e)


# ── Landed Cost Allocation ──


def allocate_landed_costs(
    db: Session, shipment_id: int, *,
    freight_cost: Decimal = None, insurance_cost: Decimal = None,
    port_charges: Decimal = None, inland_freight: Decimal = None,
    bank_charges: Decimal = None, other_costs: Decimal = None,
    allocation_method: str = "by_value",
    freight_vendor_id: int = None, insurance_vendor_id: int = None,
    created_by: int = None,
) -> ImportShipment:
    _ensure_import_accounts(db)
    shipment = db.query(ImportShipment).options(
        joinedload(ImportShipment.lines)
    ).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    if shipment.status not in ("in_transit", "draft"):
        raise ValueError(f"Cannot allocate costs for shipment in status '{shipment.status}'")
    costs = {}
    if freight_cost is not None:
        costs["freight"] = Decimal(str(freight_cost))
    if insurance_cost is not None:
        costs["insurance"] = Decimal(str(insurance_cost))
    if port_charges is not None:
        costs["port_charges"] = Decimal(str(port_charges))
    if inland_freight is not None:
        costs["inland_freight"] = Decimal(str(inland_freight))
    if bank_charges is not None:
        costs["bank_charges"] = Decimal(str(bank_charges))
    if other_costs is not None:
        costs["other_costs"] = Decimal(str(other_costs))
    if not costs:
        return shipment
    lines = shipment.lines
    if not lines:
        raise ValueError("Shipment has no lines to allocate costs against")
    weights = _compute_allocation_weights(lines, allocation_method)
    total_weight = sum(weights.values())
    if total_weight == 0:
        raise ValueError("Cannot allocate — total allocation weight is zero")
    for cost_type, cost_amount in costs.items():
        _create_cost_allocation(db, shipment, cost_type, cost_amount, weights, total_weight,
                                allocation_method, created_by)
    shipment.freight_cost = (shipment.freight_cost or 0) + costs.get("freight", 0)
    shipment.insurance_cost = (shipment.insurance_cost or 0) + costs.get("insurance", 0)
    shipment.port_charges = (shipment.port_charges or 0) + costs.get("port_charges", 0)
    shipment.inland_freight = (shipment.inland_freight or 0) + costs.get("inland_freight", 0)
    shipment.bank_charges = (shipment.bank_charges or 0) + costs.get("bank_charges", 0)
    shipment.other_costs = (shipment.other_costs or 0) + costs.get("other_costs", 0)
    t = (shipment.freight_cost + shipment.insurance_cost + shipment.port_charges
         + shipment.inland_freight + shipment.bank_charges + shipment.other_costs)
    shipment.total_landed_cost = shipment.product_cost_total + t
    _post_landed_cost_journals(db, shipment, costs, created_by)
    db.commit()
    db.refresh(shipment)
    return shipment


def _compute_allocation_weights(lines: list[ImportShipmentLine], method: str) -> dict[int, Decimal]:
    weights = {}
    if method == "by_value":
        for l in lines:
            weights[l.id] = l.line_total_fx
    elif method == "by_weight":
        for l in lines:
            w = l.weight_kg or Decimal("0")
            weights[l.id] = w
    elif method == "by_volume":
        for l in lines:
            v = l.volume_cbm or Decimal("0")
            weights[l.id] = v
    elif method == "by_quantity":
        for l in lines:
            weights[l.id] = l.quantity
    else:
        for l in lines:
            weights[l.id] = l.line_total_fx
    return weights


def _create_cost_allocation(db: Session, shipment: ImportShipment, cost_type: str,
                             total_amount: Decimal, weights: dict, total_weight: Decimal,
                             method: str, created_by: int = None) -> None:
    cost_label = cost_type.replace("_", " ").title()
    alloc = LandedCostAllocation(
        shipment_id=shipment.id,
        cost_type=cost_type,
        description=f"{cost_label} — {shipment.shipment_ref}",
        total_amount=total_amount,
        allocation_method=method,
        currency=shipment.currency,
        exchange_rate=shipment.exchange_rate,
        country_code=shipment.country_code,
        status="allocated",
    )
    db.add(alloc)
    db.flush()
    field_map = {
        "freight": "allocated_freight",
        "insurance": "allocated_insurance",
        "port_charges": "allocated_port",
        "inland_freight": "allocated_other",
        "bank_charges": "allocated_other",
        "other_costs": "allocated_other",
    }
    target_field = field_map.get(cost_type, "allocated_other")
    for sl in shipment.lines:
        share = total_amount * (weights.get(sl.id, Decimal("0")) / total_weight)
        share = share.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        setattr(sl, target_field, (getattr(sl, target_field) or 0) + share)
        allocated = (sl.allocated_freight + sl.allocated_insurance + sl.allocated_port
                     + sl.allocated_other)
        total_cost = (sl.unit_cost_local or sl.unit_cost_fx) * sl.quantity + allocated
        sl.landed_unit_cost = (total_cost / sl.quantity).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _post_landed_cost_journals(db: Session, shipment: ImportShipment, costs: dict,
                                created_by: int = None) -> None:
    account_map = {
        "freight": (GOODS_IN_TRANSIT, AP_ACCOUNT),
        "insurance": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
        "port_charges": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
        "inland_freight": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
        "bank_charges": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
        "other_costs": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
    }
    for cost_type, amount in costs.items():
        if amount <= 0:
            continue
        dr, cr = account_map.get(cost_type, (GOODS_IN_TRANSIT, CASH_ACCOUNT))
        try:
            gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=_utcnow(),
                reference_type="landed_cost", reference_id=shipment.id,
                description=f"{cost_type.replace('_', ' ').title()} — {shipment.shipment_ref}",
                currency=shipment.currency, country_code=shipment.country_code,
                lines=[
                    JournalLineInput(
                        account_code=dr, side="debit", amount=amount,
                        description=f"{cost_type} allocated to {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                    JournalLineInput(
                        account_code=cr, side="credit", amount=amount,
                        description=f"{cost_type} — {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                ],
            ))
        except Exception as e:
            logger.warning("Landed cost journal failed for %s: %s", cost_type, e)


# ── Customs ──


def record_customs_entry(db: Session, shipment_id: int, *,
                          customs_declaration_number: str = None,
                          customs_broker: str = None,
                          entry_date: datetime = None,
                          duty_rate: Decimal = None,
                          duty_amount: Decimal = None,
                          vat_on_duty: Decimal = None,
                          penalties: Decimal = None,
                          notes: str = None,
                          created_by: int = None) -> CustomsEntry:
    _ensure_import_accounts(db)
    shipment = db.query(ImportShipment).options(
        joinedload(ImportShipment.lines)
    ).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    duty = Decimal(str(duty_amount)) if duty_amount else Decimal("0")
    vat = Decimal(str(vat_on_duty)) if vat_on_duty else Decimal("0")
    penalty = Decimal(str(penalties)) if penalties else Decimal("0")
    total_customs = duty + vat + penalty
    entry = CustomsEntry(
        shipment_id=shipment_id,
        customs_declaration_number=customs_declaration_number,
        customs_broker=customs_broker,
        entry_date=entry_date or _utcnow(),
        duty_rate_applied=Decimal(str(duty_rate)) if duty_rate else None,
        duty_amount=duty, vat_on_duty=vat,
        penalties=penalty, total_customs_cost=total_customs,
        status="cleared", notes=notes,
        country_code=shipment.country_code,
    )
    db.add(entry)
    db.flush()
    shipment.duty_cost = duty
    t = (shipment.freight_cost + shipment.insurance_cost + shipment.port_charges
         + shipment.inland_freight + shipment.bank_charges + shipment.other_costs)
    shipment.total_landed_cost = shipment.product_cost_total + t + duty + vat + penalty
    if total_customs > 0:
        for sl in shipment.lines:
            share = duty * (sl.line_total_fx / shipment.product_cost_total) if shipment.product_cost_total > 0 else 0
            sl.duty_amount = share
            allocated = (sl.allocated_freight + sl.allocated_insurance + sl.allocated_port
                         + sl.allocated_other + (sl.duty_amount or 0))
            total_cost = (sl.unit_cost_local or sl.unit_cost_fx) * sl.quantity + allocated
            sl.landed_unit_cost = (total_cost / sl.quantity).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        try:
            gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=entry.entry_date,
                reference_type="customs_duty", reference_id=entry.id,
                description=f"Customs duty — {shipment.shipment_ref}",
                currency=shipment.currency, country_code=shipment.country_code,
                lines=[
                    JournalLineInput(
                        account_code=GOODS_IN_TRANSIT, side="debit",
                        amount=total_customs,
                        description=f"Duty for {shipment.shipment_ref}",
                        entity_type="customs_entry", entity_id=entry.id,
                    ),
                    JournalLineInput(
                        account_code=CUSTOMS_DUTY_PAYABLE, side="credit",
                        amount=total_customs,
                        description=f"Duty payable for {shipment.shipment_ref}",
                        entity_type="customs_entry", entity_id=entry.id,
                    ),
                ],
            ))
        except Exception as e:
            logger.warning("Customs journal post failed: %s", e)
    db.commit()
    db.refresh(entry)
    return entry


# ── Finalize ──


def finalize_landed_cost(db: Session, shipment_id: int, warehouse_id: int = None,
                          created_by: int = None) -> ImportShipment:
    shipment = db.query(ImportShipment).options(
        joinedload(ImportShipment.lines)
    ).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    if shipment.status not in ("in_transit", "customs_cleared"):
        raise ValueError(f"Cannot finalize shipment in status '{shipment.status}'")
    warehouse = None
    if warehouse_id:
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    elif shipment.warehouse_id:
        warehouse = db.query(Warehouse).filter(Warehouse.id == shipment.warehouse_id).first()
    if not warehouse:
        raise ValueError("Warehouse is required to finalize landed cost")
    total_inventory = Decimal("0")
    for sl in shipment.lines:
        if sl.landed_unit_cost and sl.quantity:
            line_total = sl.landed_unit_cost * sl.quantity
            total_inventory += line_total
            product = db.query(Product).filter(Product.id == sl.product_id).first()
            if product:
                new_cost = sl.landed_unit_cost
                product.cost_price = new_cost
                product.stock = (product.stock or 0) + int(sl.quantity)
    if total_inventory > 0:
        try:
            gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=_utcnow(),
                reference_type="landed_cost_finalize", reference_id=shipment.id,
                description=f"Landed cost finalization — {shipment.shipment_ref}",
                currency=shipment.currency, country_code=shipment.country_code,
                lines=[
                    JournalLineInput(
                        account_code=INVENTORY, side="debit",
                        amount=total_inventory,
                        description=f"Inventory from {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                    JournalLineInput(
                        account_code=GOODS_IN_TRANSIT, side="credit",
                        amount=total_inventory,
                        description=f"Goods in transit cleared — {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                ],
            ))
        except Exception as e:
            logger.warning("Landed cost finalization journal failed: %s", e)
    shipment.warehouse_id = warehouse.id
    shipment.status = "landed"
    db.commit()
    db.refresh(shipment)
    return shipment


# ── FX Revaluation ──


def run_fx_revaluation(db: Session, as_of: date = None, country_code: str = None,
                        created_by: int = None) -> list[dict]:
    _ensure_import_accounts(db)
    as_of = as_of or date.today()
    results = []
    shipments = db.query(ImportShipment).filter(
        ImportShipment.status.in_(["in_transit", "customs_cleared", "landed"]),
        ImportShipment.exchange_rate.isnot(None),
    )
    if country_code:
        shipments = shipments.filter(ImportShipment.country_code == country_code)
    for shipment in shipments.all():
        current_rate = Decimal(str(shipment.exchange_rate))
        diff = Decimal("0")
        if current_rate != Decimal("1"):
            open_balance = shipment.total_landed_cost or shipment.product_cost_total
            revalued = open_balance * current_rate
            diff = revalued - open_balance
        if abs(diff) < Decimal("0.01"):
            continue
        try:
            entry = gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=datetime(as_of.year, as_of.month, as_of.day, 23, 59, 59),
                reference_type="fx_revaluation", reference_id=shipment.id,
                description=f"FX revaluation — {shipment.shipment_ref}",
                currency=shipment.currency, country_code=shipment.country_code,
                lines=[
                    JournalLineInput(
                        account_code=FX_GAIN_LOSS, side="debit" if diff > 0 else "credit",
                        amount=abs(diff),
                        description=f"FX adj for {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                    JournalLineInput(
                        account_code=AP_ACCOUNT, side="credit" if diff > 0 else "debit",
                        amount=abs(diff),
                        description=f"FX adj AP — {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                ],
            ))
            results.append({
                "shipment_id": shipment.id,
                "shipment_ref": shipment.shipment_ref,
                "fx_adjustment": float(diff),
                "journal_entry_id": entry.id,
            })
        except Exception as e:
            logger.warning("FX revaluation failed for %s: %s", shipment.shipment_ref, e)
    return results


# ── Cost Template ──


def create_cost_template(db: Session, *, name: str,
                          default_duty_rate: Decimal = None,
                          default_freight_percent: Decimal = None,
                          default_insurance_percent: Decimal = None,
                          default_port_charges_percent: Decimal = None,
                          default_bank_charges_percent: Decimal = None,
                          allocation_method: str = "by_value",
                          country_code: str = None) -> ImportCostTemplate:
    existing = db.query(ImportCostTemplate).filter(
        ImportCostTemplate.name == name,
        ImportCostTemplate.country_code == country_code,
    ).first()
    if existing:
        raise ValueError(f"Cost template '{name}' already exists for this country")
    tmpl = ImportCostTemplate(
        name=name,
        default_duty_rate=default_duty_rate,
        default_freight_percent=default_freight_percent,
        default_insurance_percent=default_insurance_percent,
        default_port_charges_percent=default_port_charges_percent,
        default_bank_charges_percent=default_bank_charges_percent,
        allocation_method=allocation_method,
        country_code=country_code,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


def auto_allocate_from_template(db: Session, shipment_id: int,
                                  template_id: int = None,
                                  country_code: str = None,
                                  created_by: int = None) -> ImportShipment:
    shipment = db.query(ImportShipment).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    tmpl = None
    if template_id:
        tmpl = db.query(ImportCostTemplate).filter(ImportCostTemplate.id == template_id).first()
    else:
        tmpl = _get_cost_template(db, country_code or shipment.country_code)
    if not tmpl:
        raise ValueError("No cost template found. Create one or specify template_id.")
    product_cost = shipment.product_cost_total or Decimal("0")
    costs = {}
    if tmpl.default_freight_percent:
        costs["freight_cost"] = product_cost * tmpl.default_freight_percent / Decimal("100")
    if tmpl.default_insurance_percent:
        costs["insurance_cost"] = product_cost * tmpl.default_insurance_percent / Decimal("100")
    if tmpl.default_port_charges_percent:
        costs["port_charges"] = product_cost * tmpl.default_port_charges_percent / Decimal("100")
    if tmpl.default_bank_charges_percent:
        costs["bank_charges"] = product_cost * tmpl.default_bank_charges_percent / Decimal("100")
    return allocate_landed_costs(
        db, shipment_id, allocation_method=tmpl.allocation_method,
        created_by=created_by, **costs,
    )


# ── Listing ──


def list_shipments(db: Session, status: str = None, po_id: int = None,
                    country_code: str = None, limit: int = 50, offset: int = 0) -> dict:
    q = db.query(ImportShipment)
    if status:
        q = q.filter(ImportShipment.status == status)
    if po_id:
        q = q.filter(ImportShipment.po_id == po_id)
    if country_code:
        q = q.filter(ImportShipment.country_code == country_code)
    total = q.count()
    rows = q.order_by(ImportShipment.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": rows}


def list_templates(db: Session, country_code: str = None) -> list[ImportCostTemplate]:
    q = db.query(ImportCostTemplate)
    if country_code:
        q = q.filter(ImportCostTemplate.country_code == country_code)
    return q.order_by(ImportCostTemplate.name).all()