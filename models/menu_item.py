from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class MenuItem:
    id: int
    name: str
    category: str
    price: Decimal
    is_available: bool
