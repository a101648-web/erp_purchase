from fastapi import APIRouter, HTTPException
from models.store import inventory

router = APIRouter()


@router.get("/")
def list_inventory(low_stock: bool = False):
    result = list(inventory.values())
    if low_stock:
        result = [i for i in result if i["qty"] < 50]
    return result


@router.get("/{sku}")
def get_inventory(sku: str):
    if sku not in inventory:
        raise HTTPException(404, "品項不存在")
    return inventory[sku]
