from fastapi import APIRouter, HTTPException
from models.store import employees, departments, new_id, now
from pydantic import BaseModel
from typing import Optional
from enum import Enum

router = APIRouter()


class EmpStatus(str, Enum):
    active     = "active"
    inactive   = "inactive"
    resigned   = "resigned"

class EmpCreate(BaseModel):
    name:          str
    emp_no:        Optional[str] = None
    dept_id:       Optional[str] = None
    title:         Optional[str] = None
    hourly_rate:   float = 0.0
    start_date:    Optional[str] = None
    phone:         Optional[str] = None
    email:         Optional[str] = None
    id_no:         Optional[str] = None   # 身份證號
    bank_account:  Optional[str] = None
    note:          Optional[str] = None
    work_start:    str = "09:00"          # 正常上班時間
    work_end:      str = "18:00"          # 正常下班時間

class EmpUpdate(BaseModel):
    name:          Optional[str]   = None
    emp_no:        Optional[str]   = None
    dept_id:       Optional[str]   = None
    title:         Optional[str]   = None
    hourly_rate:   Optional[float] = None
    start_date:    Optional[str]   = None
    phone:         Optional[str]   = None
    email:         Optional[str]   = None
    bank_account:  Optional[str]   = None
    note:          Optional[str]   = None
    work_start:    Optional[str]   = None
    work_end:      Optional[str]   = None
    status:        Optional[EmpStatus] = None


@router.get("/")
def list_employees(dept_id: str = None, status: str = None):
    result = list(employees.values())
    if dept_id: result = [e for e in result if e.get("dept_id") == dept_id]
    if status:  result = [e for e in result if e.get("status") == status]
    # 附上部門名稱
    for e in result:
        dept = departments.get(e.get("dept_id", ""), {})
        e["dept_name"] = dept.get("name", "-")
    return result

@router.post("/", status_code=201)
def create_employee(body: EmpCreate):
    eid = new_id()
    emp = {**body.model_dump(), "id": eid, "status": "active", "created_at": now()}
    employees[eid] = emp
    return emp

@router.get("/{eid}")
def get_employee(eid: str):
    if eid not in employees:
        raise HTTPException(404, "員工不存在")
    emp = employees[eid].copy()
    dept = departments.get(emp.get("dept_id", ""), {})
    emp["dept_name"] = dept.get("name", "-")
    return emp

@router.patch("/{eid}")
def update_employee(eid: str, body: EmpUpdate):
    if eid not in employees:
        raise HTTPException(404, "員工不存在")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    employees[eid].update(updates)
    employees[eid]["updated_at"] = now()
    return employees[eid]
