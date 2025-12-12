// src/services/stripeService.js
const API_BASE_URL = '/api/stripe';

export const stripeService = {
  async getStripeStatus(token) {
    const response = await fetch(`${API_BASE_URL}/status`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to get Stripe status');
    }

    return data;
  },

  async connectStripeAccount(token) {
    const response = await fetch(`${API_BASE_URL}/connect`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to connect Stripe account');
    }

    return data;
  },
};
