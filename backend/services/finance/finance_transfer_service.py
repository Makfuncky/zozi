from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal, Protocol, cast
from uuid import uuid4

import stripe
import requests

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import CountryConfig, FinanceBankAccount, LogisticsPartnerBankAccount, LogisticsPartnerPayout, LogisticsSettlement, Payout, SupplierBankAccount
from utils.config import settings
from utils.money import round_money, to_decimal

TransferExportType = Literal[
    "supplier-payout-transfers",
    "logistics-payout-transfers",
    "cod-remittance-transfers",
]

DispatchableTransferType = Literal[
    "supplier-payout-transfers",
    "logistics-payout-transfers",
]

TransferReferenceKind = Literal[
    "supplier_payout",
    "logistics_payout",
    "cod_remittance",
]


def get_active_finance_bank_settings(db: Session) -> FinanceBankAccount | None:
    record = (
        db.query(FinanceBankAccount)
        .filter(FinanceBankAccount.is_active == True)
        .order_by(FinanceBankAccount.id.desc())
        .first()
    )
    if record is None or not bool(getattr(record, "is_active", True)):
        return None
    return record


def _clean_reference_prefix(value: str | None) -> str:
    raw = (value or "ZOZI").strip().upper()
    sanitized = re.sub(r"[^A-Z0-9]+", "-", raw)
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    return sanitized or "ZOZI"


def _mask_value(value: str | None, *, visible: int = 4) -> str | None:
    if not value:
        return None
    normalized = value.strip()
    if len(normalized) <= visible:
        return "*" * len(normalized)
    mask_length = max(len(normalized) - visible, 4)
    return f"{'*' * mask_length}{normalized[-visible:]}"


def build_transfer_reference(
    db: Session,
    *,
    kind: TransferReferenceKind,
    entity_id: int,
    record_id: int | None = None,
) -> str:
    record = get_active_finance_bank_settings(db)
    prefix = _clean_reference_prefix(getattr(record, "remittance_reference_prefix", None))
    kind_code = {
        "supplier_payout": "SUP",
        "logistics_payout": "LOG",
        "cod_remittance": "COD",
    }[kind]
    parts = [prefix, kind_code, str(entity_id)]
    if record_id is not None:
        parts.append(str(record_id))
    return "-".join(parts)[:96]


def _has_bank_details(record: FinanceBankAccount | None) -> bool:
    if record is None:
        return False
    return any(
        bool(getattr(record, field, None))
        for field in (
            "account_label",
            "beneficiary_name",
            "bank_name",
            "account_number",
            "iban",
        )
    )


def _serialize_bank_instruction(
    record: FinanceBankAccount | None,
    *,
    title: str,
    direction: str,
    reference_value: str,
    reference_help: str,
    include_sensitive_details: bool,
    fallback_instructions: str,
) -> dict[str, Any]:
    if record is None:
        return {
            "configured": False,
            "title": title,
            "direction": direction,
            "account_label": None,
            "beneficiary_name": None,
            "bank_name": None,
            "branch_name": None,
            "account_number": None,
            "iban": None,
            "swift_code": None,
            "routing_number": None,
            "currency": settings.default_currency,
            "support_email": None,
            "support_phone": None,
            "remittance_reference_prefix": _clean_reference_prefix(None),
            "reference_value": reference_value,
            "reference_help": reference_help,
            "instructions": fallback_instructions,
            "details_visible": include_sensitive_details,
        }

    account_number = record.account_number if include_sensitive_details else _mask_value(record.account_number)
    iban = record.iban if include_sensitive_details else _mask_value(record.iban)
    swift_code = record.swift_code if include_sensitive_details else _mask_value(record.swift_code)
    routing_number = record.routing_number if include_sensitive_details else _mask_value(record.routing_number)

    return {
        "configured": _has_bank_details(record),
        "title": title,
        "direction": direction,
        "account_label": record.account_label,
        "beneficiary_name": record.beneficiary_name,
        "bank_name": record.bank_name,
        "branch_name": record.branch_name,
        "account_number": account_number,
        "iban": iban,
        "swift_code": swift_code,
        "routing_number": routing_number,
        "currency": record.currency or settings.default_currency,
        "support_email": record.support_email,
        "support_phone": record.support_phone,
        "remittance_reference_prefix": _clean_reference_prefix(record.remittance_reference_prefix),
        "reference_value": reference_value,
        "reference_help": reference_help,
        "instructions": record.instructions or fallback_instructions,
        "details_visible": include_sensitive_details,
    }


