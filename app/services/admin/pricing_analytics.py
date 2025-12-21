from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import math
from collections import defaultdict

from sqlalchemy.orm import selectinload
from sqlalchemy import desc 
from app.models.SubscriptionPlan import SubscriptionPlan

def _to_utc_aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    # If dt is naive, assume it's UTC (common in DBs configured without tz)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    # If dt is aware, convert to UTC
    return dt.astimezone(timezone.utc)

def _safe_float(x) -> Optional[float]:
    try:
        return float(x) if x is not None else None
    except Exception:
        return None


def _days_between(a: Optional[datetime], b: Optional[datetime]) -> Optional[int]:
    if not a or not b:
        return None
    a = _to_utc_aware(a)
    b = _to_utc_aware(b)
    return abs((a - b).days)


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def _std(values: List[float]) -> Optional[float]:
    # population std; swap to sample std if you want (n-1)
    if not values:
        return None
    m = _mean(values)
    if m is None:
        return None
    var = sum((v - m) ** 2 for v in values) / len(values)
    return math.sqrt(var)


def _month_key(dt: datetime) -> str:
    # "YYYY-MM"
    return f"{dt.year:04d}-{dt.month:02d}"


class PricingAnalyticsService:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    def get_pricing_trends(self) -> Dict[str, Any]:
        """
        Returns:
          - plans: per-plan time series + derived metrics (for charts)
          - rollups: portfolio-level signals (overall trend summary)
        """
        db = self.db_session_factory()
        try:
            plans = (
                db.query(SubscriptionPlan)
                .filter(SubscriptionPlan.is_active == True)
                .options(selectinload(SubscriptionPlan.prices))
                .all()
            )

            now = datetime.now(timezone.utc)

            plan_results: List[Dict[str, Any]] = []
            all_current_prices: List[float] = []
            total_changes = 0

            for plan in plans:
                history_rows = list(plan.prices or [])

                # Sort history by effective_from ASC for charting
                history_rows = sorted(
                    history_rows,
                    key=lambda h: (h.effective_from or datetime.min)
                )

                series = []
                for h in history_rows:
                    if not h.effective_from:
                        continue
                    price = _safe_float(h.price)
                    if price is None:
                        continue
                    series.append({
                        "date": h.effective_from.date().isoformat(),
                        "price": price,
                    })

                # Determine current = last effective_from
                current_price = series[-1]["price"] if series else None
                first_price = series[0]["price"] if series else None

                if current_price is not None:
                    all_current_prices.append(current_price)

                num_changes = max(0, len(series) - 1)
                total_changes += num_changes

                abs_change = (current_price - first_price) if (
                    current_price is not None and first_price is not None
                ) else None

                pct_change = None
                if abs_change is not None and first_price not in (None, 0):
                    pct_change = abs_change / first_price

                last_change_days_ago = None
                if history_rows and history_rows[-1].effective_from:
                    last_change_days_ago = _days_between(now, history_rows[-1].effective_from)

                prices_only = [p["price"] for p in series]
                avg_price = _mean(prices_only)
                std_price = _std(prices_only)
                min_price = min(prices_only) if prices_only else None
                max_price = max(prices_only) if prices_only else None

                # Monthly snapshot series (last price seen in each month)
                monthly_map: Dict[str, float] = {}
                for p in series:
                    dt = datetime.fromisoformat(p["date"])
                    key = _month_key(dt)
                    monthly_map[key] = p["price"]  # overwrite → last seen in month

                monthly_series = [
                    {"month": m, "price": monthly_map[m]}
                    for m in sorted(monthly_map.keys())
                ]

                # Normalized index series (100 at first price)
                index_series = []
                if first_price not in (None, 0):
                    for p in series:
                        index_series.append({
                            "date": p["date"],
                            "index": (p["price"] / first_price) * 100.0
                        })

                plan_results.append({
                    "plan_id": plan.plan_id,
                    "plan_name": getattr(plan, "name", None),

                    # current state
                    "current_price": current_price,
                    "first_price": first_price,

                    # analytics
                    "num_changes": num_changes,
                    "abs_change": abs_change,
                    "pct_change": pct_change,  # e.g., 0.15 = +15%
                    "days_since_last_change": last_change_days_ago,
                    "avg_price": avg_price,
                    "std_price": std_price,
                    "min_price": min_price,
                    "max_price": max_price,

                    # chart-friendly time series
                    "series": series,                   # line chart / step chart
                    "monthly_series": monthly_series,   # line chart by month
                    "price_index_series": index_series, # compare plans on same scale
                })

            # Rollups across plans (portfolio view)
            rollups = {
                "active_plans": len(plan_results),
                "total_price_changes": total_changes,
                "avg_current_price": _mean(all_current_prices),
                "std_current_price": _std(all_current_prices),
                "min_current_price": min(all_current_prices) if all_current_prices else None,
                "max_current_price": max(all_current_prices) if all_current_prices else None,
                "as_of": now.isoformat(),
            }

            return {"plans": plan_results, "rollups": rollups}

        finally:
            db.close()
