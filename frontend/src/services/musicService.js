// Library service hitting the backend; falls back to demo tracks on failure.
const API = '/api/library/tracks';

const demoTracks = [
  {
    id: 'demo-1',
    title: 'Chill Ambient',
    artist: 'Wavvy',
    album: 'Demo Collection',
    track_number: 1,
    audio_url: 'https://cdn.pixabay.com/download/audio/2022/03/15/audio_e32846d7d8.mp3?filename=chill-ambient-110387.mp3',
    cover_url: 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=320&auto=format&fit=crop',
    duration_ms: 120000,
  },
  {
    id: 'demo-2',
    title: 'Lofi Breeze',
    artist: 'Wavvy',
    album: 'Demo Collection',
    track_number: 2,
    audio_url: 'https://cdn.pixabay.com/download/audio/2022/03/19/audio_e2d1dd9d29.mp3?filename=lofi-study-112191.mp3',
    cover_url: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=320&auto=format&fit=crop',
    duration_ms: 180000,
  },
];

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
      if (normalized.length === 0) return groupByAlbum(demoTracks);
      return groupByAlbum(normalized);
    } catch (e) {
      console.warn('Falling back to demo tracks:', e.message);
      return groupByAlbum(demoTracks);
    }
  },
};

