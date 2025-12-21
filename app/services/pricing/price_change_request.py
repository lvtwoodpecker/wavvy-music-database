from typing import Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class PriceChangeRequest:
    plan_id: int
    new_price: float
    country_code: Optional[str] = None
    currency_code: str = "USD"
    change_reason: Optional[str] = None