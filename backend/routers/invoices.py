from fastapi import APIRouter, HTTPException
from models.store import invoices, purchase_orders, new_id, now
from schemas.purchase import InvoiceCreate, InvoiceStatusUpdate

router = APIRouter()


@router.get("/")
def list_invoices(status: str = None):
    result = list(invoices.values())
    if status:
        result = [i for i in result if i["status"] == status]
    return result


@router.post("/", status_code=201)
def create_invoice(body: InvoiceCreate):
    if body.po_id not in purchase_orders:
        raise HTTPException(404, "採購單不存在")

    po = purchase_orders[body.po_id]

    # 自動對帳：比對金額
    po_total = po["total_amount"]
    invoice_total = round(body.amount + body.tax, 2)
    matched = abs(po_total - invoice_total) < 0.01

    inv_id = "INV-" + new_id()
    record = {
        "id":            inv_id,
        "po_id":         body.po_id,
        "supplier_name": po["supplier_name"],
        "invoice_no":    body.invoice_no,
        "invoice_date":  body.invoice_date,
        "amount":        body.amount,
        "tax":           body.tax,
        "total":         invoice_total,
        "po_total":      po_total,
        "status":        "matched" if matched else "disputed",
        "match_note":    "金額相符，自動對帳" if matched else f"金額不符（採購單 {po_total}，發票 {invoice_total}）",
        "created_at":    now(),
    }
    invoices[inv_id] = record
    return record


@router.patch("/{inv_id}/status")
def update_invoice_status(inv_id: str, body: InvoiceStatusUpdate):
    if inv_id not in invoices:
        raise HTTPException(404, "發票不存在")
    invoices[inv_id]["status"] = body.status
    invoices[inv_id]["updated_at"] = now()
    return invoices[inv_id]
