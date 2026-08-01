from __future__ import annotations

import logging
from typing import Any, Iterable, cast

from sqlalchemy.orm import selectinload

from db.database import get_service_session
from models import Order, OrderItem, ReturnRequest, Shipment, User
from utils.background_jobs import enqueue_job
from utils.config import settings
from utils.email_service import send_email
from utils.order_tracking import order_status_label, shipment_status_label

logger = logging.getLogger(__name__)


def _order_link(order_id: int) -> str:
    return f"{settings.frontend_url.rstrip('/')}/orders/{order_id}"


def _tracking_link(order_id: int) -> str:
    return f"{settings.frontend_url.rstrip('/')}/tracking/{order_id}"


def _first_name(user: User | None) -> str:
    if user is None:
        return "there"
    username = str(getattr(user, "username", "") or "").strip()
    return username.split("_")[0].title() if username else "there"


def _order_items_summary(items: Iterable[OrderItem]) -> str:
    labels: list[str] = []
    for item in items:
        product = getattr(item, "product", None)
        name = str(getattr(product, "name", "Item") or "Item")
        quantity = int(getattr(item, "quantity", 0) or 0)
        labels.append(f"{name} x{quantity}")
    return ", ".join(labels[:4]) if labels else "your items"


def _send_order_created_email(order_id: int) -> dict[str, Any]:
    with get_service_session() as db:
        order = (
            db.query(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product), selectinload(Order.user))
            .filter(Order.id == order_id)
            .first()
        )
        if order is None or order.user is None or not getattr(order.user, "email", None):
            return {"order_id": order_id, "sent": False, "reason": "missing-order-or-user"}

        payment_method = str(getattr(order, "payment_method", "card") or "card").lower()
        status = str(getattr(order, "status", "pending") or "pending")
        subject = (
            f"ZOZI order #{order.id} confirmed"
            if payment_method == "cod" or status == "confirmed"
            else f"ZOZI order #{order.id} received"
        )
        body = (
            "<p>Your order has been confirmed and will be prepared for dispatch.</p>"
            if payment_method == "cod" or status == "confirmed"
            else "<p>Your order has been created and is awaiting payment confirmation.</p>"
        )
        html = (
            f"<h2>Hi {_first_name(order.user)},</h2>"
            f"<p>Thank you for shopping with ZOZI.</p>"
            f"<p><strong>Order:</strong> #{order.id}</p>"
            f"<p><strong>Items:</strong> {_order_items_summary(order.items)}</p>"
            f"<p><strong>Total:</strong> {getattr(order, 'total_amount', 0)}</p>"
            f"<p><strong>Payment method:</strong> {payment_method.upper()}</p>"
            f"{body}"
            f"<p><a href=\"{_order_link(cast(int, order.id))}\">View order details</a></p>"
        )
        send_email(str(order.user.email), subject, html, purpose="transactional")
        return {"order_id": order_id, "sent": True}


def _send_payment_email(order_id: int, *, outcome: str, provider: str, message: str | None = None) -> dict[str, Any]:
    with get_service_session() as db:
        order = db.query(Order).options(selectinload(Order.user)).filter(Order.id == order_id).first()
        if order is None or order.user is None or not getattr(order.user, "email", None):
            return {"order_id": order_id, "sent": False, "reason": "missing-order-or-user"}

        if outcome == "confirmed":
            subject = f"Payment confirmed for order #{order.id}"
            detail = message or "Your payment was successful and we are preparing your order."
        else:
            subject = f"Payment failed for order #{order.id}"
            detail = message or "We could not confirm your payment. Please try again."

        html = (
            f"<h2>Hi {_first_name(order.user)},</h2>"
            f"<p><strong>Order:</strong> #{order.id}</p>"
            f"<p><strong>Provider:</strong> {provider.title()}</p>"
            f"<p>{detail}</p>"
            f"<p><a href=\"{_order_link(cast(int, order.id))}\">Open your order</a></p>"
        )
        send_email(str(order.user.email), subject, html, purpose="transactional")
        return {"order_id": order_id, "sent": True, "outcome": outcome}


