"""
models/store.py - In-memory 資料層

此 demo 採用記憶體資料，重啟服務後會重新載入種子資料。
資料情境改為零售業：服飾、日用品、食品、美妝、3C 配件與門市/電商流程。
"""
from datetime import datetime
from typing import Dict, Any
import uuid


def new_id() -> str:
    return str(uuid.uuid4())[:8].upper()


def now() -> str:
    return datetime.now().isoformat()


TAX_RATES  = {"taxable": 0.05, "zero": 0.0, "exempt": 0.0}
TAX_LABELS = {"taxable": "應稅 5%", "zero": "零稅率", "exempt": "免稅"}

# ─── 進貨模組 ──────────────────────────────────────────
suppliers:         Dict[str, Any] = {}
rfqs:              Dict[str, Any] = {}
rfq_items:         Dict[str, Any] = {}
purchase_orders:   Dict[str, Any] = {}
po_items:          Dict[str, Any] = {}
receiving_records: Dict[str, Any] = {}
invoices:          Dict[str, Any] = {}
inventory:         Dict[str, Any] = {}

# ─── 銷貨模組 ──────────────────────────────────────────
customers:         Dict[str, Any] = {}
sales_orders:      Dict[str, Any] = {}
so_items:          Dict[str, Any] = {}
shipments:         Dict[str, Any] = {}
sales_invoices:    Dict[str, Any] = {}

# ─── 人資模組資料表 ────────────────────────────────────
departments: Dict[str, Any] = {}
employees:   Dict[str, Any] = {}
attendance:  Dict[str, Any] = {}
leaves:      Dict[str, Any] = {}
payroll:     Dict[str, Any] = {}


def _add_supplier(data: Dict[str, Any]) -> str:
    sid = new_id()
    suppliers[sid] = {**data, "id": sid, "status": "active", "created_at": now()}
    return sid


def _add_customer(data: Dict[str, Any]) -> str:
    cid = new_id()
    customers[cid] = {**data, "id": cid, "status": "active", "created_at": now()}
    return cid


def _add_product(data: Dict[str, Any]) -> str:
    inventory[data["sku"]] = {**data, "updated_at": now()}
    return data["sku"]


def _add_rfq(supplier_id: str, items: list[Dict[str, Any]], **meta) -> str:
    sup = suppliers[supplier_id]
    rfq_id = "RFQ-" + new_id()
    total = round(sum(i["qty"] * i["unit_price"] for i in items), 2)
    total_tax = 0.0
    rfqs[rfq_id] = {
        "id":                rfq_id,
        "supplier_id":       supplier_id,
        "supplier_name":     sup["name"],
        "supplier_code":     sup.get("supplier_code", ""),
        "deadline":          meta.get("deadline"),
        "expected_date":     meta.get("expected_date"),
        "delivery_location": meta.get("delivery_location", "主倉"),
        "confirm_delivery":  meta.get("confirm_delivery", True),
        "status":            meta.get("status", "draft"),
        "total_amount":      total,
        "total_tax":         0.0,
        "note":              meta.get("note", ""),
        "po_id":             None,
        "created_at":        now(),
    }
    for item in items:
        sku = item["sku"]
        tax_type = item.get("tax_type") or inventory.get(sku, {}).get("tax_type") or sup.get("tax_type", "taxable")
        tax_rate = TAX_RATES.get(tax_type, 0.05)
        subtotal = round(item["qty"] * item["unit_price"], 2)
        tax_amt = round(subtotal * tax_rate, 2)
        total_tax += tax_amt
        iid = new_id()
        rfq_items[iid] = {
            **item,
            "id": iid,
            "rfq_id": rfq_id,
            "tax_type": tax_type,
            "tax_rate": tax_rate,
            "subtotal": subtotal,
            "tax_amt": tax_amt,
        }
    rfqs[rfq_id]["total_tax"] = round(total_tax, 2)
    return rfq_id


