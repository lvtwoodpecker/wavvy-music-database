const API = '/api/recommend';

export const recommenderService = {
  async recommendForPlaylist(token, playlistId, limit = 10) {
    const res = await fetch(`${API}/playlist/${playlistId}?limit=${limit}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch recommendations');
    return data.recommendations || [];
  },

  async recommendForUser(token, limit = 10) {
    const res = await fetch(`${API}/user?limit=${limit}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch recommendations');
    return data.recommendations || [];
  },
};
