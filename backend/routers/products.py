from fastapi import APIRouter, HTTPException
from models.store import inventory, now
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

router = APIRouter()


class TaxType(str, Enum):
    taxable = "taxable"
    zero    = "zero"
    exempt  = "exempt"


class ProductCreate(BaseModel):
    sku:       str
    name:      str
    unit:      str
    unit_cost: float = Field(ge=0)
    tax_type:  TaxType = TaxType.taxable
    qty:       float = 0


class ProductUpdate(BaseModel):
    name:      Optional[str]     = None
    unit:      Optional[str]     = None
    unit_cost: Optional[float]   = None
    tax_type:  Optional[TaxType] = None


class QtyAdjust(BaseModel):
    qty:  float
    note: Optional[str] = None


@router.get("/")
def list_products():
    return list(inventory.values())


@router.get("/{sku}")
def get_product(sku: str):
    if sku not in inventory:
        raise HTTPException(404, "商品不存在")
    return inventory[sku]


@router.post("/", status_code=201)
def create_product(body: ProductCreate):
    if body.sku in inventory:
        raise HTTPException(400, f"SKU {body.sku} 已存在")
    inventory[body.sku] = {
        "sku":        body.sku,
        "name":       body.name,
        "unit":       body.unit,
        "unit_cost":  body.unit_cost,
        "tax_type":   body.tax_type,
        "qty":        body.qty,
        "updated_at": now(),
    }
    return inventory[body.sku]


@router.patch("/{sku}")
def update_product(sku: str, body: ProductUpdate):
    if sku not in inventory:
        raise HTTPException(404, "商品不存在")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    inventory[sku].update(updates)
    inventory[sku]["updated_at"] = now()
    return inventory[sku]


@router.patch("/{sku}/qty")
def adjust_qty(sku: str, body: QtyAdjust):
    if sku not in inventory:
        raise HTTPException(404, "商品不存在")
    inventory[sku]["qty"] = body.qty
    inventory[sku]["updated_at"] = now()
    return inventory[sku]


@router.delete("/{sku}", status_code=204)
def delete_product(sku: str):
    if sku not in inventory:
        raise HTTPException(404, "商品不存在")
    del inventory[sku]


@router.post("/bulk", status_code=201)
def bulk_create(products: list[ProductCreate]):
    results = {"created": [], "skipped": []}
    for p in products:
        if p.sku in inventory:
            results["skipped"].append(p.sku)
            continue
        inventory[p.sku] = {
            "sku":        p.sku,
            "name":       p.name,
            "unit":       p.unit,
            "unit_cost":  p.unit_cost,
            "tax_type":   p.tax_type,
            "qty":        p.qty,
            "updated_at": now(),
        }
        results["created"].append(p.sku)
    return results
