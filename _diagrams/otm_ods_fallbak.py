from save_mrmaid import mm_to_img

flowchart_code = """
flowchart TB
  U["User"] --> FE["Frontend Search Bar"]
  FE --> Q["GET /api/search?q=..."]

  Q --> ROUTE["Search Route (Flask)"]
  ROUTE --> SERVICE["SearchService<br/>(strategy: FTS primary, trigram fallback)"]
  SERVICE --> REPO["SearchRepository<br/>(ORM / SQLAlchemy)"]
  REPO --> ODS["ODS Table: ods_track_search<br/>(indexed: search_tsv + normalized trigram columns)"]

  %% FTS vs trigram decision path
  SERVICE -->|FTS hit| ODS
  SERVICE -->|FTS weak / empty| TRIG["Trigram fallback query"]
  TRIG --> ODS

  %% OLTP -> ODS refresh
  subgraph OLTP["OLTP Tables"]
    direction LR
    TR[Track] --- AR[Artist] --- AL[Album] --- GN[Genre] --- JT["Join tables"]
  end

  OLTP --> REFRESH["ODS Refresh Job (UPSERT)<br/>aggregates + precomputes search fields"]
  REFRESH --> ODS

  ODS --> OUT["Ranked Search Results (JSON)"]
  OUT --> U
"""

mm_to_img(flowchart_code, filename="images/otm_ods_fallback.png", fmt="png")
