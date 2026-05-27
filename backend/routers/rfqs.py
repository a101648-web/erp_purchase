from fastapi import APIRouter, HTTPException
from models.store import (
    rfqs, rfq_items, purchase_orders, po_items,
    suppliers, inventory, new_id, now, TAX_RATES
)
from schemas.purchase import RFQCreate, RFQStatusUpdate, RFQItem
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


class RFQUpdate(BaseModel):
    supplier_id:       Optional[str] = None
    deadline:          Optional[str] = None
    expected_date:     Optional[str] = None
    delivery_location: Optional[str] = None
    confirm_delivery:  Optional[bool] = None
    note:              Optional[str] = None
    items:             Optional[List[RFQItem]] = None


def _attach_items(rfq):
    rfq = rfq.copy()
    rfq["items"] = [i for i in rfq_items.values() if i["rfq_id"] == rfq["id"]]
    return rfq


@router.get("/")
def list_rfqs(status: str = None):
    result = list(rfqs.values())
    if status:
        result = [r for r in result if r["status"] == status]
    return [_attach_items(r) for r in result]


@router.post("/", status_code=201)
def create_rfq(body: RFQCreate):
    if body.supplier_id not in suppliers:
        raise HTTPException(404, "供應商不存在")

    sup = suppliers[body.supplier_id]
    sup_tax = sup.get("tax_type", "taxable")

    rfq_id = "RFQ-" + new_id()
    total = sum(i.qty * i.unit_price for i in body.items)

    rfq = {
        "id":                rfq_id,
        "supplier_id":       body.supplier_id,
        "supplier_name":     sup["name"],
        "supplier_code":     sup.get("supplier_code", ""),
        "deadline":          body.deadline,
        "expected_date":     body.expected_date,
        "delivery_location": body.delivery_location,
        "confirm_delivery":  body.confirm_delivery,
        "status":            "draft",
        "total_amount":      round(total, 2),
        "total_tax":         0.0,
        "note":              body.note,
        "po_id":             None,
        "created_at":        now(),
    }
    rfqs[rfq_id] = rfq

    total_tax = 0.0
    for item in body.items:
        # 優先：品項手填 > 庫存產品主檔 > 供應商預設
        inv_tax  = inventory.get(item.sku, {}).get("tax_type")
        tax_type = item.tax_type or inv_tax or sup_tax
        tax_rate = TAX_RATES.get(tax_type, 0.05)
        subtotal = round(item.qty * item.unit_price, 2)
        tax_amt  = round(subtotal * tax_rate, 2)
        total_tax += tax_amt

        iid = new_id()
        rfq_items[iid] = {
            **item.model_dump(),
            "id":        iid,
            "rfq_id":    rfq_id,
            "tax_type":  tax_type,
            "tax_rate":  tax_rate,
            "subtotal":  subtotal,
            "tax_amt":   tax_amt,
        }

    rfqs[rfq_id]["total_tax"] = round(total_tax, 2)
    return _attach_items(rfqs[rfq_id])


@router.get("/{rfq_id}")
def get_rfq(rfq_id: str):
    if rfq_id not in rfqs:
        raise HTTPException(404, "詢價單不存在")
    return _attach_items(rfqs[rfq_id])


@router.patch("/{rfq_id}/status")
def update_rfq_status(rfq_id: str, body: RFQStatusUpdate):
    if rfq_id not in rfqs:
        raise HTTPException(404, "詢價單不存在")
    if rfqs[rfq_id]["status"] == "confirmed":
        raise HTTPException(400, "已確認的詢價單不可再變更狀態")
    rfqs[rfq_id]["status"] = body.status
    rfqs[rfq_id]["updated_at"] = now()
    return _attach_items(rfqs[rfq_id])


