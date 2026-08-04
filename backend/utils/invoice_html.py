"""
Invoice HTML generator — produces a printable, email-safe HTML invoice.

No external PDF libraries required; browsers and email clients render this
directly. Users can print-to-PDF from any browser.

Usage:
    html = generate_invoice_html(inv_data)
    email_invoice(inv_data, to="customer@example.com")
"""
import html as _html
import io
import logging
from utils.config import settings

logger = logging.getLogger(__name__)


def _e(value: object) -> str:
    """HTML-escape a value for safe insertion into templates."""
    return _html.escape(str(value) if value is not None else "")


def generate_invoice_html(inv: dict) -> str:
    """Render a full invoice as an HTML document suitable for email or browser."""
    items_html = ""
    for item in inv.get("items", []):
        items_html += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;">{_e(item.get('description',''))}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center;">{_e(item.get('quantity',''))}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;">{_e(inv.get('currency','AED'))} {float(item.get('unit_price',0)):.2f}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;">{_e(inv.get('currency','AED'))} {float(item.get('line_total',0)):.2f}</td>
        </tr>"""

    currency = _e(inv.get("currency", "AED"))
    subtotal = float(inv.get("subtotal", 0))
    tax = float(inv.get("tax_amount", 0))
    shipping = float(inv.get("shipping_amount", 0))
    discount = float(inv.get("discount_amount", 0))
    total = float(inv.get("total_amount", 0))
    issued_at = _e(inv.get("issued_at", "")[:10] if inv.get("issued_at") else "—")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Invoice {_e(inv.get('invoice_number',''))}</title>
  <style>
    body{{font-family:Arial,Helvetica,sans-serif;color:#1f2937;margin:0;padding:0;background:#f9fafb}}
    .wrapper{{max-width:700px;margin:40px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
    .header{{background:#1f2937;color:#fff;padding:30px 40px;display:flex;justify-content:space-between;align-items:center}}
    .header h1{{margin:0;font-size:26px;letter-spacing:1px}}
    .header .inv-details{{text-align:right;font-size:13px;color:#d1d5db}}
    .body{{padding:32px 40px}}
    .info-row{{display:flex;gap:40px;margin-bottom:28px}}
    .info-block{{flex:1}}
    .info-block h4{{margin:0 0 6px 0;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#6b7280}}
    .info-block p{{margin:0;font-size:14px;line-height:1.6}}
    table{{width:100%;border-collapse:collapse;margin-bottom:24px}}
    thead tr{{background:#f3f4f6}}
    thead th{{padding:10px 12px;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:#6b7280;font-weight:600}}
    thead th:nth-child(2){{text-align:center}}
    thead th:nth-child(3),thead th:nth-child(4){{text-align:right}}
    .totals{{margin-left:auto;width:260px}}
    .totals tr td{{padding:5px 12px;font-size:14px}}
    .totals tr td:last-child{{text-align:right}}
    .totals .total-row td{{font-size:16px;font-weight:bold;color:#1f2937;border-top:2px solid #1f2937;padding-top:10px}}
    .badge{{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;text-transform:capitalize}}
    .badge-issued{{background:#dbeafe;color:#1d4ed8}}
    .badge-in_transit{{background:#fef3c7;color:#d97706}}
    .badge-delivered{{background:#d1fae5;color:#065f46}}
    .badge-cancelled{{background:#fee2e2;color:#dc2626}}
    .badge-draft{{background:#f3f4f6;color:#6b7280}}
    .footer{{background:#f9fafb;padding:20px 40px;font-size:12px;color:#9ca3af;text-align:center;border-top:1px solid #e5e7eb}}
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>ZOZI</h1>
    <div class="inv-details">
      <div style="font-size:18px;font-weight:bold;color:#fff;margin-bottom:4px">{_e(inv.get('invoice_number',''))}</div>
      <div>Issued: {issued_at}</div>
      <div style="margin-top:6px">
        <span class="badge badge-{_e(inv.get('status','draft'))}">{_e(inv.get('status','draft'))}</span>
      </div>
    </div>
  </div>

  <div class="body">
    <div class="info-row">
      <div class="info-block">
        <h4>From</h4>
        <p><strong>ZOZI Marketplace</strong><br>
        {_e(getattr(settings,'business_address','Dubai, UAE'))}<br>
        {_e(getattr(settings,'support_email','support@zozi.ae'))}</p>
      </div>
      <div class="info-block">
        <h4>Supplier</h4>
        <p>{_e(inv.get('supplier_name','—'))}</p>
      </div>
      <div class="info-block">
        <h4>Order</h4>
        <p>#{_e(inv.get('order_id','—'))}</p>
      </div>
    </div>

    <table>
      <thead>
        <tr>
          <th>Description</th>
          <th>Qty</th>
          <th>Unit Price</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        {items_html}
      </tbody>
    </table>

    <table class="totals">
      <tr><td style="color:#6b7280">Subtotal</td><td>{currency} {subtotal:.2f}</td></tr>
      {'<tr><td style="color:#6b7280">Discount</td><td style="color:#dc2626">- ' + currency + ' ' + f'{discount:.2f}' + '</td></tr>' if discount else ''}
      <tr><td style="color:#6b7280">Tax (5% VAT)</td><td>{currency} {tax:.2f}</td></tr>
      {'<tr><td style="color:#6b7280">Shipping</td><td>' + currency + ' ' + f'{shipping:.2f}' + '</td></tr>' if shipping else ''}
      <tr class="total-row"><td>Total Due</td><td>{currency} {total:.2f}</td></tr>
    </table>

    {'<p style="font-size:13px;color:#6b7280;margin-top:16px"><strong>Notes:</strong> ' + _e(inv.get('notes','')) + '</p>' if inv.get('notes') else ''}
  </div>

  <div class="footer">
    ZOZI Marketplace &mdash; Thank you for your business.<br>
    Questions? Contact <a href="mailto:{_e(getattr(settings,'support_email','support@zozi.ae'))}">
      {_e(getattr(settings,'support_email','support@zozi.ae'))}</a>
  </div>
</div>
</body>
</html>"""


