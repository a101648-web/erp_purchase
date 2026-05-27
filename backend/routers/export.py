"""
routers/export.py
產生 Excel 報表下載
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.store import (
    purchase_orders, po_items, sales_orders, so_items,
    inventory, payroll, employees, departments, suppliers, customers,
    TAX_LABELS
)
import io
import csv
from datetime import datetime

router = APIRouter()


def make_csv(headers: list, rows: list) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)
    # Add BOM for Excel UTF-8
    content = '\ufeff' + output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=export.csv'}
    )


@router.get("/purchase-orders")
def export_purchase_orders(year_month: str = None):
    """匯出採購訂單"""
    pos = list(purchase_orders.values())
    if year_month:
        pos = [p for p in pos if p.get('created_at','').startswith(year_month)]

    headers = ['訂單號', '供應商', '供應商編碼', '狀態', '預計到貨', '未稅金額', '稅額', '建立時間']
    rows = []
    for p in sorted(pos, key=lambda x: x.get('created_at',''), reverse=True):
        items = [i for i in po_items.values() if i['po_id'] == p['id']]
        tax = sum(i.get('tax_amt', 0) for i in items)
        rows.append([
            p['id'], p['supplier_name'], p.get('supplier_code',''),
            p['status'], p.get('expected_date',''),
            p['total_amount'], round(tax, 2),
            p.get('created_at','')[:10]
        ])
    return make_csv(headers, rows)


@router.get("/purchase-items")
def export_purchase_items(year_month: str = None):
    """匯出採購明細"""
    pos = list(purchase_orders.values())
    if year_month:
        pos = [p for p in pos if p.get('created_at','').startswith(year_month)]
    po_ids = {p['id'] for p in pos}

    headers = ['訂單號', '供應商', 'SKU', '品名', '數量', '單位', '單價', '稅別', '稅額', '小計']
    rows = []
    for i in po_items.values():
        if i['po_id'] not in po_ids: continue
        po = purchase_orders.get(i['po_id'], {})
        rows.append([
            i['po_id'], po.get('supplier_name',''),
            i['sku'], i['name'], i['qty'], i['unit'],
            i['unit_price'],
            TAX_LABELS.get(i.get('tax_type',''), i.get('tax_type','')),
            i.get('tax_amt', 0), i['subtotal']
        ])
    return make_csv(headers, rows)


@router.get("/sales-orders")
def export_sales_orders(year_month: str = None):
    """匯出銷貨訂單"""
    sos = list(sales_orders.values())
    if year_month:
        sos = [s for s in sos if s.get('created_at','').startswith(year_month)]

    headers = ['訂單號', '客戶', '客戶編碼', '狀態', '預計出貨', '未稅金額', '稅額', '建立時間']
    rows = []
    for s in sorted(sos, key=lambda x: x.get('created_at',''), reverse=True):
        items = [i for i in so_items.values() if i['so_id'] == s['id']]
        tax = sum(i.get('tax_amt', 0) for i in items)
        rows.append([
            s['id'], s['customer_name'], s.get('customer_code',''),
            s['status'], s.get('expected_date',''),
            s['total_amount'], round(tax, 2),
            s.get('created_at','')[:10]
        ])
    return make_csv(headers, rows)


@router.get("/inventory")
def export_inventory():
    """匯出庫存"""
    headers = ['SKU', '品名', '單位', '庫存數量', '單位成本', '庫存總值', '稅別', '更新時間']
    rows = []
    for i in sorted(inventory.values(), key=lambda x: x['sku']):
        rows.append([
            i['sku'], i['name'], i['unit'],
            i['qty'], i['unit_cost'],
            round(i['qty'] * i['unit_cost'], 2),
            TAX_LABELS.get(i.get('tax_type',''), i.get('tax_type','')),
            i.get('updated_at','')[:10]
        ])
    return make_csv(headers, rows)


@router.get("/payroll")
def export_payroll(year_month: str = None):
    """匯出薪資"""
    pays = list(payroll.values())
    if year_month:
        pays = [p for p in pays if p['year_month'] == year_month]

    headers = ['員工', '月份', '時薪', '出勤天數', '總時數', '加班時數', '正常薪資', '加班費', '請假薪資', '扣款', '實發金額', '狀態']
    rows = []
    for p in sorted(pays, key=lambda x: (x['year_month'], x['emp_name'])):
        rows.append([
            p['emp_name'], p['year_month'], p['hourly_rate'],
            p['att_days'], p['total_hours'], p['ot_hours'],
            p['normal_pay'], p['ot_pay'], p['leave_pay'],
            p['deduct'], p['gross'], p['status']
        ])
    return make_csv(headers, rows)


@router.get("/suppliers")
def export_suppliers():
    """匯出供應商"""
    headers = ['編碼', '公司名稱', '聯絡人', '電話', 'Email', '付款天數', '預設稅別', '狀態']
    rows = [[
        s.get('supplier_code',''), s['name'], s['contact'],
        s['phone'], s['email'], s['payment_terms'],
        TAX_LABELS.get(s.get('tax_type',''), ''),
        s['status']
    ] for s in suppliers.values()]
    return make_csv(headers, rows)


@router.get("/customers")
def export_customers():
    """匯出客戶"""
    headers = ['編碼', '公司名稱', '統編', '聯絡人', '電話', 'Email', '地址', '付款天數', '狀態']
    rows = [[
        c.get('customer_code',''), c['name'], c.get('tax_id',''),
        c['contact'], c['phone'], c['email'],
        c.get('address',''), c['payment_terms'], c['status']
    ] for c in customers.values()]
    return make_csv(headers, rows)