def _convert_rfq_to_po(rfq_id: str, status: str = "confirmed", received: Dict[str, int] | None = None) -> str:
    rfq = rfqs[rfq_id]
    po_id = "PO-" + new_id()
    purchase_orders[po_id] = {
        "id":                po_id,
        "rfq_id":            rfq_id,
        "supplier_id":       rfq["supplier_id"],
        "supplier_name":     rfq["supplier_name"],
        "supplier_code":     rfq.get("supplier_code", ""),
        "expected_date":     rfq.get("expected_date"),
        "delivery_location": rfq.get("delivery_location", "主倉"),
        "status":            status,
        "total_amount":      rfq["total_amount"],
        "total_tax":         rfq.get("total_tax", 0.0),
        "note":              rfq.get("note", ""),
        "created_at":        now(),
    }
    received = received or {}
    for item in [i for i in rfq_items.values() if i["rfq_id"] == rfq_id]:
        iid = new_id()
        po_items[iid] = {
            "id":           iid,
            "po_id":        po_id,
            "sku":          item["sku"],
            "name":         item["name"],
            "qty":          item["qty"],
            "unit":         item["unit"],
            "unit_price":   item["unit_price"],
            "tax_type":     item.get("tax_type", "taxable"),
            "tax_rate":     item.get("tax_rate", 0.05),
            "subtotal":     item["subtotal"],
            "tax_amt":      item.get("tax_amt", 0.0),
            "received_qty": received.get(item["sku"], 0),
        }
    rfq["status"] = "confirmed"
    rfq["po_id"] = po_id
    rfq["updated_at"] = now()
    return po_id


def _add_receiving(po_id: str, lines: list[Dict[str, Any]], note: str = "") -> str:
    rec_id = "REC-" + new_id()
    receiving_records[rec_id] = {"id": rec_id, "po_id": po_id, "lines": lines, "note": note, "created_at": now()}
    return rec_id


def _add_invoice(po_id: str, invoice_no: str, amount: float, tax: float, status: str = "matched") -> str:
    po = purchase_orders[po_id]
    inv_id = "INV-" + new_id()
    total = round(amount + tax, 2)
    invoices[inv_id] = {
        "id": inv_id,
        "po_id": po_id,
        "supplier_name": po["supplier_name"],
        "invoice_no": invoice_no,
        "invoice_date": "2026-05-20",
        "amount": amount,
        "tax": tax,
        "total": total,
        "po_total": po["total_amount"],
        "status": status,
        "match_note": "金額相符，自動對帳" if status in ["matched", "paid"] else f"金額不符（採購單 {po['total_amount']}，發票 {total}）",
        "created_at": now(),
    }
    return inv_id


def _add_sales_order(customer_id: str, items: list[Dict[str, Any]], **meta) -> str:
    cus = customers[customer_id]
    so_id = "SO-" + new_id()
    total = round(sum(i["qty"] * i["unit_price"] for i in items), 2)
    total_tax = 0.0
    sales_orders[so_id] = {
        "id":               so_id,
        "customer_id":      customer_id,
        "customer_name":    cus["name"],
        "customer_code":    cus.get("customer_code", ""),
        "expected_date":    meta.get("expected_date"),
        "delivery_address": meta.get("delivery_address") or cus.get("address", ""),
        "status":           meta.get("status", "draft"),
        "total_amount":     total,
        "total_tax":        0.0,
        "note":             meta.get("note", ""),
        "created_at":       now(),
    }
    for item in items:
        sku = item["sku"]
        tax_type = item.get("tax_type") or inventory.get(sku, {}).get("tax_type", "taxable")
        tax_rate = TAX_RATES.get(tax_type, 0.05)
        subtotal = round(item["qty"] * item["unit_price"], 2)
        tax_amt = round(subtotal * tax_rate, 2)
        total_tax += tax_amt
        iid = new_id()
        so_items[iid] = {
            **item,
            "id": iid,
            "so_id": so_id,
            "tax_type": tax_type,
            "tax_rate": tax_rate,
            "subtotal": subtotal,
            "tax_amt": tax_amt,
            "shipped_qty": meta.get("shipped", {}).get(sku, 0),
        }
    sales_orders[so_id]["total_tax"] = round(total_tax, 2)
    return so_id


def _add_shipment(so_id: str, lines: list[Dict[str, Any]], note: str = "") -> str:
    ship_id = "SHIP-" + new_id()
    shipments[ship_id] = {"id": ship_id, "so_id": so_id, "lines": lines, "note": note, "created_at": now()}
    return ship_id


