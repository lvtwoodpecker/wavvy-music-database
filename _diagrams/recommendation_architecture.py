from save_mrmaid import mm_to_img

flowchart_code = """
flowchart TB
    U[User] --> FE{Frontend}
    
    FE -->|GET /api/recommend/playlist/:id| REC_PL[Recommend for Playlist]
    FE -->|GET /api/recommend/user| REC_USR[Recommend for User]
    
    REC_PL --> AUTH[JWT Auth @login_required]
    REC_USR --> AUTH
    
    AUTH --> CBS[ContentBasedRecommenderService]
    
    CBS --> |recommend_for_playlist| PLREC[Get playlist tracks]
    CBS --> |recommend_for_user| USREC[Get user play history]
    
    PLREC --> FEAT[Extract Features]
    USREC --> FEAT
    
    FEAT --> TRAIN[Train/Load KNN Model]
    
    TRAIN --> SHOULD[Check should_retrain]
    SHOULD -->|No cache needed| LOAD[Load cached model<br/>from ModelCache]
    SHOULD -->|Needs retraining| BUILD[Build feature matrix<br/>from AudioFeatures]
    
    LOAD --> KNN[KNN Model<br/>fit_neighbors:<br/>metric=cosine<br/>n=10]
    BUILD --> KNN
    
    BUILD --> SAVE[Save model to ModelCache<br/>pickle + base64]
    
    KNN --> QUERY[Query nearest neighbors]
    QUERY --> RANK[Rank recommendations<br/>by similarity]
    RANK --> RES[Return JSON results]
    
    RES --> FE
    FE --> U
    
    subgraph DATA[Data Sources]
        AF["AudioFeatures<br/>tempo, loudness<br/>danceability, energy<br/>valence, acousticness"]
        TG["TrackGenre<br/>genre_id mappings"]
        GN["Genre<br/>name list"]
        PL["Playlist<br/>tracks"]
        PH["PlayHistory<br/>user listens"]
        TR["Track<br/>metadata"]
    end
    
    FEAT --> AF
    FEAT --> TG
    FEAT --> GN
    PLREC --> PL
    USREC --> PH
    PLREC --> TR
    
    subgraph CACHE["Caching Layer"]
        MC["ModelCache<br/>stores:<br/>KNN pickled model<br/>feature matrices<br/>track_ids<br/>genre_encoding<br/>metadata"]
    end
    
    TRAIN --> MC
    MC --> LOAD
    SAVE --> MC
"""

mm_to_img(flowchart_code, filename="images/recommendation_architecture.png", fmt="png")
print("✓ Recommendation architecture diagram generated!")
