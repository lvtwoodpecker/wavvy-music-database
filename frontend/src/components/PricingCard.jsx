// src/components/admin/PricingCard.jsx
import React, { useMemo, useState } from "react";

function Sparkline({ points, height = 36, width = 160 }) {
  // points: [{ xLabel, y }]
  const path = useMemo(() => {
    if (!points || points.length < 2) return null;

    const ys = points.map(p => p.y);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    const scaleY = (y) => {
      if (maxY === minY) return height / 2;
      // invert y for SVG
      return height - ((y - minY) / (maxY - minY)) * height;
    };

    const stepX = width / (points.length - 1);

    return points
      .map((p, i) => {
        const x = i * stepX;
        const y = scaleY(p.y);
        return `${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
      })
      .join(" ");
  }, [points, height, width]);

  if (!path) return <div style={{ height }} className="sparkline-empty">No trend yet</div>;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-label="Price trend">
      <path d={path} fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

export default function PricingCard({ plan, onUpdatePrice }) {
  const [newPrice, setNewPrice] = useState("");

  const handleUpdate = async () => {
    if (!newPrice) return;
    await onUpdatePrice(plan.plan_id, newPrice);
    setNewPrice("");
  };

  const pct = typeof plan.pct_change === "number" ? plan.pct_change * 100 : null;

  // Prefer monthly_series for clean charts; fallback to series
  const trendPoints = useMemo(() => {
    const s = plan.monthly_series?.length ? plan.monthly_series : plan.series;
    if (!s || s.length === 0) return [];

    // monthly_series: [{ month, price }]
    if (s[0]?.month) {
      return s.map(p => ({ xLabel: p.month, y: p.price }));
    }

    // series: [{ date, price }]
    return s.map(p => ({ xLabel: p.date, y: p.price }));
  }, [plan.monthly_series, plan.series]);

  return (
    <div className="pricing-card">
      <div className="pricing-card-header">
        <div>
          <h3>{plan.plan_name}</h3>
          <div className="current-price">
            <span>Current Price:</span>{" "}
            <strong>
              {plan.current_price != null ? `$${Number(plan.current_price).toFixed(2)}` : "N/A"}
            </strong>
          </div>
        </div>

        <div className="pricing-sparkline">
          <Sparkline points={trendPoints} />
        </div>
      </div>

      {/* Analytics chips */}
      <div className="pricing-metrics">
        <div className="chip">
          <span>Changes</span>
          <strong>{plan.num_changes ?? 0}</strong>
        </div>

        <div className="chip">
          <span>Total %</span>
          <strong>{pct == null ? "N/A" : `${pct.toFixed(1)}%`}</strong>
        </div>

        <div className="chip">
          <span>Volatility</span>
          <strong>
            {plan.std_price == null ? "N/A" : Number(plan.std_price).toFixed(2)}
          </strong>
        </div>

        <div className="chip">
          <span>Last change</span>
          <strong>
            {plan.days_since_last_change == null
              ? "N/A"
              : `${plan.days_since_last_change}d ago`}
          </strong>
        </div>
      </div>

      <div className="price-update-form">
        <input
          type="number"
          step="0.01"
          placeholder="New price"
          value={newPrice}
          onChange={(e) => setNewPrice(e.target.value)}
        />
        <button onClick={handleUpdate}>Update Price</button>
      </div>

      {/* Table: use monthly_series/series instead of old price_history */}
      {trendPoints.length > 0 && (
        <div className="price-history">
          <h4>Price History</h4>
          <table>
            <thead>
              <tr>
                <th>Period</th>
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              {trendPoints
                .slice()
                .reverse()
                .map((p, idx) => (
                  <tr key={`${p.xLabel}-${idx}`}>
                    <td>{p.xLabel}</td>
                    <td>${Number(p.y).toFixed(2)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
