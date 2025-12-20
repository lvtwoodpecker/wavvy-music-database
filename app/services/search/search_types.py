# app/services/search/search_types.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TrackSearchHit:
    track_id: int
    track_title: str
    artist_names: str
    album_titles: str
    genre_names: str
    score: float
    source: str