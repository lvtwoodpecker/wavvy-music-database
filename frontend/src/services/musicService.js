// Library service hitting the backend
const API = '/api/library/tracks';

const normalizeTrack = (t) => ({
  id: t.id || t.track_id || t.uuid || t.slug,
  title: t.title || t.name || 'Untitled',
  artist: t.artist || t.artists || t.artist_name || 'Unknown artist',
  album: t.album || t.album_name || t.album_title || 'Unknown album',
  track_number: t.track_number || t.trackNo || t.track_no,
  // Backend schema exposes audio_file_url; keep audio_url fallback for demo/other sources
  audio_url: t.audio_url || t.audio_file_url || t.preview_url || t.stream_url,
  cover_url: t.cover_url || t.cover_image_url || t.album_cover_url,
  duration_ms: t.duration_ms || t.duration,
});

const groupByAlbum = (tracks) => {
  const byAlbum = new Map();
  tracks.forEach((t) => {
    const key = t.album || 'Unknown album';
    if (!byAlbum.has(key)) byAlbum.set(key, []);
    byAlbum.get(key).push(t);
  });
  return Array.from(byAlbum.entries()).map(([album, songs]) => {
    const sorted = [...songs].sort((a, b) => {
      const ta = a.track_number ?? 0;
      const tb = b.track_number ?? 0;
      return ta - tb;
    });
    const cover = sorted.find((s) => s.cover_url)?.cover_url || sorted[0]?.cover_url;
    const artist = sorted[0]?.artist || 'Unknown artist';
    return { album, artist, cover_url: cover, tracks: sorted };
  });
};

export const musicService = {
  async getLibrary(token) {
    try {
      const res = await fetch(API, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('failed');
      const data = await res.json();
      const normalized = (Array.isArray(data) ? data : []).map(normalizeTrack)
        .filter((t) => !!t.audio_url);
      console.log('Loaded tracks:', { total: (Array.isArray(data) ? data : []).length, withAudio: normalized.length });
      return groupByAlbum(normalized);
    } catch (e) {
      console.warn('Failed to load library:', e.message);
      return [];
    }
  },
};

