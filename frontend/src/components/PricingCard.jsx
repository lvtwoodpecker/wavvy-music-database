// src/components/admin/PricingCard.jsx
import React, { useState } from 'react';

export default function PricingCard({ plan, onUpdatePrice }) {
  const [newPrice, setNewPrice] = useState('');

  const handleUpdate = async () => {
    if (!newPrice) return;
    await onUpdatePrice(plan.plan_id, newPrice);
    setNewPrice('');
  };

  return (
    <div className="pricing-card">
      <h3>{plan.plan_name}</h3>

      <div className="current-price">
        <span>Current Price:</span>
        <strong>${plan.current_price}</strong>
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

      {plan.price_history && plan.price_history.length > 0 && (
        <div className="price-history">
          <h4>Price History</h4>
          <table>
            <thead>
              <tr>
                <th>Price</th>
                <th>Effective From</th>
              </tr>
            </thead>
            <tbody>
              {plan.price_history.map((history, idx) => (
                <tr key={history.price_id ?? idx}>
                  <td>${history.price}</td>
                  <td>
                    {history.effective_from
                      ? new Date(history.effective_from).toLocaleDateString()
                      : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
