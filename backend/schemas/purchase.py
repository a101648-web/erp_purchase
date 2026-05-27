from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class SupplierStatus(str, Enum):
    active   = "active"
    inactive = "inactive"

class TaxType(str, Enum):
    taxable = "taxable"
    zero    = "zero"
    exempt  = "exempt"

class RFQStatus(str, Enum):
    draft     = "draft"
    sent      = "sent"
    confirmed = "confirmed"
    cancelled = "cancelled"

class POStatus(str, Enum):
    confirmed = "confirmed"
    partial   = "partial"
    received  = "received"
    closed    = "closed"

class InvoiceStatus(str, Enum):
    pending  = "pending"
    matched  = "matched"
    paid     = "paid"
    disputed = "disputed"

class CustomerStatus(str, Enum):
    active   = "active"
    inactive = "inactive"

class SOStatus(str, Enum):
    draft     = "draft"
    confirmed = "confirmed"
    partial   = "partial"
    shipped   = "shipped"
    closed    = "closed"

class SalesInvoiceStatus(str, Enum):
    pending  = "pending"
    received = "received"
    overdue  = "overdue"


# ── 供應商 ────────────────────────────────────────────
class SupplierCreate(BaseModel):
    name:          str
    supplier_code: Optional[str] = None
    contact:       str
    phone:         str
    email:         str
    payment_terms: int = Field(30)
    tax_type:      TaxType = TaxType.taxable

class SupplierUpdate(BaseModel):
    supplier_code: Optional[str]      = None
    contact:       Optional[str]      = None
    phone:         Optional[str]      = None
    email:         Optional[str]      = None
    payment_terms: Optional[int]      = None
    tax_type:      Optional[TaxType]  = None
    status:        Optional[SupplierStatus] = None


# ── 詢價單 ────────────────────────────────────────────
class RFQItem(BaseModel):
    sku:        str
    name:       str
    qty:        int   = Field(gt=0)
    unit:       str
    unit_price: float = Field(ge=0)
    tax_type:   Optional[TaxType] = None

class RFQCreate(BaseModel):
    supplier_id:       str
    deadline:          Optional[str] = None
    expected_date:     Optional[str] = None
    delivery_location: Optional[str] = None
    confirm_delivery:  bool = False
    items:             List[RFQItem]
    note:              Optional[str] = None

class RFQStatusUpdate(BaseModel):
    status: RFQStatus


# ── 採購訂單 ──────────────────────────────────────────
class POItem(BaseModel):
    sku:        str
    name:       str
    qty:        int   = Field(gt=0)
    unit:       str
    unit_price: float = Field(gt=0)
    tax_type:   Optional[TaxType] = None

class POCreate(BaseModel):
    supplier_id:       str
    expected_date:     str
    delivery_location: Optional[str] = None
    items:             List[POItem]
    note:              Optional[str] = None

class POStatusUpdate(BaseModel):
    status: POStatus


# ── 入庫 ──────────────────────────────────────────────
class ReceivingItem(BaseModel):
    sku:          str
    received_qty: int = Field(gt=0)

class ReceivingCreate(BaseModel):
    po_id:  str
    items:  List[ReceivingItem]
    note:   Optional[str] = None


# ── 採購發票 ──────────────────────────────────────────
class InvoiceCreate(BaseModel):
    po_id:        str
    invoice_no:   str
    invoice_date: str
    amount:       float = Field(gt=0)
    tax:          float = 0.0

class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus


# ── 客戶 ──────────────────────────────────────────────
class CustomerCreate(BaseModel):
    name:          str
    customer_code: Optional[str] = None
    tax_id:        Optional[str] = None
    contact:       str
    phone:         str
    email:         str
    address:       Optional[str] = None
    payment_terms: int = Field(30)
    note:          Optional[str] = None

class CustomerUpdate(BaseModel):
    customer_code: Optional[str] = None
    tax_id:        Optional[str] = None
    contact:       Optional[str] = None
    phone:         Optional[str] = None
    email:         Optional[str] = None
    address:       Optional[str] = None
    payment_terms: Optional[int] = None
    note:          Optional[str] = None
    status:        Optional[CustomerStatus] = None


# ── 銷貨訂單 ──────────────────────────────────────────
class SOItem(BaseModel):
    sku:        str
    name:       str
    qty:        int   = Field(gt=0)
    unit:       str
    unit_price: float = Field(ge=0)
    tax_type:   Optional[TaxType] = None

class SOCreate(BaseModel):
    customer_id:       str
    expected_date:     Optional[str] = None
    delivery_address:  Optional[str] = None
    items:             List[SOItem]
    note:              Optional[str] = None

class SOStatusUpdate(BaseModel):
    status: SOStatus


# ── 出貨 ──────────────────────────────────────────────
class ShipmentItem(BaseModel):
    sku:         str
    shipped_qty: int = Field(gt=0)

class ShipmentCreate(BaseModel):
    so_id:  str
    items:  List[ShipmentItem]
    note:   Optional[str] = None


# ── 銷貨發票 ──────────────────────────────────────────
class SalesInvoiceCreate(BaseModel):
    so_id:        str
    invoice_no:   str
    invoice_date: str
    due_date:     str
    amount:       float = Field(gt=0)
    tax:          float = 0.0

class SalesInvoiceStatusUpdate(BaseModel):
    status: SalesInvoiceStatus
