from save_mrmaid import mm_to_img

flowchart_code = """
flowchart TB

subgraph CLIENT[Client]
    U["User Search Query"] --> Q["GET /api/search?q=..."]
end

subgraph API[Flask API Layer]
    Q --> ROUTE["Search Route"]
    ROUTE --> SERVICE["SearchService<br/>(FTS vs Trigram decision)"]
end

subgraph ORM[ORM + Query Layer]
    SERVICE --> REPO["SearchRepository<br/>(SQLAlchemy ORM queries)"]
    REPO --> MODEL["ODSTrackSearch ORM Model<br/>maps to ods_track_search"]
end

subgraph DB[Supabase Postgres]
    MODEL --> ODS["ods_track_search"]
    ODS --> IDX1["GIN index on search_tsv"]
    ODS --> IDX2["GIN trigram on normalized fields"]

    subgraph OLTP[OLTP Normalized Tables]
        TR[Track] --- TA[TrackArtist] --- AR[Artist]
        TR --- AT[AlbumTrack] --- AL[Album]
        TR --- TG[TrackGenre] --- GN[Genre]
    end

    OLTP --> REFRESH["ODS Refresh UPSERT<br/>aggregate and precompute fields"]
    REFRESH --> ODS
end

ODS --> OUT["Ranked Results JSON"]
OUT --> U
"""

mm_to_img(flowchart_code, filename="images/otm_ods_orm.svg") 