def _add_sales_invoice(so_id: str, invoice_no: str, amount: float, tax: float, status: str, due_date: str) -> str:
    so = sales_orders[so_id]
    inv_id = "SINV-" + new_id()
    sales_invoices[inv_id] = {
        "id": inv_id,
        "so_id": so_id,
        "customer_name": so["customer_name"],
        "invoice_no": invoice_no,
        "invoice_date": "2026-05-21",
        "due_date": due_date,
        "amount": amount,
        "tax": tax,
        "total": round(amount + tax, 2),
        "status": status,
        "created_at": now(),
    }
    return inv_id


def seed():
    # 供應商：零售業常見品類
    fashion = _add_supplier({"name": "潮流服飾批發有限公司", "supplier_code": "SUP-FAS-001", "contact": "陳怡君", "phone": "02-2711-8899", "email": "service@style-wholesale.tw", "payment_terms": 30, "tax_type": "taxable"})
    beauty = _add_supplier({"name": "美妝生活供應股份有限公司", "supplier_code": "SUP-BEA-002", "contact": "林柏宏", "phone": "04-2255-1688", "email": "sales@beautylife.tw", "payment_terms": 45, "tax_type": "taxable"})
    food = _add_supplier({"name": "台灣食品物流有限公司", "supplier_code": "SUP-FOD-003", "contact": "黃雅婷", "phone": "07-3322-889", "email": "order@foodlog.tw", "payment_terms": 15, "tax_type": "taxable"})
    daily = _add_supplier({"name": "日用品紙品批發商行", "supplier_code": "SUP-DAY-004", "contact": "張志明", "phone": "03-5588-012", "email": "contact@dailypro.tw", "payment_terms": 30, "tax_type": "taxable"})
    gadget = _add_supplier({"name": "3C 配件總匯", "supplier_code": "SUP-ACC-005", "contact": "吳佳蓉", "phone": "02-2999-7111", "email": "sales@accmall.tw", "payment_terms": 30, "tax_type": "taxable"})

    # 商品主檔與庫存
    for item in [
        {"sku": "APP-TEE-001", "name": "素色棉質 T-Shirt", "unit": "件", "qty": 180, "unit_cost": 180.0, "tax_type": "taxable"},
        {"sku": "APP-JKT-002", "name": "輕量防潑水外套", "unit": "件", "qty": 45, "unit_cost": 620.0, "tax_type": "taxable"},
        {"sku": "APP-CAP-003", "name": "經典棒球帽", "unit": "頂", "qty": 90, "unit_cost": 160.0, "tax_type": "taxable"},
        {"sku": "BEA-SER-001", "name": "保濕精華液 30ml", "unit": "瓶", "qty": 70, "unit_cost": 260.0, "tax_type": "taxable"},
        {"sku": "BEA-MSK-002", "name": "植萃面膜 5 入", "unit": "盒", "qty": 120, "unit_cost": 95.0, "tax_type": "taxable"},
        {"sku": "FOD-TEA-001", "name": "冷泡茶包 20 入", "unit": "盒", "qty": 150, "unit_cost": 110.0, "tax_type": "taxable"},
        {"sku": "FOD-SNK-002", "name": "堅果隨手包", "unit": "包", "qty": 260, "unit_cost": 32.0, "tax_type": "taxable"},
        {"sku": "DAY-TIS-001", "name": "抽取式衛生紙 100 抽", "unit": "串", "qty": 85, "unit_cost": 135.0, "tax_type": "taxable"},
        {"sku": "DAY-CLN-002", "name": "多用途清潔噴霧", "unit": "瓶", "qty": 110, "unit_cost": 78.0, "tax_type": "taxable"},
        {"sku": "ACC-CAB-001", "name": "USB-C 快充線 1.5m", "unit": "條", "qty": 210, "unit_cost": 75.0, "tax_type": "taxable"},
        {"sku": "ACC-CHG-002", "name": "20W 快充頭", "unit": "個", "qty": 95, "unit_cost": 180.0, "tax_type": "taxable"},
        {"sku": "SET-GFT-001", "name": "節慶禮盒組", "unit": "組", "qty": 35, "unit_cost": 420.0, "tax_type": "taxable"},
    ]:
        _add_product(item)

    # 客戶：門市、電商、企業採購
    store_a = _add_customer({"name": "台北信義旗艦店", "customer_code": "CUS-STORE-001", "tax_id": "24567891", "contact": "周店長", "phone": "02-8787-3000", "email": "xinyi-store@retaildemo.tw", "address": "台北市信義區松高路 11 號", "payment_terms": 0, "note": "直營門市"})
    store_b = _add_customer({"name": "高雄漢神門市", "customer_code": "CUS-STORE-002", "tax_id": "53421987", "contact": "許店長", "phone": "07-555-9000", "email": "kaohsiung-store@retaildemo.tw", "address": "高雄市左營區博愛二路 777 號", "payment_terms": 0, "note": "直營門市"})
    ecommerce = _add_customer({"name": "官方電商倉", "customer_code": "CUS-EC-003", "tax_id": "81234567", "contact": "電商營運組", "phone": "02-2211-8899", "email": "ec-ops@retaildemo.tw", "address": "新北市新店區寶中路 88 號", "payment_terms": 15, "note": "線上訂單出貨倉"})
    corp = _add_customer({"name": "晨星企業福委會", "customer_code": "CUS-B2B-004", "tax_id": "70661234", "contact": "何小姐", "phone": "03-666-1688", "email": "welfare@morningstar.tw", "address": "新竹市東區園區二路 1 號", "payment_terms": 30, "note": "企業團購"})

    # 採購流程 demo：草稿、已傳送、已確認、部分入庫、已入庫、付款
    _add_rfq(fashion, [
        {"sku": "APP-TEE-001", "name": "素色棉質 T-Shirt", "qty": 80, "unit": "件", "unit_price": 175},
        {"sku": "APP-CAP-003", "name": "經典棒球帽", "qty": 60, "unit": "頂", "unit_price": 155},
    ], deadline="2026-05-30", expected_date="2026-06-04", delivery_location="台北主倉", status="draft", note="夏季活動備貨，待供應商報價確認。")
    _add_rfq(beauty, [
        {"sku": "BEA-SER-001", "name": "保濕精華液 30ml", "qty": 50, "unit": "瓶", "unit_price": 255},
        {"sku": "BEA-MSK-002", "name": "植萃面膜 5 入", "qty": 100, "unit": "盒", "unit_price": 92},
    ], deadline="2026-05-29", expected_date="2026-06-03", delivery_location="台北主倉", status="sent", note="檔期補貨，已寄出詢價。")

    rfq_food = _add_rfq(food, [
        {"sku": "FOD-TEA-001", "name": "冷泡茶包 20 入", "qty": 120, "unit": "盒", "unit_price": 108},
        {"sku": "FOD-SNK-002", "name": "堅果隨手包", "qty": 300, "unit": "包", "unit_price": 30},
    ], deadline="2026-05-18", expected_date="2026-05-25", delivery_location="台北主倉", status="confirmed", note="端午連假前補貨。")
    po_food = _convert_rfq_to_po(rfq_food, status="received", received={"FOD-TEA-001": 120, "FOD-SNK-002": 300})
    _add_receiving(po_food, [{"sku": "FOD-TEA-001", "name": "冷泡茶包 20 入", "received_qty": 120}, {"sku": "FOD-SNK-002", "name": "堅果隨手包", "received_qty": 300}], "全數入庫，效期已抽查。")
    _add_invoice(po_food, "FO-20260520-001", 21960, 1098, "paid")

    rfq_daily = _add_rfq(daily, [
        {"sku": "DAY-TIS-001", "name": "抽取式衛生紙 100 抽", "qty": 100, "unit": "串", "unit_price": 132},
        {"sku": "DAY-CLN-002", "name": "多用途清潔噴霧", "qty": 80, "unit": "瓶", "unit_price": 76},
    ], deadline="2026-05-17", expected_date="2026-05-28", delivery_location="高雄倉", status="confirmed", note="南區門市補貨。")
    po_daily = _convert_rfq_to_po(rfq_daily, status="partial", received={"DAY-TIS-001": 60, "DAY-CLN-002": 20})
    _add_receiving(po_daily, [{"sku": "DAY-TIS-001", "name": "抽取式衛生紙 100 抽", "received_qty": 60}, {"sku": "DAY-CLN-002", "name": "多用途清潔噴霧", "received_qty": 20}], "第一批到貨，清潔噴霧缺貨待補。")
    _add_invoice(po_daily, "DA-20260522-018", 19500, 975, "disputed")

    rfq_gadget = _add_rfq(gadget, [
        {"sku": "ACC-CAB-001", "name": "USB-C 快充線 1.5m", "qty": 150, "unit": "條", "unit_price": 72},
        {"sku": "ACC-CHG-002", "name": "20W 快充頭", "qty": 80, "unit": "個", "unit_price": 175},
    ], deadline="2026-05-19", expected_date="2026-06-01", delivery_location="台北主倉", status="confirmed", note="電商熱銷品補貨。")
    _convert_rfq_to_po(rfq_gadget, status="confirmed")

    # 銷貨流程 demo
    _add_sales_order(store_a, [
        {"sku": "APP-TEE-001", "name": "素色棉質 T-Shirt", "qty": 40, "unit": "件", "unit_price": 390},
        {"sku": "APP-CAP-003", "name": "經典棒球帽", "qty": 25, "unit": "頂", "unit_price": 320},
    ], expected_date="2026-05-29", status="draft", note="門市夏季陳列補貨。")

    so_ec = _add_sales_order(ecommerce, [
        {"sku": "ACC-CAB-001", "name": "USB-C 快充線 1.5m", "qty": 60, "unit": "條", "unit_price": 199},
        {"sku": "ACC-CHG-002", "name": "20W 快充頭", "qty": 40, "unit": "個", "unit_price": 399},
    ], expected_date="2026-05-27", status="confirmed", note="官方電商週末檔期備貨。")

    so_ks = _add_sales_order(store_b, [
        {"sku": "DAY-TIS-001", "name": "抽取式衛生紙 100 抽", "qty": 35, "unit": "串", "unit_price": 199},
        {"sku": "DAY-CLN-002", "name": "多用途清潔噴霧", "qty": 30, "unit": "瓶", "unit_price": 159},
    ], expected_date="2026-05-23", status="partial", shipped={"DAY-TIS-001": 20, "DAY-CLN-002": 10}, note="第一批已出貨，剩餘待調撥。")
    _add_shipment(so_ks, [{"sku": "DAY-TIS-001", "name": "抽取式衛生紙 100 抽", "shipped_qty": 20}, {"sku": "DAY-CLN-002", "name": "多用途清潔噴霧", "shipped_qty": 10}], "南區門市先出第一批。")

    so_corp = _add_sales_order(corp, [
        {"sku": "SET-GFT-001", "name": "節慶禮盒組", "qty": 30, "unit": "組", "unit_price": 880},
        {"sku": "FOD-TEA-001", "name": "冷泡茶包 20 入", "qty": 30, "unit": "盒", "unit_price": 260},
    ], expected_date="2026-05-20", status="shipped", shipped={"SET-GFT-001": 30, "FOD-TEA-001": 30}, note="企業團購已完成出貨。")
    _add_shipment(so_corp, [{"sku": "SET-GFT-001", "name": "節慶禮盒組", "shipped_qty": 30}, {"sku": "FOD-TEA-001", "name": "冷泡茶包 20 入", "shipped_qty": 30}], "企業團購一次出貨。")
    _add_sales_invoice(so_corp, "SA-20260521-006", sales_orders[so_corp]["total_amount"], sales_orders[so_corp]["total_tax"], "received", "2026-06-20")
    _add_sales_invoice(so_ks, "SA-20260522-011", sales_orders[so_ks]["total_amount"], sales_orders[so_ks]["total_tax"], "pending", "2026-06-06")
    _add_sales_invoice(so_ec, "SA-20260420-089", sales_orders[so_ec]["total_amount"], sales_orders[so_ec]["total_tax"], "overdue", "2026-05-20")


