// Search service for track/song searching using the backend search API
const SEARCH_API = '/api/search';

/**
 * Search for tracks using the specialized FTS + trigram query
 * @param {string} query - Search query string
 * @param {string} token - Authentication token
 * @param {number} limit - Maximum number of results (default: 25)
 * @returns {Promise<Object>} Search results with tracks
 */
const searchTracks = async (query, token, limit = 25) => {
  if (!query || query.trim().length === 0) {
    return { results: [], query: '' };
  }

  try {
    const url = `${SEARCH_API}?q=${encodeURIComponent(query)}&limit=${limit}`;
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (!res.ok) {
      throw new Error(`Search failed with status ${res.status}`);
    }

    const data = await res.json();
    return data;
  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
};

export const searchService = {
  searchTracks,
};
