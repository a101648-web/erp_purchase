from fastapi import APIRouter, HTTPException
from models.store import suppliers, new_id, now
from schemas.purchase import SupplierCreate, SupplierUpdate

router = APIRouter()


@router.get("/")
def list_suppliers():
    return list(suppliers.values())


@router.post("/", status_code=201)
def create_supplier(body: SupplierCreate):
    sid = new_id()
    record = {**body.model_dump(), "id": sid, "status": "active", "created_at": now()}
    suppliers[sid] = record
    return record


@router.get("/{sid}")
def get_supplier(sid: str):
    if sid not in suppliers:
        raise HTTPException(404, "供應商不存在")
    return suppliers[sid]


@router.patch("/{sid}")
def update_supplier(sid: str, body: SupplierUpdate):
    if sid not in suppliers:
        raise HTTPException(404, "供應商不存在")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    suppliers[sid].update(updates)
    suppliers[sid]["updated_at"] = now()
    return suppliers[sid]


@router.delete("/{sid}", status_code=204)
def delete_supplier(sid: str):
    if sid not in suppliers:
        raise HTTPException(404, "供應商不存在")
    suppliers[sid]["status"] = "inactive"
