from pathlib import Path
from decimal import Decimal
from app.config import RECEIPTS_DIR, CURRENCY

def create_pdf(order_data):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise RuntimeError("PDF support requires ReportLab. Run: pip install reportlab") from exc

    order = order_data["order"]
    items = order_data["items"]
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RECEIPTS_DIR / f"{order['order_number']}.pdf"
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 55

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(48, y, "RESTAURANT BILL")
    y -= 28
    pdf.setFont("Helvetica", 10)
    pdf.drawString(48, y, f"Order: {order['order_number']}")
    y -= 16
    pdf.drawString(48, y, f"Date: {order['created_at']}")
    y -= 16
    pdf.drawString(48, y, f"Type: {order['order_type']}  Table: {order.get('table_number') or '-'}")
    y -= 26
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(48, y, "Item")
    pdf.drawString(300, y, "Qty")
    pdf.drawString(355, y, "Price")
    pdf.drawString(440, y, "Amount")
    y -= 12
    pdf.line(48, y, width - 48, y)
    y -= 18
    pdf.setFont("Helvetica", 10)
    for item in items:
        if y < 90:
            pdf.showPage()
            y = height - 55
        name = item["item_name"][:38]
        pdf.drawString(48, y, name)
        pdf.drawRightString(330, y, str(item["quantity"]))
        pdf.drawRightString(410, y, f"{CURRENCY}{Decimal(item['unit_price']):.2f}")
        pdf.drawRightString(width - 48, y, f"{CURRENCY}{Decimal(item['line_total']):.2f}")
        y -= 18

    y -= 8
    pdf.line(300, y, width - 48, y)
    y -= 20
    for label, key in [
        ("Subtotal", "subtotal"),
        ("Discount", "discount_amount"),
        ("Tax", "tax_amount"),
        ("TOTAL", "total_amount"),
    ]:
        pdf.setFont("Helvetica-Bold" if label == "TOTAL" else "Helvetica", 11)
        pdf.drawString(320, y, label)
        pdf.drawRightString(width - 48, y, f"{CURRENCY}{Decimal(order[key]):.2f}")
        y -= 20
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(48, 40, "Thank you for visiting!")
    pdf.save()
    return path
