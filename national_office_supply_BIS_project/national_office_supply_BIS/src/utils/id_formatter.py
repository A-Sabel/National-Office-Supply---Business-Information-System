# src/utils/id_formatter.py

def _abbv(name: str, length: int = 3) -> str:
    """Take first `length` uppercase letters from a name, stripping spaces."""
    letters = [c for c in name.upper() if c.isalpha()]
    return "".join(letters[:length]).ljust(length, "X")

def _pad(raw_id: int, digits: int = 4) -> str:
    return str(int(raw_id)).zfill(digits)

# Position type codes
POSITION_CODE = {
    "Manager":   "01",
    "Sales Rep": "02",
    "Hourly":    "03",
}

def fmt_customer(raw_id: int, company_name: str) -> str:
    """CUST-APX-0015"""
    return f"CUST-{_abbv(company_name)}-{_pad(raw_id)}"

def fmt_invoice(raw_id: int, company_name: str) -> str:
    """INV-APX-1042"""
    return f"INV-{_abbv(company_name)}-{_pad(raw_id)}"

def fmt_employee(raw_id: int, position: str) -> str:
    """EMP-01-003 / EMP-02-007 / EMP-03-012"""
    code = POSITION_CODE.get(position, "00")
    return f"EMP-{code}-{_pad(raw_id, 3)}"

def fmt_supplier(raw_id: int, company_name: str) -> str:
    """SUPP-BIC-004"""
    return f"SUPP-{_abbv(company_name)}-{_pad(raw_id)}"

def fmt_part(raw_id: int) -> str:
    """PN-0021"""
    return f"PN-{_pad(raw_id)}"

def fmt_purchase_order(raw_id: int, supplier_name: str) -> str:
    """PO-BIC-0007"""
    return f"PO-{_abbv(supplier_name)}-{_pad(raw_id)}"

def fmt_timecard(raw_id: int, position: str) -> str:
    """TC-03-0088"""
    code = POSITION_CODE.get(position, "00")
    return f"TC-{code}-{_pad(raw_id)}"

def fmt_customer_payment(raw_id: int, company_name: str) -> str:
    """PAY-APX-0033"""
    return f"PAY-{_abbv(company_name)}-{_pad(raw_id)}"

def fmt_employee_payment(raw_id: int, position: str) -> str:
    """CHK-02-0019"""
    code = POSITION_CODE.get(position, "00")
    return f"CHK-{code}-{_pad(raw_id)}"