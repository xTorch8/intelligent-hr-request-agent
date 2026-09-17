from datetime import date, datetime
from typing import Optional


def standardize_employee_number(emp_num: Optional[str]) -> str:
    if not emp_num or not emp_num.strip():
        raise ValueError("employee_number parameter is required.")
    cleaned = emp_num.strip().upper()
    if cleaned.isdigit():
        return f"EMP-{int(cleaned):04d}"
    if cleaned.startswith("EMP"):
        digits = "".join(c for c in cleaned if c.isdigit())
        if digits:
            return f"EMP-{int(digits):04d}"
    return cleaned


def standardize_str(val: Optional[str]) -> Optional[str]:
    if not val or not val.strip():
        return None
    return val.strip().upper().replace(" ", "_").replace("-", "_")


def parse_date(date_input: str) -> date:
    cleaned = date_input.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Could not parse date '{date_input}'. Format must be YYYY-MM-DD.")

