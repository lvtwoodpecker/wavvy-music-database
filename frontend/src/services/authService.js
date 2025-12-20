// src/services/authService.js
const API_BASE_URL = '/api/auth';

export const authService = {
  async signup(userData) {
    const response = await fetch(`${API_BASE_URL}/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    let data = null;
    try { data = await response.json(); } catch { /* empty or non-JSON */ }

    if (!response.ok) {
      throw new Error((data && data.error) || `Failed to sign up (HTTP ${response.status})`);
    }

    if (!data) throw new Error('Empty response from server');
    return data;
  },

  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    let data = null;
    try { data = await response.json(); } catch { }

    if (!response.ok) {
      throw new Error((data && data.error) || `Failed to log in (HTTP ${response.status})`);
    }

    if (!data) throw new Error('Empty response from server');
    return data;
  },

  async getCurrentUser(token) {
    const response = await fetch(`${API_BASE_URL}/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    let data = null;
    try { data = await response.json(); } catch { }

    if (!response.ok) {
      throw new Error((data && data.error) || `Failed to fetch user (HTTP ${response.status})`);
    }

    if (!data) throw new Error('Empty response from server');
    return data;
  },

  async requestPasswordReset(email) {
    const response = await fetch(`${API_BASE_URL}/request-password-reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    let data = null;
    try { data = await response.json(); } catch {}
    if (!response.ok) {
      throw new Error((data && data.error) || `Failed to request reset (HTTP ${response.status})`);
    }
    return data || { message: 'Reset initiated' };
  },

  async resetPassword(token, newPassword) {
    const response = await fetch(`${API_BASE_URL}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    let data = null;
    try { data = await response.json(); } catch {}
    if (!response.ok) {
      throw new Error((data && data.error) || `Failed to reset password (HTTP ${response.status})`);
    }
    return data || { message: 'Password has been reset' };
  },

  async changePassword(token, oldPassword, newPassword) {
    const response = await fetch(`${API_BASE_URL}/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });
    let data = null;
    try { data = await response.json(); } catch {}
    if (!response.ok) {
      throw new Error((data && data.error) || `Failed to change password (HTTP ${response.status})`);
    }
    return data || { message: 'Password updated' };
  },
};
