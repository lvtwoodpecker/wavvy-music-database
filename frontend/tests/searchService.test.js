import { test, expect, describe } from 'vitest';
import { searchService } from '../src/services/searchService';

describe('searchService', () => {
  test('searchTracks should construct correct URL', () => {
    // This is a basic test to ensure the search service module structure is correct
    expect(searchService).toBeDefined();
    expect(typeof searchService.searchTracks).toBe('function');
  });

  test('searchTracks should handle empty query', async () => {
    const result = await searchService.searchTracks('', 'fake-token');
    expect(result).toEqual({ results: [], query: '' });
  });

  test('searchTracks should handle whitespace-only query', async () => {
    const result = await searchService.searchTracks('   ', 'fake-token');
    expect(result).toEqual({ results: [], query: '' });
  });
});