def _send_refund_email(order_id: int, *, source: str) -> dict[str, Any]:
    with get_service_session() as db:
        order = db.query(Order).options(selectinload(Order.user)).filter(Order.id == order_id).first()
        if order is None or order.user is None or not getattr(order.user, "email", None):
            return {"order_id": order_id, "sent": False, "reason": "missing-order-or-user"}
        html = (
            f"<h2>Refund processed for order #{order.id}</h2>"
            f"<p>Hi {_first_name(order.user)}, your refund has been processed via {source.title()}.</p>"
            f"<p><a href=\"{_order_link(cast(int, order.id))}\">View order details</a></p>"
        )
        send_email(str(order.user.email), f"Refund processed for order #{order.id}", html, purpose="notification")
        return {"order_id": order_id, "sent": True, "source": source}


def _send_order_status_email(order_id: int, *, status: str) -> dict[str, Any]:
    with get_service_session() as db:
        order = db.query(Order).options(selectinload(Order.user)).filter(Order.id == order_id).first()
        if order is None or order.user is None or not getattr(order.user, "email", None):
            return {"order_id": order_id, "sent": False, "reason": "missing-order-or-user"}
        label = order_status_label(status, [], [])
        html = (
            f"<h2>Order #{order.id} update</h2>"
            f"<p>Hi {_first_name(order.user)}, your order status is now <strong>{label}</strong>.</p>"
            f"<p><a href=\"{_order_link(cast(int, order.id))}\">Review your order</a></p>"
        )
        send_email(str(order.user.email), f"Order #{order.id} status: {label}", html, purpose="notification")
        return {"order_id": order_id, "sent": True, "status": status}


def _send_return_email(return_id: int, *, event_kind: str) -> dict[str, Any]:
    with get_service_session() as db:
        req = db.query(ReturnRequest).options(selectinload(ReturnRequest.order).selectinload(Order.user)).filter(ReturnRequest.id == return_id).first()
        order = getattr(req, "order", None)
        user = getattr(order, "user", None)
        if req is None or order is None or user is None or not getattr(user, "email", None):
            return {"return_id": return_id, "sent": False, "reason": "missing-return-or-user"}

        if event_kind == "created":
            subject = f"Return request received for order #{order.id}"
            detail = f"We received your {getattr(req, 'intent', 'return')} request and the team will review it shortly."
        else:
            status = str(getattr(req, "status", "pending") or "pending").replace("_", " ").title()
            subject = f"Return request update for order #{order.id}"
            detail = f"Your return request is now <strong>{status}</strong>."

        html = (
            f"<h2>Hi {_first_name(user)},</h2>"
            f"<p>{detail}</p>"
            f"<p><strong>Reason:</strong> {getattr(req, 'reason', '')}</p>"
            f"<p><a href=\"{_order_link(cast(int, order.id))}\">View order</a></p>"
        )
        send_email(str(user.email), subject, html, purpose="notification")
        return {"return_id": return_id, "sent": True, "event_kind": event_kind}


def _send_shipment_status_email(shipment_id: int, *, event_type: str | None = None) -> dict[str, Any]:
    with get_service_session() as db:
        shipment = db.query(Shipment).options(selectinload(Shipment.order).selectinload(Order.user)).filter(Shipment.id == shipment_id).first()
        order = getattr(shipment, "order", None)
        user = getattr(order, "user", None)
        if shipment is None or order is None or user is None or not getattr(user, "email", None):
            return {"shipment_id": shipment_id, "sent": False, "reason": "missing-shipment-or-user"}

        status = str(getattr(shipment, "status", "pending") or "pending")
        status_label = shipment_status_label(status, shipment=shipment)
        detail = f"Shipment for order #{order.id} is now <strong>{status_label}</strong>."
        if event_type:
            detail = f"Shipment event: <strong>{event_type.replace('_', ' ').title()}</strong>.<br>{detail}"

        html = (
            f"<h2>Shipment update for order #{order.id}</h2>"
            f"<p>Hi {_first_name(user)},</p>"
            f"<p>{detail}</p>"
            f"<p><a href=\"{_tracking_link(cast(int, order.id))}\">Track your shipment</a></p>"
        )
        send_email(str(user.email), f"Shipment update for order #{order.id}", html, purpose="notification")
        return {"shipment_id": shipment_id, "sent": True, "status": status}


