from fastapi import APIRouter, HTTPException
from models.store import sales_invoices, sales_orders, new_id, now
from schemas.purchase import SalesInvoiceCreate, SalesInvoiceStatusUpdate

router = APIRouter()


@router.get("/")
def list_sales_invoices(status: str = None):
    result = list(sales_invoices.values())
    if status:
        result = [i for i in result if i["status"] == status]
    return result


@router.post("/", status_code=201)
def create_sales_invoice(body: SalesInvoiceCreate):
    if body.so_id not in sales_orders:
        raise HTTPException(404, "銷貨訂單不存在")
    so = sales_orders[body.so_id]
    inv_id = "SINV-" + new_id()
    total  = round(body.amount + body.tax, 2)
    record = {
        "id":            inv_id,
        "so_id":         body.so_id,
        "customer_name": so["customer_name"],
        "invoice_no":    body.invoice_no,
        "invoice_date":  body.invoice_date,
        "due_date":      body.due_date,
        "amount":        body.amount,
        "tax":           body.tax,
        "total":         total,
        "status":        "pending",
        "created_at":    now(),
    }
    sales_invoices[inv_id] = record
    return record


@router.patch("/{inv_id}/status")
def update_invoice_status(inv_id: str, body: SalesInvoiceStatusUpdate):
    if inv_id not in sales_invoices:
        raise HTTPException(404, "銷貨發票不存在")
    sales_invoices[inv_id]["status"] = body.status
    sales_invoices[inv_id]["updated_at"] = now()
    return sales_invoices[inv_id]
