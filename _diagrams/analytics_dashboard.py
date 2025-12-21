from save_mrmaid import mm_to_img

mermaid_code = """
flowchart TD
    Admin[Admin User] --> Dashboard[Analytics Dashboard]
    Dashboard --> GetAnalytics[GET /api/admin/music-analytics]
    
    GetAnalytics --> Auth[JWT Admin Auth]
    Auth --> AnalyticsService[AdminService.get_music_analytics]
    
    AnalyticsService --> TotalTracks[Query Total Tracks]
    TotalTracks --> TrackTable[(Track Table)]
    
    AnalyticsService --> TopPlayed[Query Top 10 Played Tracks]
    TopPlayed --> JoinTables[JOIN Track + PlayHistory]
    JoinTables --> PlayHistoryTable[(PlayHistory Table)]
    JoinTables --> TrackTable2[(Track Table)]
    
    AnalyticsService --> PlaysByDate[Query Plays by Date Last 30 Days]
    PlaysByDate --> PlayHistoryTable2[(PlayHistory Table)]
    
    JoinTables --> GroupByTrack[GROUP BY track_id, title]
    GroupByTrack --> OrderByCount[ORDER BY play_count DESC]
    OrderByCount --> Limit10[LIMIT 10]
    
    PlaysByDate --> FilterLast30[WHERE played_at >= 30 days ago]
    FilterLast30 --> GroupByDate[GROUP BY date played_at]
    GroupByDate --> OrderByDate[ORDER BY date]
    
    TotalTracks --> Response[Analytics Response]
    Limit10 --> Response
    OrderByDate --> Response
    
    Response --> DashboardUI[Dashboard UI]
    DashboardUI --> TotalTracksCard[Total Tracks Card]
    DashboardUI --> TopTracksChart[Top Tracks Bar Chart]
    DashboardUI --> PlaysTimelineChart[Plays Timeline Line Chart]
    
    style TrackTable fill:#e1f5ff
    style PlayHistoryTable fill:#e1f5ff
    style TrackTable2 fill:#e1f5ff
    style PlayHistoryTable2 fill:#e1f5ff
    style Response fill:#d4edda
"""

# Generate the diagram
mm_to_img(mermaid_code, "images/analytics_dashboard.png")
print("✓ Music Analytics Dashboard diagram generated!")