def _send_invoice_email(invoice_id: int) -> dict[str, Any]:
    with get_service_session() as db:
        from models import Invoice
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice is None:
            return {"invoice_id": invoice_id, "sent": False, "reason": "not-found"}
        order = db.query(Order).filter(Order.id == invoice.order_id).first()
        user = order.user if order else None
        if not user or not getattr(user, "email", None):
            return {"invoice_id": invoice_id, "sent": False, "reason": "no-customer-email"}
        invoice_num = str(getattr(invoice, "invoice_number", f"#{invoice_id}"))
        total = float(getattr(invoice, "total_amount", 0) or 0)
        currency = str(getattr(invoice, "currency", "AED") or "AED")
        html = (
            f"<h2>Your ZOZI Invoice {invoice_num}</h2>"
            f"<p>Hi {_first_name(user)},</p>"
            f"<p>Your invoice <strong>{invoice_num}</strong> for "
            f"<strong>{currency} {total:.2f}</strong> has been issued for order "
            f"#{invoice.order_id}.</p>"
            f"<p><a href=\"{settings.frontend_url.rstrip('/')}/orders/{invoice.order_id}\">View Order</a></p>"
        )
        send_email(str(user.email), f"ZOZI Invoice {invoice_num}", html, purpose="transactional")
        return {"invoice_id": invoice_id, "sent": True}


def _send_low_stock_alert_email(product_id: int, stock_count: int) -> dict[str, Any]:
    with get_service_session() as db:
        from models import Product
        product = db.query(Product).filter(Product.id == product_id).first()  # type: ignore[attr-defined]
        if product is None:
            return {"product_id": product_id, "sent": False, "reason": "not-found"}
        # Alert goes to the supplier or platform admin alert inbox
        supplier = None
        supplier_id = getattr(product, "supplier_id", None)
        if supplier_id:
            supplier = db.query(User).filter(User.id == supplier_id).first()
        to = str(getattr(supplier, "email", None) or settings.email_from)
        name = str(getattr(product, "name", f"Product #{product_id}") or f"Product #{product_id}")
        html = (
            f"<h2>Low Stock Alert</h2>"
            f"<p>Product <strong>{name}</strong> (ID: {product_id}) has reached a low stock level: "
            f"<strong>{stock_count}</strong> unit(s) remaining.</p>"
            f"<p>Please restock soon to avoid out-of-stock situations.</p>"
        )
        send_email(to, f"Low Stock Alert: {name}", html, purpose="alert")
        return {"product_id": product_id, "sent": True, "stock_count": stock_count}


def _send_doc_status_email(supplier_id: int, doc_type: str, status: str, review_note: str | None) -> dict[str, Any]:
    with get_service_session() as db:
        supplier = db.query(User).filter(User.id == supplier_id).first()
        if not supplier or not getattr(supplier, "email", None):
            return {"supplier_id": supplier_id, "sent": False, "reason": "no-supplier-email"}
        label = doc_type.replace("_", " ").title()
        status_label = status.replace("_", " ").title()
        html = (
            f"<h2>Document {status_label}: {label}</h2>"
            f"<p>Hi {_first_name(supplier)},</p>"
            f"<p>Your document <strong>{label}</strong> has been reviewed and the status is now "
            f"<strong>{status_label}</strong>.</p>"
        )
        if review_note:
            html += f"<p><em>Reviewer note:</em> {review_note}</p>"
        html += (
            f"<p><a href=\"{settings.frontend_url.rstrip('/')}/supplier/documents\">View Documents</a></p>"
        )
        send_email(
            str(supplier.email),
            f"Document Update: {label} — {status_label}",
            html,
            purpose="notification",
        )
        return {"supplier_id": supplier_id, "sent": True, "status": status}


def enqueue_invoice_email(invoice_id: int) -> dict[str, Any]:
    return enqueue_job(kind="email-invoice-issued", owner_user_id=None, owner_role="system", metadata={"invoice_id": invoice_id}, func=lambda: _send_invoice_email(invoice_id))


def enqueue_order_created_email(order_id: int) -> dict[str, Any]:
    return enqueue_job(kind="email-order-created", owner_user_id=None, owner_role="system", metadata={"order_id": order_id}, func=lambda: _send_order_created_email(order_id))


def enqueue_low_stock_alert_email(product_id: int, stock_count: int) -> dict[str, Any]:
    return enqueue_job(kind="email-low-stock-alert", owner_user_id=None, owner_role="system", metadata={"product_id": product_id, "stock_count": stock_count}, func=lambda: _send_low_stock_alert_email(product_id, stock_count))