def build_supplier_payout_instruction(supplier_id: int, db: Session) -> dict[str, Any]:
    reference_value = build_transfer_reference(
        db,
        kind="supplier_payout",
        entity_id=supplier_id,
    )
    return _serialize_bank_instruction(
        get_active_finance_bank_settings(db),
        title="Payout Reference Guide",
        direction="incoming_payout",
        reference_value=reference_value,
        reference_help="Quote this reference when asking Zozi finance to trace a supplier payout.",
        include_sensitive_details=False,
        fallback_instructions="Use the payout reference on support tickets or bank trace requests so finance can reconcile your transfer quickly.",
    )


def build_logistics_cod_remittance_instruction(partner_id: int, db: Session) -> dict[str, Any]:
    reference_value = build_transfer_reference(
        db,
        kind="cod_remittance",
        entity_id=partner_id,
    )
    return _serialize_bank_instruction(
        get_active_finance_bank_settings(db),
        title="COD Remittance Instructions",
        direction="outbound_remittance",
        reference_value=reference_value,
        reference_help="Include this remittance reference on every COD bank transfer so Zozi can match the deposit to your settlement ledger.",
        include_sensitive_details=True,
        fallback_instructions="Configure Zozi treasury bank details before asking logistics partners to remit collected COD balances.",
    )


