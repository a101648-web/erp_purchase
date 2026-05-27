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


def seed_retail_demo_volume():
    """補足零售業 demo 資料量，讓報表可以呈現跨月份趨勢。

    目標：
    - 商品資料至少 60 筆
    - 員工資料至少 30 人
    - 客戶資料至少 100 筆
    - 詢價單 / 採購單 / 銷貨單 / 發票資料分布於 2025-07 ~ 2026-05
    """
    from datetime import date, timedelta
    import random

    random.seed(20260527)

    def iso(dt: date, hour: int = 9, minute: int = 0) -> str:
        return f"{dt.isoformat()}T{hour:02d}:{minute:02d}:00"

    def money(n: float) -> float:
        return round(float(n), 2)

    # ─── 增加供應商：讓採購來源更像零售公司 ─────────────────────
    supplier_templates = [
        ("SUP-FAS-006", "城市風格服飾有限公司", "服飾", "02-2766-1122"),
        ("SUP-FAS-007", "北區鞋包配件批發", "服飾配件", "02-2558-7070"),
        ("SUP-BEA-008", "自然植萃美妝股份有限公司", "美妝", "04-2320-1888"),
        ("SUP-FOD-009", "良品食品開發有限公司", "食品", "06-312-9988"),
        ("SUP-DAY-010", "家用清潔用品供應社", "日用品", "03-526-6611"),
        ("SUP-ACC-011", "智慧生活 3C 配件商", "3C 配件", "02-8228-9000"),
        ("SUP-PKG-012", "綠色包材有限公司", "包材", "04-2388-2525"),
        ("SUP-GFT-013", "節慶禮贈品整合商", "禮盒", "07-398-2000"),
        ("SUP-KID-014", "親子生活用品批發", "親子用品", "02-2299-5118"),
        ("SUP-PET-015", "毛孩生活選品有限公司", "寵物用品", "04-2452-7755"),
    ]
    category_supplier_ids: Dict[str, list[str]] = {}
    for idx, (code, name, category, phone) in enumerate(supplier_templates, start=6):
        sid = _add_supplier({
            "name": name,
            "supplier_code": code,
            "contact": ["林小姐", "許先生", "陳經理", "王專員", "吳小姐"][idx % 5],
            "phone": phone,
            "email": f"sales{idx}@retail-supplier.demo",
            "payment_terms": [15, 30, 45][idx % 3],
            "tax_type": "taxable",
            "category": category,
        })
        category_supplier_ids.setdefault(category, []).append(sid)

    # 把既有供應商也放入可用池
    existing_suppliers = list(suppliers.values())
    for sup in existing_suppliers:
        name = sup.get("name", "")
        if "服飾" in name:
            category_supplier_ids.setdefault("服飾", []).append(sup["id"])
        elif "美妝" in name:
            category_supplier_ids.setdefault("美妝", []).append(sup["id"])
        elif "食品" in name:
            category_supplier_ids.setdefault("食品", []).append(sup["id"])
        elif "日用品" in name or "紙品" in name:
            category_supplier_ids.setdefault("日用品", []).append(sup["id"])
        elif "3C" in name:
            category_supplier_ids.setdefault("3C 配件", []).append(sup["id"])

    # ─── 增加商品主檔：補到 60+ 款 ─────────────────────────────
    product_catalog = [
        ("APP-TEE-004", "涼感機能上衣", "件", 210, "服飾", 155),
        ("APP-PNT-005", "休閒直筒長褲", "件", 180, "服飾", 360),
        ("APP-SKT-006", "高腰 A 字裙", "件", 120, "服飾", 290),
        ("APP-SHO-007", "輕量休閒鞋", "雙", 95, "服飾配件", 520),
        ("APP-BAG-008", "防潑水托特包", "個", 140, "服飾配件", 260),
        ("APP-SOC-009", "棉質短襪 3 入", "組", 220, "服飾配件", 75),
        ("APP-BLT-010", "簡約皮帶", "條", 90, "服飾配件", 180),
        ("BEA-TON-003", "舒緩化妝水 200ml", "瓶", 110, "美妝", 165),
        ("BEA-CRM-004", "保濕乳霜 50ml", "瓶", 90, "美妝", 220),
        ("BEA-CLN-005", "溫和潔面乳", "條", 130, "美妝", 105),
        ("BEA-LIP-006", "潤色護唇膏", "支", 180, "美妝", 58),
        ("BEA-SUN-007", "清爽防曬乳 SPF50", "瓶", 100, "美妝", 210),
        ("BEA-HND-008", "香氛護手霜", "支", 160, "美妝", 75),
        ("FOD-COF-003", "濾掛咖啡 10 入", "盒", 160, "食品", 145),
        ("FOD-CKI-004", "燕麥餅乾", "盒", 210, "食品", 65),
        ("FOD-DRK-005", "無糖氣泡飲", "箱", 80, "食品", 360),
        ("FOD-NOD-006", "即食拌麵 4 入", "袋", 130, "食品", 95),
        ("FOD-JAM-007", "水果果醬", "罐", 95, "食品", 88),
        ("FOD-CHO-008", "黑巧克力分享包", "包", 150, "食品", 120),
        ("DAY-WIP-003", "濕紙巾 80 抽", "包", 250, "日用品", 42),
        ("DAY-LDR-004", "洗衣膠囊 30 入", "盒", 90, "日用品", 210),
        ("DAY-DSP-005", "抗菌洗手乳", "瓶", 160, "日用品", 68),
        ("DAY-BAG-006", "環保垃圾袋", "捲", 180, "日用品", 50),
        ("DAY-TWL-007", "超細纖維毛巾", "條", 140, "日用品", 85),
        ("DAY-BOX-008", "透明收納箱", "個", 75, "日用品", 160),
        ("ACC-PHB-003", "手機支架", "個", 170, "3C 配件", 70),
        ("ACC-PBK-004", "10000mAh 行動電源", "個", 85, "3C 配件", 430),
        ("ACC-EAR-005", "藍牙耳機入門款", "副", 70, "3C 配件", 520),
        ("ACC-MSE-006", "無線滑鼠", "個", 105, "3C 配件", 190),
        ("ACC-KBD-007", "藍牙鍵盤", "個", 65, "3C 配件", 480),
        ("ACC-PAD-008", "平板保護套", "個", 90, "3C 配件", 230),
        ("PKG-BAG-001", "紙提袋 M", "個", 500, "包材", 12),
        ("PKG-BOX-002", "宅配紙箱 S", "個", 420, "包材", 18),
        ("PKG-TAP-003", "封箱膠帶", "捲", 250, "包材", 22),
        ("PKG-FIL-004", "氣泡緩衝袋", "包", 160, "包材", 95),
        ("GFT-SET-002", "美妝保養禮盒", "組", 45, "禮盒", 580),
        ("GFT-SET-003", "茶點伴手禮盒", "組", 60, "禮盒", 390),
        ("GFT-SET-004", "企業客製禮盒", "組", 35, "禮盒", 760),
        ("KID-CUP-001", "兒童吸管杯", "個", 90, "親子用品", 130),
        ("KID-BIB-002", "防水圍兜", "件", 120, "親子用品", 95),
        ("KID-TOY-003", "益智積木組", "組", 55, "親子用品", 360),
        ("PET-BWL-001", "寵物慢食碗", "個", 85, "寵物用品", 120),
        ("PET-TOY-002", "耐咬玩具", "個", 130, "寵物用品", 75),
        ("PET-SNK-003", "寵物零食", "包", 160, "寵物用品", 95),
        ("PET-PAD-004", "寵物尿布墊", "包", 90, "寵物用品", 180),
        ("SET-BDL-005", "開學季組合包", "組", 70, "禮盒", 450),
        ("SET-BDL-006", "露營小物組", "組", 50, "禮盒", 620),
        ("SET-BDL-007", "辦公桌整理組", "組", 80, "禮盒", 330),
        ("SET-BDL-008", "門市加價購組", "組", 100, "禮盒", 260),
    ]
    product_category: Dict[str, str] = {}
    product_supplier: Dict[str, str] = {}
    for sku, name, unit, qty, category, cost in product_catalog:
        _add_product({"sku": sku, "name": name, "unit": unit, "qty": qty, "unit_cost": money(cost), "tax_type": "taxable", "category": category})
        product_category[sku] = category
        pool = category_supplier_ids.get(category) or category_supplier_ids.get("日用品") or list(suppliers.keys())
        product_supplier[sku] = random.choice(pool)
    for sku in inventory.keys():
        if sku not in product_category:
            if sku.startswith("APP"):
                product_category[sku] = "服飾"
            elif sku.startswith("BEA"):
                product_category[sku] = "美妝"
            elif sku.startswith("FOD"):
                product_category[sku] = "食品"
            elif sku.startswith("DAY"):
                product_category[sku] = "日用品"
            elif sku.startswith("ACC"):
                product_category[sku] = "3C 配件"
            else:
                product_category[sku] = "禮盒"
            product_supplier[sku] = random.choice(category_supplier_ids.get(product_category[sku], list(suppliers.keys())))

    # ─── 增加客戶：補到 100 筆 ────────────────────────────────
    city_data = [
        ("台北", "台北市中山區南京東路"), ("新北", "新北市板橋區縣民大道"),
        ("桃園", "桃園市中壢區中正路"), ("新竹", "新竹市東區光復路"),
        ("台中", "台中市西屯區臺灣大道"), ("彰化", "彰化市中山路"),
        ("嘉義", "嘉義市西區民族路"), ("台南", "台南市東區崇學路"),
        ("高雄", "高雄市左營區博愛路"), ("屏東", "屏東市自由路"),
        ("宜蘭", "宜蘭市神農路"), ("花蓮", "花蓮市中山路"),
    ]
    customer_types = ["直營門市", "加盟門市", "百貨櫃位", "官方電商", "平台賣場", "企業團購", "快閃活動", "校園合作"]
    target_customer_count = 100
    existing_count = len(customers)
    for i in range(existing_count + 1, target_customer_count + 1):
        city, addr = city_data[(i - 1) % len(city_data)]
        ctype = customer_types[(i - 1) % len(customer_types)]
        if ctype in ["官方電商", "平台賣場"]:
            name = f"{city}電商出貨點 {i:03d}"
        elif ctype == "企業團購":
            name = f"{city}企業福利社 {i:03d}"
        elif ctype == "百貨櫃位":
            name = f"{city}百貨櫃位 {i:03d}"
        else:
            name = f"{city}{ctype} {i:03d}"
        cid = _add_customer({
            "name": name,
            "customer_code": f"CUS-{i:03d}",
            "tax_id": f"{random.randint(10000000, 99999999)}",
            "contact": random.choice(["陳店長", "林小姐", "王先生", "黃主任", "張經理", "吳專員"]),
            "phone": f"09{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(100,999)}",
            "email": f"customer{i:03d}@retail-demo.tw",
            "address": f"{addr} {random.randint(1, 399)} 號",
            "payment_terms": random.choice([0, 15, 30, 45]),
            "note": ctype,
            "customer_type": ctype,
            "region": city,
        })
        # 分散客戶建立時間，讓客戶列表也不像全部同一天
        customers[cid]["created_at"] = iso(date(2025, 7, 1) + timedelta(days=random.randint(0, 330)), random.randint(8, 17), random.choice([0, 15, 30, 45]))

    # ─── 增加員工：補到 30 人 ────────────────────────────────
    dept_list = list(departments.values())
    titles_by_dept = {
        "門市營運部": ["區督導", "門市店長", "副店長", "銷售顧問", "收銀人員"],
        "採購商品部": ["商品經理", "採購專員", "商品助理", "供應商管理專員"],
        "倉儲物流部": ["倉儲組長", "入庫人員", "出貨人員", "物流調度", "盤點專員"],
        "電商營運部": ["電商企劃", "平台營運", "客服專員", "內容行銷", "活動企劃"],
        "人資行政部": ["HR 專員", "行政總務", "薪資專員", "教育訓練專員"],
    }
    names = [
        "林冠廷", "陳怡安", "黃柏翰", "張雅婷", "吳承恩", "劉佳蓉", "蔡孟哲", "楊子涵", "許庭瑄", "鄭宇翔",
        "謝佳樺", "郭建宏", "曾郁婷", "羅偉倫", "葉欣怡", "潘志豪", "廖品妤", "宋家豪", "方語涵", "邱柏宇",
        "侯怡君", "洪孟軒", "賴佳琪", "余承翰", "簡郁雯", "鍾佩珊", "戴秉勳", "沈昱翔", "卓庭萱", "江哲宇",
    ]
    current_emp_count = len(employees)
    for i in range(current_emp_count + 1, 31):
        dept = dept_list[(i - 1) % len(dept_list)]
        dept_name = dept["name"]
        title = random.choice(titles_by_dept.get(dept_name, ["專員"]))
        eid = new_id()
        work_start, work_end = ("10:00", "19:00") if dept_name == "門市營運部" else (("08:30", "17:30") if dept_name == "倉儲物流部" else ("09:00", "18:00"))
        employees[eid] = {
            "id": eid,
            "name": names[i - 1],
            "emp_no": f"EMP-{i:03d}",
            "title": title,
            "hourly_rate": float(random.choice([190, 200, 220, 240, 260, 280, 300, 320])),
            "dept_id": dept["id"],
            "dept_name": dept_name,
            "work_start": work_start,
            "work_end": work_end,
            "phone": f"09{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(100,999)}",
            "email": f"emp{i:03d}@retaildemo.tw",
            "start_date": (date(2020, 1, 1) + timedelta(days=random.randint(0, 2000))).isoformat(),
            "bank_account": "",
            "id_no": "",
            "note": "零售 demo 員工資料",
            "status": "active",
            "created_at": iso(date(2025, 7, 1) + timedelta(days=random.randint(0, 330)), 9, 0),
        }

    # 出勤補足：近 3 個月，每位員工抽幾天，HR 頁面與報表較有資料感
    for emp in employees.values():
        for offset in random.sample(range(0, 75), k=5):
            day = date(2026, 3, 15) + timedelta(days=offset)
            if day.weekday() >= 5:
                continue
            aid = new_id()
            late_min = random.choice([0, 0, 0, 5, 10, 15])
            ot_hours = random.choice([0, 0, 0.5, 1.0, 1.5])
            hourly_rate = emp.get("hourly_rate", 0)
            attendance[aid] = {
                "id": aid,
                "emp_id": emp["id"],
                "emp_name": emp["name"],
                "date": day.isoformat(),
                "clock_in": emp.get("work_start", "09:00") if late_min == 0 else "09:15",
                "clock_out": "19:30" if ot_hours >= 1.0 else emp.get("work_end", "18:00"),
                "is_holiday": False,
                "late_min": late_min,
                "early_min": 0,
                "actual_hours": 8 + ot_hours,
                "ot_hours": ot_hours,
                "normal_hours": 8.0,
                "normal_pay": money(8 * hourly_rate),
                "ot_pay": money(ot_hours * hourly_rate * 1.34),
                "deduct": money(late_min * hourly_rate / 60),
                "total_pay": money(8 * hourly_rate + ot_hours * hourly_rate * 1.34 - late_min * hourly_rate / 60),
                "note": "批量 demo 出勤紀錄",
                "created_at": iso(day, 18, 30),
            }

    # ─── 交易資料：跨月份 RFQ / PO / 入庫 / 採購發票 ─────────────
    all_skus = list(inventory.keys())
    months = [date(2025, m, 8) for m in range(7, 13)] + [date(2026, m, 8) for m in range(1, 6)]
    status_cycle = ["draft", "sent", "confirmed", "partial", "received", "paid"]
    rfq_no = 0
    for mi, base_day in enumerate(months):
        for j in range(5):
            rfq_no += 1
            sku1, sku2 = random.sample(all_skus, 2)
            cat = product_category.get(sku1, "日用品")
            sid = product_supplier.get(sku1) or random.choice(category_supplier_ids.get(cat, list(suppliers.keys())))
            create_day = base_day + timedelta(days=random.randint(0, 18))
            status = status_cycle[(mi + j) % len(status_cycle)]
            items = []
            for sku in [sku1, sku2]:
                prod = inventory[sku]
                qty = random.randint(20, 180)
                unit_cost = float(prod.get("unit_cost", 100))
                items.append({
                    "sku": sku,
                    "name": prod["name"],
                    "qty": qty,
                    "unit": prod.get("unit", "件"),
                    "unit_price": money(unit_cost * random.uniform(0.96, 1.08)),
                })
            rfq_id = _add_rfq(
                sid,
                items,
                deadline=(create_day + timedelta(days=7)).isoformat(),
                expected_date=(create_day + timedelta(days=random.randint(12, 25))).isoformat(),
                delivery_location=random.choice(["台北主倉", "高雄倉", "台中轉運倉", "電商倉"]),
                status=status if status in ["draft", "sent"] else "confirmed",
                note=f"{create_day.strftime('%Y-%m')} 檔期與安全庫存補貨。",
            )
            rfqs[rfq_id]["created_at"] = iso(create_day, random.randint(9, 16), random.choice([0, 15, 30]))
            if status not in ["draft", "sent"]:
                received_map = {}
                if status == "partial":
                    received_map = {item["sku"]: max(1, int(item["qty"] * random.uniform(0.35, 0.75))) for item in items}
                elif status in ["received", "paid"]:
                    received_map = {item["sku"]: item["qty"] for item in items}
                po_status = "confirmed" if status == "confirmed" else status
                po_id = _convert_rfq_to_po(rfq_id, status=po_status, received=received_map)
                purchase_orders[po_id]["created_at"] = iso(create_day + timedelta(days=2), random.randint(9, 16), 0)
                purchase_orders[po_id]["expected_date"] = (create_day + timedelta(days=random.randint(12, 25))).isoformat()
                if status in ["partial", "received", "paid"]:
                    lines = []
                    for item in items:
                        rec_qty = received_map.get(item["sku"], 0)
                        if rec_qty:
                            lines.append({"sku": item["sku"], "name": item["name"], "received_qty": rec_qty})
                    rec_id = _add_receiving(po_id, lines, f"{create_day.strftime('%Y-%m')} 到貨驗收紀錄")
                    receiving_records[rec_id]["created_at"] = iso(create_day + timedelta(days=random.randint(13, 28)), 14, 0)
                if status in ["received", "paid"]:
                    inv_status = "paid" if status == "paid" else random.choice(["matched", "matched", "disputed"])
                    inv_id = _add_invoice(po_id, f"P-{create_day.strftime('%Y%m')}-{rfq_no:03d}", purchase_orders[po_id]["total_amount"], purchase_orders[po_id].get("total_tax", 0.0), inv_status)
                    invoices[inv_id]["invoice_date"] = (create_day + timedelta(days=random.randint(15, 30))).isoformat()
                    invoices[inv_id]["created_at"] = iso(create_day + timedelta(days=random.randint(15, 32)), 10, 0)

    # ─── 銷貨資料：100+ 張訂單，跨月份報表趨勢會明顯 ─────────────
    customer_ids = list(customers.keys())
    sales_status_cycle = ["draft", "confirmed", "partial", "shipped", "invoiced", "closed"]
    so_no = 0
    for mi, base_day in enumerate(months):
        for j in range(9):
            so_no += 1
            customer_id = random.choice(customer_ids)
            create_day = base_day + timedelta(days=random.randint(0, 20))
            selected_skus = random.sample(all_skus, k=random.choice([2, 2, 3]))
            status = sales_status_cycle[(mi + j) % len(sales_status_cycle)]
            items = []
            shipped_map = {}
            for sku in selected_skus:
                prod = inventory[sku]
                qty = random.randint(5, 60)
                price = money(float(prod.get("unit_cost", 100)) * random.uniform(1.45, 2.35))
                items.append({"sku": sku, "name": prod["name"], "qty": qty, "unit": prod.get("unit", "件"), "unit_price": price})
                if status == "partial":
                    shipped_map[sku] = max(1, int(qty * random.uniform(0.3, 0.75)))
                elif status in ["shipped", "invoiced", "closed"]:
                    shipped_map[sku] = qty
            so_id = _add_sales_order(
                customer_id,
                items,
                expected_date=(create_day + timedelta(days=random.randint(2, 10))).isoformat(),
                status=status,
                shipped=shipped_map,
                note=f"{create_day.strftime('%Y-%m')} 零售通路訂單。",
            )
            sales_orders[so_id]["created_at"] = iso(create_day, random.randint(9, 20), random.choice([0, 10, 20, 30, 40, 50]))
            if status in ["partial", "shipped", "invoiced", "closed"]:
                ship_lines = []
                for sku, qty in shipped_map.items():
                    ship_lines.append({"sku": sku, "name": inventory[sku]["name"], "shipped_qty": qty})
                ship_id = _add_shipment(so_id, ship_lines, f"{create_day.strftime('%Y-%m')} 出貨紀錄")
                shipments[ship_id]["created_at"] = iso(create_day + timedelta(days=random.randint(1, 8)), 15, 0)
            if status in ["invoiced", "closed"]:
                inv_status = "received" if status == "closed" else random.choice(["pending", "pending", "overdue"])
                inv_day = create_day + timedelta(days=random.randint(2, 12))
                due = inv_day + timedelta(days=random.choice([15, 30, 45]))
                inv_id = _add_sales_invoice(so_id, f"S-{inv_day.strftime('%Y%m')}-{so_no:03d}", sales_orders[so_id]["total_amount"], sales_orders[so_id].get("total_tax", 0.0), inv_status, due.isoformat())
                sales_invoices[inv_id]["invoice_date"] = inv_day.isoformat()
                sales_invoices[inv_id]["created_at"] = iso(inv_day, 11, 0)


seed()
seed_hr()
seed_retail_demo_volume()
