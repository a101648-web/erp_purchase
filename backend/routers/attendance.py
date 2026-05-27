from fastapi import APIRouter, HTTPException
from models.store import attendance, employees, new_id, now
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time
import math

router = APIRouter()

NORMAL_HOURS = 8.0   # 正常工時
OT_RATE_1    = 1.34  # 加班前2小時倍率
OT_RATE_2    = 1.67  # 加班2小時後倍率


def parse_time(t: str) -> time:
    h, m = map(int, t.split(":"))
    return time(h, m)

def time_diff_minutes(t1: str, t2: str) -> float:
    """t2 - t1 in minutes"""
    h1, m1 = map(int, t1.split(":"))
    h2, m2 = map(int, t2.split(":"))
    return (h2 * 60 + m2) - (h1 * 60 + m1)

def calc_attendance(clock_in: str, clock_out: str, work_start: str, work_end: str, hourly_rate: float):
    """計算出勤各項數值"""
    # 遲到分鐘
    late_min  = max(0, time_diff_minutes(work_start, clock_in))
    # 早退分鐘
    early_min = max(0, time_diff_minutes(clock_out, work_end))
    # 實際工時（分鐘）
    actual_min = time_diff_minutes(clock_in, clock_out)
    # 正常工時（分鐘）
    normal_min = time_diff_minutes(work_start, work_end)
    # 加班分鐘
    ot_min = max(0, actual_min - normal_min)
    # 正常出勤時數
    normal_work_min = max(0, actual_min - ot_min)
    normal_hours = round(normal_work_min / 60, 2)
    # 加班費計算
    ot_hours = ot_min / 60
    ot1 = min(ot_hours, 2)
    ot2 = max(0, ot_hours - 2)
    ot_pay = round((ot1 * OT_RATE_1 + ot2 * OT_RATE_2) * hourly_rate, 2)
    # 遲到/早退扣款
    deduct = round((late_min + early_min) * hourly_rate / 60, 2)
    # 正常薪資
    normal_pay = round(normal_hours * hourly_rate, 2)

    return {
        "late_min":    late_min,
        "early_min":   early_min,
        "actual_hours": round(actual_min / 60, 2),
        "ot_hours":    round(ot_hours, 2),
        "normal_hours": normal_hours,
        "normal_pay":  normal_pay,
        "ot_pay":      ot_pay,
        "deduct":      deduct,
        "total_pay":   round(normal_pay + ot_pay - deduct, 2),
    }


class AttendanceCreate(BaseModel):
    emp_id:    str
    date:      str        # YYYY-MM-DD
    clock_in:  str        # HH:MM
    clock_out: str        # HH:MM
    is_holiday: bool = False
    note:      Optional[str] = None

class AttendanceUpdate(BaseModel):
    clock_in:  Optional[str]  = None
    clock_out: Optional[str]  = None
    note:      Optional[str]  = None


@router.get("/")
def list_attendance(emp_id: str = None, year_month: str = None):
    result = list(attendance.values())
    if emp_id:     result = [a for a in result if a["emp_id"] == emp_id]
    if year_month: result = [a for a in result if a["date"].startswith(year_month)]
    return sorted(result, key=lambda x: x["date"], reverse=True)


@router.post("/", status_code=201)
def create_attendance(body: AttendanceCreate):
    if body.emp_id not in employees:
        raise HTTPException(404, "員工不存在")

    # 檢查同一天是否已有紀錄
    existing = [a for a in attendance.values() if a["emp_id"] == body.emp_id and a["date"] == body.date]
    if existing:
        raise HTTPException(400, f"{body.date} 已有出勤紀錄")

    emp = employees[body.emp_id]
    work_start   = emp.get("work_start", "09:00")
    work_end     = emp.get("work_end",   "18:00")
    hourly_rate  = emp.get("hourly_rate", 0)

    calc = calc_attendance(body.clock_in, body.clock_out, work_start, work_end, hourly_rate)
    if body.is_holiday:
        calc["ot_pay"]    = round(calc["actual_hours"] * hourly_rate * 2, 2)
        calc["normal_pay"] = 0
        calc["deduct"]    = 0
        calc["total_pay"] = calc["ot_pay"]

    aid = new_id()
    record = {
        "id":         aid,
        "emp_id":     body.emp_id,
        "emp_name":   emp["name"],
        "date":       body.date,
        "clock_in":   body.clock_in,
        "clock_out":  body.clock_out,
        "is_holiday": body.is_holiday,
        "note":       body.note,
        **calc,
        "created_at": now(),
    }
    attendance[aid] = record
    return record


@router.patch("/{aid}")
def update_attendance(aid: str, body: AttendanceUpdate):
    if aid not in attendance:
        raise HTTPException(404, "出勤紀錄不存在")
    rec = attendance[aid]
    clock_in  = body.clock_in  or rec["clock_in"]
    clock_out = body.clock_out or rec["clock_out"]
    emp = employees[rec["emp_id"]]
    calc = calc_attendance(clock_in, clock_out, emp.get("work_start","09:00"), emp.get("work_end","18:00"), emp.get("hourly_rate",0))
    rec.update({**calc, "clock_in": clock_in, "clock_out": clock_out})
    if body.note: rec["note"] = body.note
    rec["updated_at"] = now()
    return rec


@router.get("/summary/{emp_id}/{year_month}")
def monthly_summary(emp_id: str, year_month: str):
    """月出勤統計"""
    if emp_id not in employees:
        raise HTTPException(404, "員工不存在")
    records = [a for a in attendance.values() if a["emp_id"] == emp_id and a["date"].startswith(year_month)]
    return {
        "emp_id":       emp_id,
        "emp_name":     employees[emp_id]["name"],
        "year_month":   year_month,
        "days":         len(records),
        "total_hours":  round(sum(r["actual_hours"] for r in records), 2),
        "ot_hours":     round(sum(r["ot_hours"] for r in records), 2),
        "late_days":    sum(1 for r in records if r["late_min"] > 0),
        "early_days":   sum(1 for r in records if r["early_min"] > 0),
        "total_pay":    round(sum(r["total_pay"] for r in records), 2),
        "records":      sorted(records, key=lambda x: x["date"]),
    }
