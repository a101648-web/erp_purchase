from fastapi import APIRouter, HTTPException
from models.store import purchase_orders, suppliers, po_items, new_id, now
from schemas.purchase import POCreate, POStatusUpdate

router = APIRouter()


@router.get("/")
def list_pos(status: str = None):
    result = list(purchase_orders.values())
    if status:
        result = [p for p in result if p["status"] == status]
    # 附上明細
    for po in result:
        po["items"] = [i for i in po_items.values() if i["po_id"] == po["id"]]
    return result


@router.post("/", status_code=201)
def create_po(body: POCreate):
    if body.supplier_id not in suppliers:
        raise HTTPException(404, "供應商不存在")

    po_id = "PO-" + new_id()
    total = sum(i.qty * i.unit_price for i in body.items)

    po = {
        "id":            po_id,
        "supplier_id":   body.supplier_id,
        "supplier_name": suppliers[body.supplier_id]["name"],
        "expected_date": body.expected_date,
        "status":        "draft",
        "total_amount":  round(total, 2),
        "note":          body.note,
        "created_at":    now(),
    }
    purchase_orders[po_id] = po

    # 寫入明細
    for item in body.items:
        iid = new_id()
        po_items[iid] = {
            **item.model_dump(),
            "id":           iid,
            "po_id":        po_id,
            "received_qty": 0,
            "subtotal":     round(item.qty * item.unit_price, 2),
        }

    po["items"] = [i for i in po_items.values() if i["po_id"] == po_id]
    return po


@router.get("/{po_id}")
def get_po(po_id: str):
    if po_id not in purchase_orders:
        raise HTTPException(404, "採購單不存在")
    po = purchase_orders[po_id].copy()
    po["items"] = [i for i in po_items.values() if i["po_id"] == po_id]
    return po


@router.patch("/{po_id}/status")
def update_po_status(po_id: str, body: POStatusUpdate):
    if po_id not in purchase_orders:
        raise HTTPException(404, "採購單不存在")
    purchase_orders[po_id]["status"] = body.status
    purchase_orders[po_id]["updated_at"] = now()
    return purchase_orders[po_id]


@router.delete("/{po_id}", status_code=204)
def cancel_po(po_id: str):
    if po_id not in purchase_orders:
        raise HTTPException(404, "採購單不存在")
    if purchase_orders[po_id]["status"] not in ["draft"]:
        raise HTTPException(400, "只有草稿狀態可以刪除")
    purchase_orders[po_id]["status"] = "closed"
