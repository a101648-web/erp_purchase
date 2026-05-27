from fastapi import APIRouter, HTTPException
from models.store import shipments, sales_orders, so_items, inventory, new_id, now
from schemas.purchase import ShipmentCreate

router = APIRouter()


@router.get("/")
def list_shipments(so_id: str = None):
    result = list(shipments.values())
    if so_id:
        result = [s for s in result if s["so_id"] == so_id]
    return result


@router.post("/", status_code=201)
def create_shipment(body: ShipmentCreate):
    if body.so_id not in sales_orders:
        raise HTTPException(404, "銷貨訂單不存在")

    so = sales_orders[body.so_id]
    if so["status"] not in ["confirmed", "partial"]:
        raise HTTPException(400, "銷貨訂單狀態必須為「已確認」或「部分出貨」")

    items_map = {i["sku"]: i for i in so_items.values() if i["so_id"] == body.so_id}
    lines = []

    for line in body.items:
        if line.sku not in items_map:
            raise HTTPException(400, f"SKU {line.sku} 不在此銷貨訂單中")
        soi = items_map[line.sku]
        remaining = soi["qty"] - soi["shipped_qty"]
        if line.shipped_qty > remaining:
            raise HTTPException(400, f"SKU {line.sku} 出貨數量超過未出貨數量（剩餘 {remaining}）")

        # 扣庫存
        if line.sku in inventory:
            if inventory[line.sku]["qty"] < line.shipped_qty:
                raise HTTPException(400, f"SKU {line.sku} 庫存不足（現有 {inventory[line.sku]['qty']}）")
            inventory[line.sku]["qty"] -= line.shipped_qty
            inventory[line.sku]["updated_at"] = now()

        soi["shipped_qty"] += line.shipped_qty
        lines.append({"sku": line.sku, "name": soi["name"], "shipped_qty": line.shipped_qty})

    # 更新銷貨訂單狀態
    all_items = [i for i in so_items.values() if i["so_id"] == body.so_id]
    fully_shipped = all(i["shipped_qty"] >= i["qty"] for i in all_items)
    so["status"] = "shipped" if fully_shipped else "partial"
    so["updated_at"] = now()

    ship_id = "SHIP-" + new_id()
    record = {"id": ship_id, "so_id": body.so_id, "lines": lines, "note": body.note, "created_at": now()}
    shipments[ship_id] = record
    return record
