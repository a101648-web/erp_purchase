from fastapi import APIRouter, HTTPException
from models.store import leaves, employees, new_id, now
from pydantic import BaseModel
from typing import Optional
from enum import Enum

router = APIRouter()


class LeaveType(str, Enum):
    annual      = "annual"      # 特休假（全薪）
    sick        = "sick"        # 病假（半薪）
    personal    = "personal"    # 事假（無薪）
    marriage    = "marriage"    # 婚假（全薪）
    funeral     = "funeral"     # 喪假（全薪）
    official    = "official"    # 公假（全薪）
    maternity   = "maternity"   # 產假（全薪）
    paternity   = "paternity"   # 陪產假（全薪）
    menstrual   = "menstrual"   # 生理假（半薪）
    injury      = "injury"      # 公傷假（全薪）

class LeaveStatus(str, Enum):
    pending  = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"

LEAVE_INFO = {
    "annual":    {"name": "特休假", "pay_rate": 1.0,  "max_days": None, "note": "依年資遞增"},
    "sick":      {"name": "病假",   "pay_rate": 0.5,  "max_days": 30,   "note": "每年30天"},
    "personal":  {"name": "事假",   "pay_rate": 0.0,  "max_days": 14,   "note": "每年14天"},
    "marriage":  {"name": "婚假",   "pay_rate": 1.0,  "max_days": 8,    "note": "本人結婚"},
    "funeral":   {"name": "喪假",   "pay_rate": 1.0,  "max_days": 8,    "note": "依親屬關係3-8天"},
    "official":  {"name": "公假",   "pay_rate": 1.0,  "max_days": None, "note": "依實際需要"},
    "maternity": {"name": "產假",   "pay_rate": 1.0,  "max_days": 56,   "note": "8週（56天）"},
    "paternity": {"name": "陪產假", "pay_rate": 1.0,  "max_days": 7,    "note": "7天"},
    "menstrual": {"name": "生理假", "pay_rate": 0.5,  "max_days": 12,   "note": "每月1天，每年12天"},
    "injury":    {"name": "公傷假", "pay_rate": 1.0,  "max_days": None, "note": "依實際需要"},
}


class LeaveCreate(BaseModel):
    emp_id:     str
    leave_type: LeaveType
    start_date: str
    end_date:   str
    days:       float
    reason:     Optional[str] = None

class LeaveUpdate(BaseModel):
    status: LeaveStatus
    note:   Optional[str] = None


@router.get("/types")
def get_leave_types():
    return [{"type": k, **v} for k, v in LEAVE_INFO.items()]


@router.get("/")
def list_leaves(emp_id: str = None, status: str = None):
    result = list(leaves.values())
    if emp_id: result = [l for l in result if l["emp_id"] == emp_id]
    if status: result = [l for l in result if l["status"] == status]
    return sorted(result, key=lambda x: x["start_date"], reverse=True)


@router.post("/", status_code=201)
def create_leave(body: LeaveCreate):
    if body.emp_id not in employees:
        raise HTTPException(404, "員工不存在")
    emp  = employees[body.emp_id]
    info = LEAVE_INFO[body.leave_type]
    lid  = new_id()
    record = {
        "id":          lid,
        "emp_id":      body.emp_id,
        "emp_name":    emp["name"],
        "leave_type":  body.leave_type,
        "leave_name":  info["name"],
        "pay_rate":    info["pay_rate"],
        "start_date":  body.start_date,
        "end_date":    body.end_date,
        "days":        body.days,
        "reason":      body.reason,
        "status":      "pending",
        "created_at":  now(),
    }
    leaves[lid] = record
    return record


@router.patch("/{lid}")
def update_leave(lid: str, body: LeaveUpdate):
    if lid not in leaves:
        raise HTTPException(404, "請假紀錄不存在")
    leaves[lid]["status"] = body.status
    if body.note: leaves[lid]["note"] = body.note
    leaves[lid]["updated_at"] = now()
    return leaves[lid]


@router.get("/balance/{emp_id}")
def leave_balance(emp_id: str):
    """查詢員工各假別已使用天數"""
    if emp_id not in employees:
        raise HTTPException(404, "員工不存在")
    emp_leaves = [l for l in leaves.values() if l["emp_id"] == emp_id and l["status"] == "approved"]
    used = {}
    for lt in LEAVE_INFO:
        used[lt] = sum(l["days"] for l in emp_leaves if l["leave_type"] == lt)
    return {
        "emp_id":   emp_id,
        "emp_name": employees[emp_id]["name"],
        "balance":  [{
            "type":     lt,
            "name":     LEAVE_INFO[lt]["name"],
            "used":     used[lt],
            "max_days": LEAVE_INFO[lt]["max_days"],
            "note":     LEAVE_INFO[lt]["note"],
        } for lt in LEAVE_INFO]
    }
