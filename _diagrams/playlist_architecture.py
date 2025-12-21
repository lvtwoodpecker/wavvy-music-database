from save_mrmaid import mm_to_img

flowchart_code = """
flowchart TB
    U[User] --> FE[Frontend React Playlist Component]
    
    FE --> LIST[GET /api/playlist]
    FE --> CREATE[POST /api/playlist]
    FE --> GET[GET /api/playlist/:id]
    FE --> DEL[DELETE /api/playlist/:id]
    FE --> ADD[POST /api/playlist/:id/tracks]
    FE --> REM[DELETE /api/playlist/:id/tracks/:tid]
    
    LIST --> AUTH[JWT Auth @login_required]
    CREATE --> AUTH
    GET --> AUTH
    DEL --> AUTH
    ADD --> AUTH
    REM --> AUTH
    
    AUTH --> PS[PlaylistService]
    
    PS --> PLM[Playlist Model]
    PS --> PTM[PlaylistTrack Model]
    
    PLM --> PLTBL[Playlist table]
    PTM --> PTTBL[PlaylistTrack table]
    
    PLTBL -.contains.-> PTTBL
    PTTBL -.references.-> TRTBL[Track table]
"""

mm_to_img(flowchart_code, filename="images/playlist_architecture.png", fmt="png")
print("✓ Playlist architecture diagram generated!")