def enqueue_doc_status_email(supplier_id: int, doc_type: str, status: str, review_note: str | None = None) -> dict[str, Any]:
    return enqueue_job(kind="email-doc-status", owner_user_id=None, owner_role="system", metadata={"supplier_id": supplier_id, "doc_type": doc_type, "status": status}, func=lambda: _send_doc_status_email(supplier_id, doc_type, status, review_note))


def enqueue_order_confirmation_email(order_id: int) -> dict[str, Any]:
    return enqueue_job(kind="email-order-confirmation", owner_user_id=None, owner_role="system", metadata={"order_id": order_id}, func=lambda: _send_order_created_email(order_id))


def enqueue_shipment_status_email(shipment_id: int, *, event_type: str | None = None) -> dict[str, Any]:
    return enqueue_job(
        kind="email-shipment-status",
        owner_user_id=None,
        owner_role="system",
        metadata={"shipment_id": shipment_id, "event_type": event_type},
        func=lambda: _send_shipment_status_email(shipment_id, event_type=event_type),
    )


def enqueue_payment_confirmed_email(order_id: int, *, provider: str, message: str | None = None) -> dict[str, Any]:
    return enqueue_job(
        kind="email-payment-confirmed",
        owner_user_id=None,
        owner_role="system",
        metadata={"order_id": order_id, "provider": provider},
        func=lambda: _send_payment_email(order_id, outcome="confirmed", provider=provider, message=message),
    )


def enqueue_payment_failed_email(order_id: int, *, provider: str, message: str | None = None) -> dict[str, Any]:
    return enqueue_job(
        kind="email-payment-failed",
        owner_user_id=None,
        owner_role="system",
        metadata={"order_id": order_id, "provider": provider},
        func=lambda: _send_payment_email(order_id, outcome="failed", provider=provider, message=message),
    )


def enqueue_refund_processed_email(order_id: int, *, source: str) -> dict[str, Any]:
    return enqueue_job(
        kind="email-refund-processed",
        owner_user_id=None,
        owner_role="system",
        metadata={"order_id": order_id, "source": source},
        func=lambda: _send_refund_email(order_id, source=source),
    )


def enqueue_order_status_email(order_id: int, *, status: str) -> dict[str, Any]:
    return enqueue_job(
        kind="email-order-status",
        owner_user_id=None,
        owner_role="system",
        metadata={"order_id": order_id, "status": status},
        func=lambda: _send_order_status_email(order_id, status=status),
    )


def enqueue_return_created_email(return_id: int) -> dict[str, Any]:
    return enqueue_job(
        kind="email-return-created",
        owner_user_id=None,
        owner_role="system",
        metadata={"return_id": return_id},
        func=lambda: _send_return_email(return_id, event_kind="created"),
    )


def enqueue_return_status_email(return_id: int, *, event_kind: str = "status") -> dict[str, Any]:
    return enqueue_job(
        kind="email-return-status",
        owner_user_id=None,
        owner_role="system",
        metadata={"return_id": return_id, "event_kind": event_kind},
        func=lambda: _send_return_email(return_id, event_kind=event_kind),
    )


# ── Dunning Emails (#12) ──────────────────────────────────────────────────


def _send_dunning_email(invoice_id: int, reminder_type: str, message: str) -> dict[str, Any]:
    with get_service_session() as db:
        from models import ARInvoice, Customer
        inv = db.query(ARInvoice).filter(ARInvoice.id == invoice_id).first()
        if not inv:
            return {"invoice_id": invoice_id, "sent": False, "reason": "not_found"}
        
        customer = db.query(Customer).filter(Customer.id == inv.customer_id).first()
        if not customer or not customer.contact_email:
            return {"invoice_id": invoice_id, "sent": False, "reason": "no_email"}
        
        subject = f"ZOZI Payment Reminder - Invoice {inv.invoice_number}"
        html = (
            f"<h2>Payment Reminder</h2>"
            f"<p>Dear {customer.name},</p>"
            f"<p>{message}</p>"
            f"<p><strong>Invoice:</strong> {inv.invoice_number}</p>"
            f"<p><strong>Amount:</strong> {inv.amount} {inv.customer.currency if inv.customer else 'OMR'}</p>"
            f"<p><strong>Due Date:</strong> {inv.due_date.strftime('%Y-%m-%d') if inv.due_date else 'N/A'}</p>"
            f"<p>Please arrange payment at your earliest convenience.</p>"
            f"<p>Best regards,<br>ZOZI Finance Team</p>"
        )
        send_email(customer.contact_email, subject, html, purpose="dunning")
        return {"invoice_id": invoice_id, "sent": True, "reminder_type": reminder_type}