def generate_invoice_pdf_bytes(inv: dict) -> bytes:
  """Render a lightweight binary PDF invoice for download/attachment flows."""
  from reportlab.lib.pagesizes import A4
  from reportlab.pdfgen import canvas

  buffer = io.BytesIO()
  pdf = canvas.Canvas(buffer, pagesize=A4)
  width, height = A4
  y = height - 50

  def line(text: str, *, size: int = 10, bold: bool = False, step: int = 16) -> None:
    nonlocal y
    font = "Helvetica-Bold" if bold else "Helvetica"
    pdf.setFont(font, size)
    pdf.drawString(40, y, text[:110])
    y -= step

  currency = str(inv.get("currency", "AED"))
  pdf.setTitle(f"Invoice {inv.get('invoice_number', '')}")
  line("ZOZI Marketplace", size=18, bold=True, step=24)
  line(f"Invoice: {inv.get('invoice_number', '—')}", bold=True)
  line(f"Order: #{inv.get('order_id', '—')}    Status: {inv.get('status', 'draft')}")
  line(f"Supplier: {inv.get('supplier_name', '—')}")
  line(f"Issued: {(inv.get('issued_at') or '—')[:10] if inv.get('issued_at') else '—'}", step=24)

  pdf.setFont("Helvetica-Bold", 10)
  pdf.drawString(40, y, "Description")
  pdf.drawString(320, y, "Qty")
  pdf.drawString(380, y, "Unit")
  pdf.drawString(470, y, "Total")
  y -= 14
  pdf.line(40, y, 550, y)
  y -= 14

  for item in inv.get("items", []):
    if y < 120:
      pdf.showPage()
      y = height - 50
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, str(item.get("description", ""))[:42])
    pdf.drawString(320, y, str(item.get("quantity", "")))
    pdf.drawRightString(450, y, f"{currency} {float(item.get('unit_price', 0)):.2f}")
    pdf.drawRightString(540, y, f"{currency} {float(item.get('line_total', 0)):.2f}")
    y -= 16

  y -= 8
  pdf.line(300, y, 550, y)
  y -= 18
  for label, value in (
    ("Subtotal", float(inv.get("subtotal", 0))),
    ("Discount", -float(inv.get("discount_amount", 0))),
    ("Tax", float(inv.get("tax_amount", 0))),
    ("Shipping", float(inv.get("shipping_amount", 0))),
    ("Total", float(inv.get("total_amount", 0))),
  ):
    if label != "Total" and value == 0:
      continue
    pdf.setFont("Helvetica-Bold" if label == "Total" else "Helvetica", 10)
    pdf.drawString(340, y, label)
    pdf.drawRightString(540, y, f"{currency} {value:.2f}")
    y -= 16

  if inv.get("notes"):
    y -= 12
    line(f"Notes: {inv['notes']}", step=14)

  pdf.showPage()
  pdf.save()
  return buffer.getvalue()


def email_invoice(inv: dict, to: str, subject_prefix: str = "Your Invoice") -> None:
    """Generate and email an HTML invoice. Silently logs on failure (non-blocking)."""
    from utils.email_service import send_email
    try:
        invoice_number = inv.get("invoice_number", "")
        subject = f"{subject_prefix} – {invoice_number}"
        html = generate_invoice_html(inv)
        send_email(to=to, subject=subject, html=html)
        logger.info("Invoice email sent: %s → %s", invoice_number, to)
    except Exception as exc:
        # Email delivery failures must not break the invoice flow
        logger.error("Failed to email invoice %s to %s: %s", inv.get("invoice_number"), to, exc)

