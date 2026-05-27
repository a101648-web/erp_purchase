from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import (
    suppliers, rfqs, purchase_orders, receiving, invoices, inventory, products,
    customers, sales_orders, shipments, sales_invoices,
    departments, employees, attendance, leaves, payroll, export
)

app = FastAPI(title="ERP 系統 API", version="4.0.0")
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 進貨模組
app.include_router(suppliers.router,       prefix="/api/suppliers",       tags=["供應商管理"])
app.include_router(rfqs.router,            prefix="/api/rfqs",            tags=["詢價單"])
app.include_router(purchase_orders.router, prefix="/api/purchase-orders", tags=["採購訂單"])
app.include_router(receiving.router,       prefix="/api/receiving",        tags=["入庫作業"])
app.include_router(invoices.router,        prefix="/api/invoices",         tags=["採購發票"])
app.include_router(inventory.router,       prefix="/api/inventory",        tags=["庫存管理"])
app.include_router(products.router,        prefix="/api/products",         tags=["商品管理"])

# 銷貨模組
app.include_router(customers.router,       prefix="/api/customers",        tags=["客戶管理"])
app.include_router(sales_orders.router,    prefix="/api/sales-orders",     tags=["銷貨訂單"])
app.include_router(shipments.router,       prefix="/api/shipments",        tags=["出貨作業"])
app.include_router(sales_invoices.router,  prefix="/api/sales-invoices",   tags=["銷貨發票"])

# 人資模組
app.include_router(departments.router,     prefix="/api/departments",      tags=["部門管理"])
app.include_router(employees.router,       prefix="/api/employees",        tags=["員工管理"])
app.include_router(attendance.router,      prefix="/api/attendance",       tags=["出勤管理"])
app.include_router(leaves.router,          prefix="/api/leaves",           tags=["請假管理"])
app.include_router(payroll.router,         prefix="/api/payroll",          tags=["薪資管理"])

app.include_router(export.router, prefix="/api/export", tags=["匯出報表"])

@app.get("/health")
def health():
    return {"status": "ok", "version": "4.0.0"}

@app.get("/", response_class=HTMLResponse)
def frontend_home():
    index_path = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "index.html"
    return index_path.read_text(encoding="utf-8")