def enqueue_dunning_email(invoice_id: int, reminder_type: str, message: str) -> dict[str, Any]:
    return enqueue_job(
        kind="email-dunning",
        owner_user_id=None,
        owner_role="system",
        metadata={"invoice_id": invoice_id, "reminder_type": reminder_type},
        func=lambda: _send_dunning_email(invoice_id, reminder_type, message),
    )


# ── Distributor Statement Email (#23) ─────────────────────────────────────


def _send_distributor_statement_email(customer_id: int, period: str, statement_data: dict) -> dict[str, Any]:
    with get_service_session() as db:
        from models import Customer
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer or not customer.contact_email:
            return {"customer_id": customer_id, "sent": False, "reason": "no_email"}
        
        subject = f"ZOZI Monthly Statement - {period}"
        invoices_html = ""
        for inv in statement_data.get("invoices", []):
            invoices_html += (
                f"<tr><td>{inv.get('invoice_number', 'N/A')}</td>"
                f"<td>{inv.get('date', 'N/A')}</td>"
                f"<td>{inv.get('amount', 0)}</td>"
                f"<td>{inv.get('status', 'N/A')}</td></tr>"
            )
        
        html = (
            f"<h2>Monthly Statement - {period}</h2>"
            f"<p>Dear {customer.name},</p>"
            f"<p>Please find your monthly statement below:</p>"
            f"<table border='1' cellpadding='8' cellspacing='0'>"
            f"<tr><th>Invoice</th><th>Date</th><th>Amount</th><th>Status</th></tr>"
            f"{invoices_html}"
            f"</table>"
            f"<p><strong>Total Invoiced:</strong> {statement_data.get('total_invoiced', 0)}</p>"
            f"<p><strong>Total Paid:</strong> {statement_data.get('total_paid', 0)}</p>"
            f"<p><strong>Outstanding:</strong> {statement_data.get('total_outstanding', 0)}</p>"
            f"<p>Best regards,<br>ZOZI Finance Team</p>"
        )
        send_email(customer.contact_email, subject, html, purpose="statement")
        return {"customer_id": customer_id, "sent": True, "period": period}


def enqueue_distributor_statement_email(customer_id: int, period: str, statement_data: dict) -> dict[str, Any]:
    return enqueue_job(
        kind="email-distributor-statement",
        owner_user_id=None,
        owner_role="system",
        metadata={"customer_id": customer_id, "period": period},
        func=lambda: _send_distributor_statement_email(customer_id, period, statement_data),
    )


# ── Supplier Payout Approval Link (#15) ───────────────────────────────────


def _send_supplier_approval_email(supplier_id: int, batch_id: int, batch_number: str, total_amount: float) -> dict[str, Any]:
    with get_service_session() as db:
        from models import User
        supplier = db.query(User).filter(User.id == supplier_id).first()
        if not supplier or not getattr(supplier, "email", None):
            return {"supplier_id": supplier_id, "sent": False, "reason": "no_email"}
        
        approval_link = f"{settings.frontend_url.rstrip('/')}/supplier/payouts/{batch_id}/approve"
        subject = f"ZOZI Payout Batch Ready for Approval - {batch_number}"
        html = (
            f"<h2>Payout Batch Ready for Approval</h2>"
            f"<p>Dear {getattr(supplier, 'username', 'Supplier')},</p>"
            f"<p>A new payout batch is ready for your approval:</p>"
            f"<p><strong>Batch:</strong> {batch_number}</p>"
            f"<p><strong>Amount:</strong> {total_amount} OMR</p>"
            f"<p><a href=\"{approval_link}\">Review and Approve</a></p>"
            f"<p>Best regards,<br>ZOZI Finance Team</p>"
        )
        send_email(supplier.email, subject, html, purpose="payout_approval")
        return {"supplier_id": supplier_id, "sent": True, "batch_id": batch_id}


def enqueue_supplier_approval_email(supplier_id: int, batch_id: int, batch_number: str, total_amount: float) -> dict[str, Any]:
    return enqueue_job(
        kind="email-supplier-approval",
        owner_user_id=None,
        owner_role="system",
        metadata={"supplier_id": supplier_id, "batch_id": batch_id},
        func=lambda: _send_supplier_approval_email(supplier_id, batch_id, batch_number, total_amount),
    )

