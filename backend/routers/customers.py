from fastapi import APIRouter, HTTPException
from models.store import customers, new_id, now
from schemas.purchase import CustomerCreate, CustomerUpdate

router = APIRouter()


@router.get("/")
def list_customers():
    return list(customers.values())


@router.post("/", status_code=201)
def create_customer(body: CustomerCreate):
    cid = new_id()
    record = {**body.model_dump(), "id": cid, "status": "active", "created_at": now()}
    customers[cid] = record
    return record


@router.get("/{cid}")
def get_customer(cid: str):
    if cid not in customers:
        raise HTTPException(404, "客戶不存在")
    return customers[cid]


@router.patch("/{cid}")
def update_customer(cid: str, body: CustomerUpdate):
    if cid not in customers:
        raise HTTPException(404, "客戶不存在")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    customers[cid].update(updates)
    customers[cid]["updated_at"] = now()
    return customers[cid]