@router.patch("/{rfq_id}")
def update_rfq(rfq_id: str, body: RFQUpdate):
    if rfq_id not in rfqs:
        raise HTTPException(404, "詢價單不存在")
    rfq = rfqs[rfq_id]
    if rfq["status"] != "draft":
        raise HTTPException(400, "只有草稿狀態的詢價單可以編輯")

    # 更新表頭欄位
    if body.supplier_id is not None:
        if body.supplier_id not in suppliers:
            raise HTTPException(404, "供應商不存在")
        sup = suppliers[body.supplier_id]
        rfq["supplier_id"]   = body.supplier_id
        rfq["supplier_name"] = sup["name"]
        rfq["supplier_code"] = sup.get("supplier_code", "")
    if body.deadline          is not None: rfq["deadline"]          = body.deadline
    if body.expected_date     is not None: rfq["expected_date"]     = body.expected_date
    if body.delivery_location is not None: rfq["delivery_location"] = body.delivery_location
    if body.confirm_delivery  is not None: rfq["confirm_delivery"]  = body.confirm_delivery
    if body.note              is not None: rfq["note"]              = body.note

    # 更新明細（整批替換）
    if body.items is not None:
        # 刪除舊明細
        old_keys = [k for k, v in rfq_items.items() if v["rfq_id"] == rfq_id]
        for k in old_keys:
            del rfq_items[k]

        sup = suppliers[rfq["supplier_id"]]
        sup_tax   = sup.get("tax_type", "taxable")
        total     = 0.0
        total_tax = 0.0

        for item in body.items:
            inv_tax  = inventory.get(item.sku, {}).get("tax_type")
            tax_type = item.tax_type or inv_tax or sup_tax
            tax_rate = TAX_RATES.get(tax_type, 0.05)
            subtotal = round(item.qty * item.unit_price, 2)
            tax_amt  = round(subtotal * tax_rate, 2)
            total    += subtotal
            total_tax += tax_amt

            iid = new_id()
            rfq_items[iid] = {
                **item.model_dump(),
                "id":       iid,
                "rfq_id":   rfq_id,
                "tax_type": tax_type,
                "tax_rate": tax_rate,
                "subtotal": subtotal,
                "tax_amt":  tax_amt,
            }

        rfq["total_amount"] = round(total, 2)
        rfq["total_tax"]    = round(total_tax, 2)

    rfq["updated_at"] = now()
    return _attach_items(rfq)


@router.post("/{rfq_id}/confirm", status_code=201)
def confirm_to_po(rfq_id: str):
    if rfq_id not in rfqs:
        raise HTTPException(404, "詢價單不存在")
    rfq = rfqs[rfq_id]
    if rfq["status"] == "confirmed":
        raise HTTPException(400, "此詢價單已轉為採購單")
    if rfq["status"] == "cancelled":
        raise HTTPException(400, "已取消的詢價單無法確認")
    if not rfq.get("expected_date"):
        raise HTTPException(400, "請先填寫預計到貨日")

    po_id = "PO-" + new_id()
    po = {
        "id":                po_id,
        "rfq_id":            rfq_id,
        "supplier_id":       rfq["supplier_id"],
        "supplier_name":     rfq["supplier_name"],
        "supplier_code":     rfq.get("supplier_code", ""),
        "expected_date":     rfq["expected_date"],
        "delivery_location": rfq.get("delivery_location", ""),
        "status":            "confirmed",
        "total_amount":      rfq["total_amount"],
        "total_tax":         rfq.get("total_tax", 0.0),
        "note":              rfq.get("note", ""),
        "created_at":        now(),
    }
    purchase_orders[po_id] = po

    for item in rfq_items.values():
        if item["rfq_id"] != rfq_id:
            continue
        iid = new_id()
        po_items[iid] = {
            "id":           iid,
            "po_id":        po_id,
            "sku":          item["sku"],
            "name":         item["name"],
            "qty":          item["qty"],
            "unit":         item["unit"],
            "unit_price":   item["unit_price"],
            "tax_type":     item.get("tax_type", "taxable"),
            "tax_rate":     item.get("tax_rate", 0.05),
            "subtotal":     item["subtotal"],
            "tax_amt":      item.get("tax_amt", 0.0),
            "received_qty": 0,
        }

    rfqs[rfq_id]["status"] = "confirmed"
    rfqs[rfq_id]["po_id"]  = po_id
    rfqs[rfq_id]["updated_at"] = now()

    po["items"] = [i for i in po_items.values() if i["po_id"] == po_id]
    return {"rfq": _attach_items(rfqs[rfq_id]), "po": po}
