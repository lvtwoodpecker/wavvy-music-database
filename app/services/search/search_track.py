# app/services/search/search_service.py
from __future__ import annotations

from typing import Dict, List
from app.services.search.search_types import TrackSearchHit
from app.services.search.search_repository import SearchRepository


class SearchTrack:
    def __init__(self, repo: SearchRepository):
        self.repo = repo

    def search_tracks(self, query: str, limit: int = 25) -> Dict:
        q = (query or "").strip()
        if not q:
            return {"query": q, "results": [], "used": {"fts": False, "trigram": False}}

        prefer_trigram = len(q) <= 3

        fts: List[TrackSearchHit] = []
        tri: List[TrackSearchHit] = []
        used_fts = False
        used_tri = False

        if not prefer_trigram:
            fts = self.repo.fts_search(q, limit=limit)
            used_fts = True

        if prefer_trigram or len(fts) < 8:
            tri = self.repo.trigram_search(q, limit=limit)
            used_tri = True

        merged = self._merge_best(fts, tri, limit=limit)
        return {
            "query": q,
            "used": {"fts": used_fts, "trigram": used_tri},
            "results": [hit.__dict__ for hit in merged],
        }

    @staticmethod
    def _merge_best(a: List[TrackSearchHit], b: List[TrackSearchHit], limit: int) -> List[TrackSearchHit]:
        best: Dict[int, TrackSearchHit] = {}

        for hit in a + b:
            cur = best.get(hit.track_id)
            if cur is None or hit.score > cur.score:
                best[hit.track_id] = hit

        return sorted(best.values(), key=lambda x: x.score, reverse=True)[:limit]
