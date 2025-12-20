const API_BASE_URL = '/api/stripe/subscription';

export const subscriptionService = {
  async getStatus(token) {
    const res = await fetch(`${API_BASE_URL}/status`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch subscription status');
    return data.subscription;
  },

  async activate(token, payload = {}) {
    const res = await fetch(`${API_BASE_URL}/activate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to activate subscription');
    return data.subscription;
  },

  async cancel(token) {
    const res = await fetch(`${API_BASE_URL}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to cancel subscription');
    return data.subscription;
  },
};