class TransferExportProvider(Protocol):
    key: str
    name: str
    description: str
    supports_direct_execution: bool

    def build_export_payload(
        self,
        export_type: TransferExportType,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        ...

    def execute_transfer_batch(
        self,
        export_type: DispatchableTransferType,
        db: Session,
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        ...


class ManualCsvTransferProvider:
    key = "manual_csv"
    name = "Manual CSV Transfer"
    description = "Creates CSV transfer files for bank portal upload or finance operations review."
    supports_direct_execution = False

    def build_export_payload(
        self,
        export_type: TransferExportType,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        if export_type == "supplier-payout-transfers":
            return self._build_supplier_payout_export(db)
        if export_type == "logistics-payout-transfers":
            return self._build_logistics_payout_export(db)
        if export_type == "cod-remittance-transfers":
            return self._build_cod_remittance_export(db)
        raise HTTPException(status_code=404, detail="Unknown transfer export type")

    def execute_transfer_batch(
        self,
        export_type: DispatchableTransferType,
        db: Session,
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        raise HTTPException(
            status_code=422,
            detail="The manual_csv provider creates bank-upload files only and cannot dispatch transfers directly.",
        )

    def _build_supplier_payout_export(
        self,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        payouts = (
            db.query(Payout)
            .filter(Payout.status == "processing")
            .order_by(Payout.created_at.asc(), Payout.id.asc())
            .all()
        )
        bank = get_active_finance_bank_settings(db)

        # Pre-load all verified supplier bank accounts for payouts in-flight
        supplier_ids = {int(p.supplier_id) for p in payouts if p.supplier_id}
        recipient_map: dict[int, SupplierBankAccount] = {}
        if supplier_ids:
            records = (
                db.query(SupplierBankAccount)
                .filter(
                    SupplierBankAccount.supplier_id.in_(supplier_ids),
                    SupplierBankAccount.verification_status == "verified",
                )
                .all()
            )
            recipient_map = {int(r.supplier_id): r for r in records}

        rows = []
        for payout in payouts:
            supplier_id = int(payout.supplier_id or 0)
            recipient = recipient_map.get(supplier_id)
            if recipient:
                recipient_status = "verified"
                recipient_note = ""
            else:
                recipient_status = "missing_in_zozi"
                recipient_note = "Supplier has not submitted a verified bank account. Add via /supplier/bank-account."

            rows.append({
                "payout_id": payout.id,
                "supplier_id": supplier_id,
                "supplier_username": getattr(payout.supplier, "username", None),
                "amount": float(round_money(to_decimal(payout.amount or 0))),
                "currency": (recipient.currency if recipient else None) or getattr(bank, "currency", None) or settings.default_currency,
                "reference": payout.reference or build_transfer_reference(
                    db,
                    kind="supplier_payout",
                    entity_id=supplier_id,
                    record_id=int(payout.id),
                ),
                "method": payout.method or "bank",
                "status": payout.status,
                "created_at": payout.created_at.isoformat() if payout.created_at else "",
                "processed_at": payout.processed_at.isoformat() if payout.processed_at else "",
                "source_account_label": getattr(bank, "account_label", None) or "Zozi treasury",
                "source_bank_name": getattr(bank, "bank_name", None) or "",
                # Recipient bank details (from verified SupplierBankAccount or empty)
                "recipient_beneficiary_name": recipient.beneficiary_name if recipient else "",
                "recipient_bank_name": recipient.bank_name if recipient else "",
                "recipient_branch_name": recipient.branch_name if recipient else "",
                "recipient_account_number": recipient.account_number if recipient else "",
                "recipient_iban": recipient.iban if recipient else "",
                "recipient_swift_code": recipient.swift_code if recipient else "",
                "recipient_routing_number": recipient.routing_number if recipient else "",
                "recipient_bank_country": recipient.bank_country if recipient else "",
                "recipient_account_status": recipient_status,
                "ops_note": recipient_note,
                "notes": payout.notes or "",
            })

        fieldnames = [
            "payout_id",
            "supplier_id",
            "supplier_username",
            "amount",
            "currency",
            "reference",
            "method",
            "status",
            "created_at",
            "processed_at",
            "source_account_label",
            "source_bank_name",
            "recipient_beneficiary_name",
            "recipient_bank_name",
            "recipient_branch_name",
            "recipient_account_number",
            "recipient_iban",
            "recipient_swift_code",
            "recipient_routing_number",
            "recipient_bank_country",
            "recipient_account_status",
            "ops_note",
            "notes",
        ]
        return rows, fieldnames, f"supplier_payout_transfers_{self.key}.csv", {
            "resource_type": "supplier_payout_transfers",
            "details": {
                "count": len(rows),
                "provider": self.key,
                "with_recipient_details": sum(1 for r in rows if r["recipient_account_status"] == "verified"),
            },
        }

    def _build_logistics_payout_export(
        self,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        payouts = (
            db.query(LogisticsPartnerPayout)
            .filter(LogisticsPartnerPayout.status == "processing")
            .order_by(LogisticsPartnerPayout.created_at.asc(), LogisticsPartnerPayout.id.asc())
            .all()
        )
        bank = get_active_finance_bank_settings(db)

        partner_ids = {int(p.partner_id) for p in payouts if p.partner_id}
        recipient_map: dict[int, LogisticsPartnerBankAccount] = {}
        if partner_ids:
            records = (
                db.query(LogisticsPartnerBankAccount)
                .filter(
                    LogisticsPartnerBankAccount.partner_id.in_(partner_ids),
                    LogisticsPartnerBankAccount.verification_status == "verified",
                )
                .all()
            )
            recipient_map = {int(r.partner_id): r for r in records}

        rows = []
        for payout in payouts:
            partner_id = int(payout.partner_id or 0)
            recipient = recipient_map.get(partner_id)
            if recipient:
                recipient_status = "verified"
                recipient_note = ""
            else:
                recipient_status = "missing_in_zozi"
                recipient_note = "Partner has not submitted a verified bank account. Add via /logistics-partners/me/bank-account."

            rows.append({
                "payout_id": payout.id,
                "partner_id": partner_id,
                "partner_name": getattr(payout.partner, "name", None),
                "partner_code": getattr(payout.partner, "code", None),
                "amount": float(round_money(to_decimal(payout.amount or 0))),
                "currency": (recipient.currency if recipient else None) or getattr(bank, "currency", None) or settings.default_currency,
                "reference": payout.reference or build_transfer_reference(
                    db,
                    kind="logistics_payout",
                    entity_id=partner_id,
                    record_id=int(payout.id),
                ),
                "method": payout.method or "bank",
                "status": payout.status,
                "created_at": payout.created_at.isoformat() if payout.created_at else "",
                "processed_at": payout.processed_at.isoformat() if payout.processed_at else "",
                "source_account_label": getattr(bank, "account_label", None) or "Zozi treasury",
                "source_bank_name": getattr(bank, "bank_name", None) or "",
                "recipient_beneficiary_name": recipient.beneficiary_name if recipient else "",
                "recipient_bank_name": recipient.bank_name if recipient else "",
                "recipient_branch_name": recipient.branch_name if recipient else "",
                "recipient_account_number": recipient.account_number if recipient else "",
                "recipient_iban": recipient.iban if recipient else "",
                "recipient_swift_code": recipient.swift_code if recipient else "",
                "recipient_routing_number": recipient.routing_number if recipient else "",
                "recipient_bank_country": recipient.bank_country if recipient else "",
                "recipient_account_status": recipient_status,
                "ops_note": recipient_note,
                "notes": payout.notes or "",
            })

        fieldnames = [
            "payout_id",
            "partner_id",
            "partner_name",
            "partner_code",
            "amount",
            "currency",
            "reference",
            "method",
            "status",
            "created_at",
            "processed_at",
            "source_account_label",
            "source_bank_name",
            "recipient_beneficiary_name",
            "recipient_bank_name",
            "recipient_branch_name",
            "recipient_account_number",
            "recipient_iban",
            "recipient_swift_code",
            "recipient_routing_number",
            "recipient_bank_country",
            "recipient_account_status",
            "ops_note",
            "notes",
        ]
        return rows, fieldnames, f"logistics_payout_transfers_{self.key}.csv", {
            "resource_type": "logistics_payout_transfers",
            "details": {
                "count": len(rows),
                "provider": self.key,
                "with_recipient_details": sum(1 for r in rows if r["recipient_account_status"] == "verified"),
            },
        }

    def _build_cod_remittance_export(
        self,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        settlements = (
            db.query(LogisticsSettlement)
            .filter(LogisticsSettlement.cod_remittance_status.in_(["pending", "partial"]))
            .order_by(LogisticsSettlement.partner_id.asc(), LogisticsSettlement.id.asc())
            .all()
        )
        bank = get_active_finance_bank_settings(db)
        aggregated: dict[int, dict[str, Any]] = {}

        for settlement in settlements:
            partner_id = int(settlement.partner_id)
            amount_due = round_money(
                to_decimal(settlement.cod_collected or 0)
                - to_decimal(settlement.cod_retained or 0)
                - to_decimal(settlement.cod_remitted or 0)
            )
            if amount_due <= Decimal("0"):
                continue

            bucket = aggregated.setdefault(
                partner_id,
                {
                    "partner_id": partner_id,
                    "partner_name": getattr(settlement.partner, "name", None),
                    "partner_code": getattr(settlement.partner, "code", None),
                    "currency": settlement.currency or getattr(bank, "currency", None) or settings.default_currency,
                    "outstanding_cod_due": Decimal("0"),
                    "settlement_ids": [],
                    "order_ids": [],
                },
            )
            bucket["outstanding_cod_due"] = round_money(bucket["outstanding_cod_due"] + amount_due)
            bucket["settlement_ids"].append(str(settlement.id))
            bucket["order_ids"].append(str(settlement.order_id))

        rows = [
            {
                "partner_id": partner_id,
                "partner_name": payload["partner_name"],
                "partner_code": payload["partner_code"],
                "outstanding_cod_due": float(round_money(payload["outstanding_cod_due"])),
                "currency": payload["currency"],
                "reference": build_transfer_reference(
                    db,
                    kind="cod_remittance",
                    entity_id=partner_id,
                ),
                "settlement_ids": ",".join(payload["settlement_ids"]),
                "order_ids": ",".join(payload["order_ids"]),
                "beneficiary_name": getattr(bank, "beneficiary_name", None) or "",
                "bank_name": getattr(bank, "bank_name", None) or "",
                "branch_name": getattr(bank, "branch_name", None) or "",
                "account_number": getattr(bank, "account_number", None) or "",
                "iban": getattr(bank, "iban", None) or "",
                "swift_code": getattr(bank, "swift_code", None) or "",
                "routing_number": getattr(bank, "routing_number", None) or "",
                "support_email": getattr(bank, "support_email", None) or "",
                "support_phone": getattr(bank, "support_phone", None) or "",
                "instructions": getattr(bank, "instructions", None)
                or "Use the generated remittance reference on the bank transfer so Zozi can reconcile COD correctly.",
            }
            for partner_id, payload in aggregated.items()
        ]
        fieldnames = [
            "partner_id",
            "partner_name",
            "partner_code",
            "outstanding_cod_due",
            "currency",
            "reference",
            "settlement_ids",
            "order_ids",
            "beneficiary_name",
            "bank_name",
            "branch_name",
            "account_number",
            "iban",
            "swift_code",
            "routing_number",
            "support_email",
            "support_phone",
            "instructions",
        ]
        return rows, fieldnames, f"cod_remittance_transfers_{self.key}.csv", {
            "resource_type": "cod_remittance_transfers",
            "details": {"count": len(rows), "provider": self.key},
        }


def _treasury_dispatch_ready(record: FinanceBankAccount | None) -> bool:
    if record is None or not bool(getattr(record, "is_active", True)):
        return False
    return bool(
        getattr(record, "beneficiary_name", None)
        and getattr(record, "bank_name", None)
        and (getattr(record, "account_number", None) or getattr(record, "iban", None))
    )


def _provider_missing_requirements(provider_key: str, db: Session | None = None) -> list[str]:
    if provider_key == ManualCsvTransferProvider.key:
        return []

    if provider_key == ConfiguredBankApiTransferProvider.key:
        missing: list[str] = []
        if not settings.bank_api_enabled:
            missing.append("Enable BANK_API_ENABLED")
        if not settings.bank_api_base_url.strip():
            missing.append("Set BANK_API_BASE_URL")
        if not settings.bank_api_batch_path.strip():
            missing.append("Set BANK_API_BATCH_PATH")
        if not settings.bank_api_auth_token.strip():
            missing.append("Set BANK_API_AUTH_TOKEN")
        if not settings.bank_api_source_account_id.strip():
            missing.append("Set BANK_API_SOURCE_ACCOUNT_ID")
        if db is not None and not _treasury_dispatch_ready(get_active_finance_bank_settings(db)):
            missing.append("Configure active treasury bank details in Finance Bank Settings")
        return missing

    if provider_key == StripeConnectTransferProvider.key:
        missing: list[str] = []
        if not settings.stripe_secret_key.strip():
            missing.append("Set STRIPE_SECRET_KEY")
        return missing

    return ["Unknown transfer provider"]


def _provider_is_configured(provider_key: str, db: Session | None = None) -> bool:
    return len(_provider_missing_requirements(provider_key, db)) == 0


def test_configured_bank_api_connection(db: Session) -> dict[str, Any]:
    endpoint = None
    if settings.bank_api_base_url.strip() and settings.bank_api_batch_path.strip():
        endpoint = f"{settings.bank_api_base_url.rstrip('/')}/{settings.bank_api_batch_path.lstrip('/')}"

    missing_requirements = _provider_missing_requirements(ConfiguredBankApiTransferProvider.key, db)
    if missing_requirements:
        return {
            "provider": ConfiguredBankApiTransferProvider.key,
            "endpoint": endpoint,
            "ok": False,
            "reachable": False,
            "status_code": None,
            "detail": "Complete the treasury and bank API requirements before testing the connection.",
            "missing_requirements": missing_requirements,
        }

    headers = {"Authorization": f"Bearer {settings.bank_api_auth_token}"}

    try:
        response = requests.request(
            "OPTIONS",
            cast(str, endpoint),
            headers=headers,
            timeout=settings.bank_api_timeout_seconds,
        )
    except requests.RequestException as exc:
        return {
            "provider": ConfiguredBankApiTransferProvider.key,
            "endpoint": endpoint,
            "ok": False,
            "reachable": False,
            "status_code": None,
            "detail": f"Bank API endpoint could not be reached: {exc}",
            "missing_requirements": [],
        }

    reachable = True
    ok = response.status_code in {200, 201, 202, 204, 401, 403, 404, 405}
    detail = (
        f"Bank API endpoint responded with HTTP {response.status_code}."
        if ok
        else f"Bank API endpoint responded with HTTP {response.status_code}; investigate before live dispatch."
    )

    return {
        "provider": ConfiguredBankApiTransferProvider.key,
        "endpoint": endpoint,
        "ok": ok,
        "reachable": reachable,
        "status_code": response.status_code,
        "detail": detail,
        "missing_requirements": [],
    }


def _build_dispatch_manifest(
    export_type: DispatchableTransferType,
    rows: list[dict[str, Any]],
    bank: FinanceBankAccount | None,
) -> dict[str, Any]:
    kind_label = "supplier" if export_type == "supplier-payout-transfers" else "logistics"
    batch_reference = f"{_clean_reference_prefix(getattr(bank, 'remittance_reference_prefix', None))}-BATCH-{kind_label[:3].upper()}-{uuid4().hex[:10].upper()}"
    dispatchable: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for row in rows:
        record_id = int(row.get("payout_id") or 0)
        recipient_status = str(row.get("recipient_account_status") or "").strip() or "missing_in_zozi"
        if recipient_status != "verified":
            skipped.append({
                "record_id": record_id,
                "reference": row.get("reference"),
                "reason": row.get("ops_note") or f"Recipient bank account is {recipient_status}.",
            })
            continue

        dispatchable.append({
            "record_id": record_id,
            "reference": row.get("reference"),
            "amount": row.get("amount"),
            "currency": row.get("currency") or settings.default_currency,
            "beneficiary_name": row.get("recipient_beneficiary_name"),
            "bank_name": row.get("recipient_bank_name"),
            "branch_name": row.get("recipient_branch_name"),
            "account_number": row.get("recipient_account_number"),
            "iban": row.get("recipient_iban"),
            "swift_code": row.get("recipient_swift_code"),
            "routing_number": row.get("recipient_routing_number"),
            "bank_country": row.get("recipient_bank_country"),
            "metadata": {
                "transfer_kind": kind_label,
                "source_account_label": row.get("source_account_label"),
                "source_bank_name": row.get("source_bank_name"),
                "notes": row.get("notes") or "",
            },
        })

    return {
        "export_type": export_type,
        "batch_reference": batch_reference,
        "source_account": {
            "account_label": getattr(bank, "account_label", None),
            "beneficiary_name": getattr(bank, "beneficiary_name", None),
            "bank_name": getattr(bank, "bank_name", None),
            "currency": getattr(bank, "currency", None) or settings.default_currency,
            "source_account_id": settings.bank_api_source_account_id or None,
        },
        "dispatchable_transfers": dispatchable,
        "skipped_transfers": skipped,
        "dispatchable_count": len(dispatchable),
        "skipped_count": len(skipped),
        "total_candidates": len(rows),
    }


def _mark_dispatch_submitted(
    export_type: DispatchableTransferType,
    db: Session,
    *,
    dispatchable_transfers: list[dict[str, Any]],
    provider_key: str,
    provider_batch_id: str,
    provider_status: str,
) -> None:
    """Persist provider dispatch metadata on payout rows for later reconciliation/UI visibility."""
    payout_ids = [int(item.get("record_id", 0)) for item in dispatchable_transfers if int(item.get("record_id", 0))]
    if not payout_ids:
        return

    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    note_line = f"Dispatched via {provider_key} batch {provider_batch_id}"

    if export_type == "supplier-payout-transfers":
        rows = db.query(Payout).filter(Payout.id.in_(payout_ids)).all()
    else:
        rows = db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.id.in_(payout_ids)).all()

    for row in rows:
        row.provider = provider_key
        row.provider_payment_id = provider_batch_id
        row.provider_status = provider_status
        row.last_provider_sync_at = synced_at
        existing_notes = (row.notes or "").strip()
        if note_line not in existing_notes:
            row.notes = f"{existing_notes}\n{note_line}".strip() if existing_notes else note_line

    db.flush()


class ConfiguredBankApiTransferProvider:
    key = "configured_bank_api"
    name = "Configured Bank API"
    description = "Submits supplier or logistics payout batches to a configured treasury or bank API using secret-managed credentials."
    supports_direct_execution = True

    def __init__(self) -> None:
        self._csv_provider = ManualCsvTransferProvider()

    def build_export_payload(
        self,
        export_type: TransferExportType,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        rows, fieldnames, filename, audit_meta = self._csv_provider.build_export_payload(export_type, db)
        return rows, fieldnames, filename.replace("manual_csv", self.key), {
            **audit_meta,
            "details": {**audit_meta["details"], "provider": self.key},
        }

    def execute_transfer_batch(
        self,
        export_type: DispatchableTransferType,
        db: Session,
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        rows, _fieldnames, _filename, _audit_meta = self._csv_provider.build_export_payload(export_type, db)
        bank = get_active_finance_bank_settings(db)
        manifest = _build_dispatch_manifest(export_type, rows, bank)
        base_result = {
            "provider": self.key,
            "provider_name": self.name,
            "supports_direct_execution": True,
            "configured": _provider_is_configured(self.key, db),
            **manifest,
        }

        if dry_run:
            return {
                **base_result,
                "status": "dry_run",
                "submitted": False,
                "preview": manifest["dispatchable_transfers"][:10],
            }

        if not settings.bank_api_enabled:
            raise HTTPException(status_code=503, detail="BANK_API_ENABLED must be true before live payout dispatch is allowed.")
        if not settings.bank_api_base_url.strip() or not settings.bank_api_batch_path.strip():
            raise HTTPException(status_code=503, detail="BANK_API_BASE_URL and BANK_API_BATCH_PATH must be configured for live payout dispatch.")
        if not settings.bank_api_auth_token.strip():
            raise HTTPException(status_code=503, detail="BANK_API_AUTH_TOKEN must be configured for live payout dispatch.")
        if not settings.bank_api_source_account_id.strip():
            raise HTTPException(status_code=503, detail="BANK_API_SOURCE_ACCOUNT_ID must be configured for live payout dispatch.")
        if not _treasury_dispatch_ready(bank):
            raise HTTPException(status_code=503, detail="Finance Bank Settings must include an active beneficiary, bank name, and account number or IBAN before live payout dispatch is allowed.")
        if manifest["dispatchable_count"] == 0:
            return {
                **base_result,
                "status": "no_dispatchable_transfers",
                "submitted": False,
                "preview": [],
            }

        endpoint = f"{settings.bank_api_base_url.rstrip('/')}/{settings.bank_api_batch_path.lstrip('/')}"
        payload = {
            "batch_reference": manifest["batch_reference"],
            "source_account": manifest["source_account"],
            "transfers": manifest["dispatchable_transfers"],
            "metadata": {
                "app": settings.app_name,
                "export_type": export_type,
                "currency": manifest["source_account"]["currency"],
            },
        }
        headers = {
            "Authorization": f"Bearer {settings.bank_api_auth_token}",
            "Content-Type": "application/json",
            "Idempotency-Key": manifest["batch_reference"],
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=settings.bank_api_timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(status_code=502, detail=f"Bank API dispatch failed: {exc}") from exc

        response_body: dict[str, Any]
        try:
            response_body = response.json() if response.content else {}
        except ValueError:
            response_body = {}

        provider_batch_id = response_body.get("batch_id") or response_body.get("id") or manifest["batch_reference"]
        provider_status = response_body.get("status") or "submitted"
        _mark_dispatch_submitted(
            export_type,
            db,
            dispatchable_transfers=manifest["dispatchable_transfers"],
            provider_key=self.key,
            provider_batch_id=provider_batch_id,
            provider_status=provider_status,
        )

        return {
            **base_result,
            "status": "submitted",
            "submitted": True,
            "provider_batch_id": provider_batch_id,
            "provider_status": provider_status,
            "provider_http_status": response.status_code,
            "preview": [],
        }


class StripeConnectTransferProvider:
    """Pays out supplier balances via Stripe Connect transfers.

    For each ``processing`` Payout the provider will:
    1. Look up a verified SupplierBankAccount for the supplier.
    2. Optionally auto-create a Stripe Express account if none exists yet
       (controlled by ``STRIPE_CONNECT_AUTO_CREATE_ACCOUNTS``).
    3. Issue a ``stripe.Transfer`` to the connected account.
    4. Persist the Stripe IDs back onto the Payout and SupplierBankAccount rows.
    """

    key = "stripe_connect"
    name = "Stripe Connect"
    description = (
        "Disburses payouts directly to supplier Stripe Connect accounts. "
        "Supports automatic account creation when STRIPE_CONNECT_AUTO_CREATE_ACCOUNTS is enabled."
    )
    supports_direct_execution = True

    def __init__(self) -> None:
        self._csv_provider = ManualCsvTransferProvider()

    def build_export_payload(
        self,
        export_type: TransferExportType,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        rows, fieldnames, filename, audit_meta = self._csv_provider.build_export_payload(export_type, db)
        return rows, fieldnames, filename.replace("manual_csv", self.key), {
            **audit_meta,
            "details": {**audit_meta["details"], "provider": self.key},
        }

    def execute_transfer_batch(
        self,
        export_type: DispatchableTransferType,
        db: Session,
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        if export_type != "supplier-payout-transfers":
            raise HTTPException(status_code=400, detail="Stripe Connect only supports supplier payout dispatch.")

        if not settings.stripe_secret_key or not settings.stripe_secret_key.strip():
            raise HTTPException(status_code=503, detail="STRIPE_SECRET_KEY must be configured for Stripe Connect payout dispatch.")

        stripe.api_key = settings.stripe_secret_key.strip()
        if hasattr(settings, "stripe_api_version") and settings.stripe_api_version:
            stripe.api_version = settings.stripe_api_version

        # Fetch processing payouts that haven't been dispatched yet
        payouts = (
            db.query(Payout)
            .filter(
                Payout.status == "processing",
                Payout.method == "bank",
                Payout.provider.is_(None),
            )
            .all()
        )

        base_result: dict[str, Any] = {
            "provider": self.key,
            "provider_name": self.name,
            "supports_direct_execution": True,
            "configured": _provider_is_configured(self.key, db),
            "dispatchable_count": len(payouts),
            "batch_reference": f"STRIPE-CONNECT-{uuid4().hex[:10].upper()}",
        }

        if dry_run:
            preview = []
            for payout in payouts[:10]:
                bank = (
                    db.query(SupplierBankAccount)
                    .filter(
                        SupplierBankAccount.supplier_id == payout.supplier_id,
                        SupplierBankAccount.verification_status == "verified",
                    )
                    .first()
                )
                preview.append({
                    "reference": payout.reference,
                    "supplier_id": payout.supplier_id,
                    "amount": float(payout.amount),
                    "has_bank_account": bank is not None,
                })
            return {
                **base_result,
                "status": "dry_run",
                "submitted": False,
                "preview": preview,
            }

        submitted_count = 0
        failed_count = 0
        skipped_count = 0
        failed_references: list[str] = []

        for payout in payouts:
            try:
                bank = (
                    db.query(SupplierBankAccount)
                    .filter(
                        SupplierBankAccount.supplier_id == payout.supplier_id,
                        SupplierBankAccount.verification_status == "verified",
                    )
                    .first()
                )
                if bank is None:
                    skipped_count += 1
                    continue

                # Resolve or create the Stripe Account
                connect_account_id: str | None = bank.provider_recipient_id if bank.provider == "stripe_connect" else None

                if not connect_account_id and settings.stripe_connect_auto_create_accounts:
                    country = getattr(settings, "stripe_connect_default_country", "US") or "US"
                    business_url = getattr(settings, "stripe_connect_default_business_url", "") or ""
                    tos_ip = getattr(settings, "stripe_connect_tos_acceptance_ip", "127.0.0.1") or "127.0.0.1"
                    create_kwargs: dict[str, Any] = {
                        "type": "express",
                        "country": country,
                        "capabilities": {"transfers": {"requested": True}},
                        "metadata": {
                            "supplier_id": str(payout.supplier_id),
                            "beneficiary_name": bank.beneficiary_name or "",
                            "zozi_reference": payout.reference,
                        },
                        "tos_acceptance": {"ip": tos_ip, "date": int(datetime.now(timezone.utc).timestamp())},
                    }
                    if business_url:
                        create_kwargs["business_profile"] = {"url": business_url}
                    acct = stripe.Account.create(**create_kwargs)
                    connect_account_id = acct.id

                    # Activate transfers capability
                    stripe.Account.modify(
                        connect_account_id,
                        capabilities={"transfers": {"requested": True}},
                    )

                    bank.provider = "stripe_connect"
                    bank.provider_recipient_id = connect_account_id
                    bank.provider_status = "active"
                    db.add(bank)

                if not connect_account_id:
                    skipped_count += 1
                    continue

                currency = (bank.currency or "usd").lower()
                amount_cents = int(round(float(payout.amount) * 100))
                transfer = stripe.Transfer.create(
                    amount=amount_cents,
                    currency=currency,
                    destination=connect_account_id,
                    metadata={
                        "payout_reference": payout.reference,
                        "supplier_id": str(payout.supplier_id),
                    },
                    transfer_group=base_result["batch_reference"],
                )

                payout.provider = "stripe_connect"
                payout.provider_recipient_id = connect_account_id
                payout.provider_transfer_id = transfer.id
                payout.provider_status = getattr(transfer, "status", "pending")
                payout.last_provider_sync_at = datetime.now(timezone.utc)
                db.add(payout)
                submitted_count += 1

            except Exception:
                failed_count += 1
                failed_references.append(payout.reference)

        db.commit()

        return {
            **base_result,
            "status": "submitted",
            "submitted": True,
            "submitted_count": submitted_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "failed_references": failed_references,
        }


_TRANSFER_PROVIDERS: dict[str, TransferExportProvider] = {
    ManualCsvTransferProvider.key: ManualCsvTransferProvider(),
    ConfiguredBankApiTransferProvider.key: ConfiguredBankApiTransferProvider(),
    StripeConnectTransferProvider.key: StripeConnectTransferProvider(),
}


def get_default_transfer_provider() -> str:
    configured = str(getattr(settings, "payout_transfer_provider", ManualCsvTransferProvider.key) or "").strip().lower()
    if configured in _TRANSFER_PROVIDERS:
        return configured
    return ManualCsvTransferProvider.key


def list_transfer_export_providers(db: Session | None = None) -> list[dict[str, Any]]:
    return [
        {
            "key": provider.key,
            "name": provider.name,
            "description": provider.description,
            "supports_direct_execution": provider.supports_direct_execution,
            "configured": _provider_is_configured(provider.key, db),
            "missing_requirements": _provider_missing_requirements(provider.key, db),
            "is_default": provider.key == get_default_transfer_provider(),
        }
        for provider in _TRANSFER_PROVIDERS.values()
    ]


def build_transfer_export_payload(
    export_type: TransferExportType,
    *,
    db: Session,
    provider: str = ManualCsvTransferProvider.key,
) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
    adapter = _TRANSFER_PROVIDERS.get(provider)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Unknown transfer provider")
    return adapter.build_export_payload(export_type, db)


def execute_transfer_batch(
    export_type: DispatchableTransferType,
    *,
    db: Session,
    provider: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    adapter_key = provider or get_default_transfer_provider()
    adapter = _TRANSFER_PROVIDERS.get(adapter_key)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Unknown transfer provider")
    if not adapter.supports_direct_execution:
        raise HTTPException(status_code=422, detail="Selected transfer provider does not support direct execution")
    return adapter.execute_transfer_batch(export_type, db, dry_run=dry_run)


# ── Country-specific payout settings ─────────────────────────────────────────

def get_country_payout_settings(country_code: str, db: Session) -> dict[str, Any]:
    """Read payout settings from a country's ``CountryConfig.payout_settings_json``.

    Returns default values if the country or its settings are not configured.
    """
    from services.logistics_partner_pricing import normalize_country_code

    code = normalize_country_code(country_code)
    if not code:
        return _default_payout_settings()

    country = db.query(CountryConfig).filter(
        CountryConfig.code == code,
        CountryConfig.is_active == True,
    ).first()
    if not country:
        return _default_payout_settings()

    raw = country.payout_settings_json
    if not raw:
        return _default_payout_settings()
    try:
        settings_dict = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return _default_payout_settings()

    if not isinstance(settings_dict, dict):
        return _default_payout_settings()

    return {
        "minimum_payout_amount": float(settings_dict.get("minimum_payout_amount", 10)),
        "payout_schedule": str(settings_dict.get("payout_schedule", "weekly")).lower(),
        "payout_day": str(settings_dict.get("payout_day", "sunday")).lower(),
        "batch_size": int(settings_dict.get("batch_size", 50)),
        "currency": str(settings_dict.get("currency") or "").upper() or None,
        "country_code": code,
    }


def _default_payout_settings() -> dict[str, Any]:
    return {
        "minimum_payout_amount": 10.0,
        "payout_schedule": "weekly",
        "payout_day": "sunday",
        "batch_size": 50,
        "currency": None,
        "country_code": None,
    }

