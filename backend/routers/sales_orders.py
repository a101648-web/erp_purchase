from fastapi import APIRouter, HTTPException
from models.store import sales_orders, so_items, customers, inventory, new_id, now, TAX_RATES
from schemas.purchase import SOCreate, SOStatusUpdate

router = APIRouter()


def _attach_items(so):
    so = so.copy()
    so["items"] = [i for i in so_items.values() if i["so_id"] == so["id"]]
    return so


@router.get("/")
def list_sos(status: str = None):
    result = list(sales_orders.values())
    if status:
        result = [s for s in result if s["status"] == status]
    return [_attach_items(s) for s in result]


@router.post("/", status_code=201)
def create_so(body: SOCreate):
    if body.customer_id not in customers:
        raise HTTPException(404, "客戶不存在")
    cus = customers[body.customer_id]
    so_id = "SO-" + new_id()
    total = sum(i.qty * i.unit_price for i in body.items)

    so = {
        "id":               so_id,
        "customer_id":      body.customer_id,
        "customer_name":    cus["name"],
        "customer_code":    cus.get("customer_code", ""),
        "expected_date":    body.expected_date,
        "delivery_address": body.delivery_address or cus.get("address", ""),
        "status":           "draft",
        "total_amount":     round(total, 2),
        "total_tax":        0.0,
        "note":             body.note,
        "created_at":       now(),
    }
    sales_orders[so_id] = so

    total_tax = 0.0
    for item in body.items:
        inv_tax  = inventory.get(item.sku, {}).get("tax_type", "taxable")
        tax_type = item.tax_type or inv_tax
        tax_rate = TAX_RATES.get(tax_type, 0.05)
        subtotal = round(item.qty * item.unit_price, 2)
        tax_amt  = round(subtotal * tax_rate, 2)
        total_tax += tax_amt
        iid = new_id()
        so_items[iid] = {
            **item.model_dump(),
            "id":          iid,
            "so_id":       so_id,
            "tax_type":    tax_type,
            "tax_rate":    tax_rate,
            "subtotal":    subtotal,
            "tax_amt":     tax_amt,
            "shipped_qty": 0,
        }
    sales_orders[so_id]["total_tax"] = round(total_tax, 2)
    return _attach_items(sales_orders[so_id])


@router.get("/{so_id}")
def get_so(so_id: str):
    if so_id not in sales_orders:
        raise HTTPException(404, "銷貨訂單不存在")
    return _attach_items(sales_orders[so_id])


@router.patch("/{so_id}/status")
def update_so_status(so_id: str, body: SOStatusUpdate):
    if so_id not in sales_orders:
        raise HTTPException(404, "銷貨訂單不存在")
    sales_orders[so_id]["status"] = body.status
    sales_orders[so_id]["updated_at"] = now()
    return _attach_items(sales_orders[so_id])
