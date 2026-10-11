from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Bill:
    subtotal: Decimal
    discount: Decimal
    tax_rate: Decimal
    tax: Decimal
    total: Decimal
