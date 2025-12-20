const API = '/api/playlist';

export const playlistService = {
  async listPlaylists(token) {
    const res = await fetch(`${API}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to list playlists');
    return data;
  },

  async createPlaylist(token, body) {
    const res = await fetch(`${API}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to create playlist');
    return data;
  },

  async getPlaylist(token, id) {
    const res = await fetch(`${API}/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch playlist');
    return data;
  },

  async addTrack(token, id, track) {
    const res = await fetch(`${API}/${id}/tracks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(track),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to add track');
    return data;
  },

  async removeTrack(token, id, trackId) {
    const res = await fetch(`${API}/${id}/tracks/${trackId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || 'Failed to remove track');
    }
    return true;
  },
};
