from fastapi import APIRouter, HTTPException
from models.store import departments, new_id, now
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class DeptCreate(BaseModel):
    name: str
    code: Optional[str] = None
    manager: Optional[str] = None
    note: Optional[str] = None


class DeptUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    manager: Optional[str] = None
    note: Optional[str] = None


@router.get("/")
def list_departments():
    return sorted(departments.values(), key=lambda x: x.get("created_at", ""), reverse=True)


@router.post("/", status_code=201)
def create_department(body: DeptCreate):
    did = new_id()
    departments[did] = {**body.model_dump(), "id": did, "created_at": now()}
    return departments[did]


@router.get("/{did}")
def get_department(did: str):
    if did not in departments:
        raise HTTPException(404, "部門不存在")
    return departments[did]


@router.patch("/{did}")
def update_department(did: str, body: DeptUpdate):
    if did not in departments:
        raise HTTPException(404, "部門不存在")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    departments[did].update(updates)
    departments[did]["updated_at"] = now()
    return departments[did]


@router.delete("/{did}", status_code=204)
def delete_department(did: str):
    if did not in departments:
        raise HTTPException(404, "部門不存在")
    del departments[did]
