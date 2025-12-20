const API = '/api/play-history';

export const playHistoryService = {
  async trackPlay(token, trackId) {
    try {
      const res = await fetch(`${API}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ track_id: trackId }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Failed to track play');
      }
      return await res.json();
    } catch (e) {
      console.error('Error tracking play:', e);
      // Don't throw - we don't want to break the player if tracking fails
    }
  },
};