def seed_hr():
    # 部門
    dept_ids = []
    for d in [
        {"name": "門市營運部", "code": "OPS", "manager": "林佩珊", "note": "門市排班、銷售與現場營運"},
        {"name": "採購商品部", "code": "MD", "manager": "吳承翰", "note": "商品開發、供應商與補貨"},
        {"name": "倉儲物流部", "code": "WH", "manager": "陳冠宇", "note": "入庫、出貨、調撥與盤點"},
        {"name": "電商營運部", "code": "EC", "manager": "謝宜庭", "note": "官網、平台訂單與活動"},
        {"name": "人資行政部", "code": "HR", "manager": "張雅雯", "note": "人事、出勤、薪資"},
    ]:
        did = new_id()
        departments[did] = {**d, "id": did, "created_at": now()}
        dept_ids.append(did)

    emp_seed = [
        {"name": "王小明", "emp_no": "EMP-001", "title": "門市店長", "hourly_rate": 260.0, "dept_id": dept_ids[0], "work_start": "10:00", "work_end": "19:00", "phone": "0912-345-678", "email": "ming@retaildemo.tw", "start_date": "2022-01-01"},
        {"name": "李美玲", "emp_no": "EMP-002", "title": "採購專員", "hourly_rate": 240.0, "dept_id": dept_ids[1], "work_start": "09:00", "work_end": "18:00", "phone": "0923-456-789", "email": "mei@retaildemo.tw", "start_date": "2023-03-01"},
        {"name": "陳大偉", "emp_no": "EMP-003", "title": "倉儲主管", "hourly_rate": 300.0, "dept_id": dept_ids[2], "work_start": "08:30", "work_end": "17:30", "phone": "0934-567-890", "email": "wei@retaildemo.tw", "start_date": "2021-06-01"},
        {"name": "林佳穎", "emp_no": "EMP-004", "title": "電商營運", "hourly_rate": 250.0, "dept_id": dept_ids[3], "work_start": "09:30", "work_end": "18:30", "phone": "0955-123-888", "email": "cherry@retaildemo.tw", "start_date": "2024-02-15"},
        {"name": "周品安", "emp_no": "EMP-005", "title": "HR 專員", "hourly_rate": 235.0, "dept_id": dept_ids[4], "work_start": "09:00", "work_end": "18:00", "phone": "0966-987-321", "email": "hr@retaildemo.tw", "start_date": "2024-08-01"},
    ]
    emp_ids = []
    for e in emp_seed:
        eid = new_id()
        dept = departments[e["dept_id"]]
        employees[eid] = {
            **e,
            "id": eid,
            "dept_name": dept["name"],
            "bank_account": "",
            "id_no": "",
            "note": "demo 資料",
            "status": "active",
            "created_at": now(),
        }
        emp_ids.append(eid)

    # 出勤與請假 demo
    for eid, emp in list(employees.items())[:3]:
        for day, times in [("2026-05-20", (emp.get("work_start", "09:00"), emp.get("work_end", "18:00"))), ("2026-05-21", (emp.get("work_start", "09:00"), "19:30")), ("2026-05-22", ("09:15", emp.get("work_end", "18:00")) )]:
            aid = new_id()
            hourly_rate = emp.get("hourly_rate", 0)
            attendance[aid] = {
                "id": aid,
                "emp_id": eid,
                "emp_name": emp["name"],
                "date": day,
                "clock_in": times[0],
                "clock_out": times[1],
                "is_holiday": False,
                "late_min": 15 if times[0] == "09:15" else 0,
                "early_min": 0,
                "actual_hours": 8.0 if times[1] != "19:30" else 9.5,
                "ot_hours": 0 if times[1] != "19:30" else 1.5,
                "normal_hours": 8.0,
                "normal_pay": round(8 * hourly_rate, 2),
                "ot_pay": 0 if times[1] != "19:30" else round(1.5 * hourly_rate * 1.34, 2),
                "deduct": round(15 * hourly_rate / 60, 2) if times[0] == "09:15" else 0,
                "total_pay": round(8 * hourly_rate, 2),
                "note": "demo 出勤紀錄",
                "created_at": now(),
            }
    lid = new_id()
    leaves[lid] = {"id": lid, "emp_id": emp_ids[1], "emp_name": employees[emp_ids[1]]["name"], "leave_type": "annual", "leave_name": "特休假", "pay_rate": 1.0, "start_date": "2026-05-28", "end_date": "2026-05-28", "days": 1, "reason": "家庭行程", "status": "pending", "created_at": now()}


seed()
seed_hr()
