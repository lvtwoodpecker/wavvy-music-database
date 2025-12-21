from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PriceKey:
    plan_id: int
    country_code: Optional[str] = None
    currency_code: str = "USD"
