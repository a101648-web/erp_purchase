from fastapi import APIRouter, HTTPException
from models.store import payroll, attendance, leaves, employees, new_id, now
from pydantic import BaseModel
from typing import Optional
from enum import Enum

router = APIRouter()


class PayrollStatus(str, Enum):
    draft    = "draft"
    confirmed = "confirmed"
    paid     = "paid"


class PayrollCreate(BaseModel):
    emp_id:     str
    year_month: str   # YYYY-MM
    note:       Optional[str] = None

class PayrollStatusUpdate(BaseModel):
    status: PayrollStatus


@router.get("/")
def list_payroll(year_month: str = None, status: str = None):
    result = list(payroll.values())
    if year_month: result = [p for p in result if p["year_month"] == year_month]
    if status:     result = [p for p in result if p["status"] == status]
    return sorted(result, key=lambda x: x["year_month"], reverse=True)


@router.post("/calculate", status_code=201)
def calculate_payroll(body: PayrollCreate):
    """根據出勤與請假紀錄計算當月薪資"""
    if body.emp_id not in employees:
        raise HTTPException(404, "員工不存在")

    # 檢查是否已計算過
    existing = [p for p in payroll.values() if p["emp_id"] == body.emp_id and p["year_month"] == body.year_month]
    if existing:
        raise HTTPException(400, f"{body.year_month} 薪資已計算，請先刪除再重算")

    emp = employees[body.emp_id]
    hourly_rate = emp.get("hourly_rate", 0)

    # 出勤統計
    att_records = [a for a in attendance.values()
                   if a["emp_id"] == body.emp_id and a["date"].startswith(body.year_month)]
    att_days      = len(att_records)
    normal_pay    = round(sum(r["normal_pay"]  for r in att_records), 2)
    ot_pay        = round(sum(r["ot_pay"]      for r in att_records), 2)
    deduct        = round(sum(r["deduct"]      for r in att_records), 2)
    total_hours   = round(sum(r["actual_hours"] for r in att_records), 2)
    ot_hours      = round(sum(r["ot_hours"]    for r in att_records), 2)

    # 請假薪資調整
    leave_records = [l for l in leaves.values()
                     if l["emp_id"] == body.emp_id
                     and l["status"] == "approved"
                     and l["start_date"].startswith(body.year_month)]
    leave_days    = sum(l["days"] for l in leave_records)
    # 請假薪資（依假別給薪比率計算，以日薪 = 時薪 × 8 為基準）
    daily_rate = hourly_rate * 8
    leave_pay  = round(sum(l["days"] * daily_rate * l["pay_rate"] for l in leave_records), 2)

    gross = round(normal_pay + ot_pay + leave_pay - deduct, 2)

    pid = new_id()
    record = {
        "id":           pid,
        "emp_id":       body.emp_id,
        "emp_name":     emp["name"],
        "dept_name":    emp.get("dept_name", "-"),
        "year_month":   body.year_month,
        "hourly_rate":  hourly_rate,
        "att_days":     att_days,
        "total_hours":  total_hours,
        "ot_hours":     ot_hours,
        "normal_pay":   normal_pay,
        "ot_pay":       ot_pay,
        "deduct":       deduct,
        "leave_days":   leave_days,
        "leave_pay":    leave_pay,
        "gross":        gross,
        "status":       "draft",
        "note":         body.note,
        "created_at":   now(),
    }
    payroll[pid] = record
    return record


@router.get("/{pid}")
def get_payroll(pid: str):
    if pid not in payroll:
        raise HTTPException(404, "薪資單不存在")
    return payroll[pid]


@router.patch("/{pid}/status")
def update_payroll_status(pid: str, body: PayrollStatusUpdate):
    if pid not in payroll:
        raise HTTPException(404, "薪資單不存在")
    payroll[pid]["status"] = body.status
    payroll[pid]["updated_at"] = now()
    return payroll[pid]


@router.delete("/{pid}", status_code=204)
def delete_payroll(pid: str):
    if pid not in payroll:
        raise HTTPException(404, "薪資單不存在")
    if payroll[pid]["status"] == "paid":
        raise HTTPException(400, "已發放的薪資單不可刪除")
    del payroll[pid]
