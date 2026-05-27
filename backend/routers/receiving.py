from fastapi import APIRouter, HTTPException
from models.store import (
    receiving_records, purchase_orders, po_items, inventory, new_id, now
)
from schemas.purchase import ReceivingCreate

router = APIRouter()


@router.get("/")
def list_receivings(po_id: str = None):
    result = list(receiving_records.values())
    if po_id:
        result = [r for r in result if r["po_id"] == po_id]
    return result


@router.post("/", status_code=201)
def create_receiving(body: ReceivingCreate):
    if body.po_id not in purchase_orders:
        raise HTTPException(404, "採購單不存在")

    po = purchase_orders[body.po_id]
    if po["status"] not in ["confirmed", "partial"]:
        raise HTTPException(400, "採購單狀態必須為「已確認」或「部分入庫」")

    # 取得此 PO 所有明細
    items_map = {i["sku"]: i for i in po_items.values() if i["po_id"] == body.po_id}
    receiving_lines = []

    for line in body.items:
        if line.sku not in items_map:
            raise HTTPException(400, f"SKU {line.sku} 不在此採購單中")

        poi = items_map[line.sku]
        remaining = poi["qty"] - poi["received_qty"]
        if line.received_qty > remaining:
            raise HTTPException(400, f"SKU {line.sku} 入庫數量超過未入庫數量（剩餘 {remaining}）")

        # 更新 PO 明細已入庫數
        poi["received_qty"] += line.received_qty

        # 更新庫存
        if line.sku in inventory:
            inventory[line.sku]["qty"] += line.received_qty
            inventory[line.sku]["updated_at"] = now()
        else:
            # 新品項自動建立
            inventory[line.sku] = {
                "sku":       line.sku,
                "name":      poi["name"],
                "unit":      poi["unit"],
                "qty":       line.received_qty,
                "unit_cost": poi["unit_price"],
                "updated_at": now(),
            }

        receiving_lines.append({
            "sku":          line.sku,
            "name":         poi["name"],
            "received_qty": line.received_qty,
        })

    # 更新 PO 狀態
    all_items = [i for i in po_items.values() if i["po_id"] == body.po_id]
    fully_received = all(i["received_qty"] >= i["qty"] for i in all_items)
    po["status"] = "received" if fully_received else "partial"
    po["updated_at"] = now()

    rec_id = "REC-" + new_id()
    record = {
        "id":         rec_id,
        "po_id":      body.po_id,
        "lines":      receiving_lines,
        "note":       body.note,
        "created_at": now(),
    }
    receiving_records[rec_id] = record
    return record
