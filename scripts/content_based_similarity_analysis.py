"""User similarity analysis using song attributes."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.services.content_based_similarity_service import ContentBasedSimilarityService

def main():
    username1 = "cedricster"
    username2 = "paola_calle"
    
    print(f"\nUser Similarity Analysis: {username1} vs {username2}\n")
    
    service = ContentBasedSimilarityService()
    
    similarity_result = service.calculate_content_based_similarity(username1, username2)
    
    if "error" in similarity_result:
        print(f"ERROR: {similarity_result['error']}")
        return
    
    scores = similarity_result['similarity_scores']
    stats = similarity_result['statistics']
    
    print(f"Similarity Scores:")
    print(f"  Cosine: {scores['cosine_similarity']*100:.1f}%")
    print(f"  Euclidean: {scores['euclidean_similarity']*100:.1f}%")
    print(f"  Genre Jaccard: {scores['genre_jaccard']*100:.1f}%")
    print(f"  Overall: {scores['overall']*100:.1f}%")
    print(f"\nStatistics:")
    print(f"  {username1}: {stats['user1_tracks']} tracks, {stats['user1_genres']} genres")
    print(f"  {username2}: {stats['user2_tracks']} tracks, {stats['user2_genres']} genres")
    print(f"  Shared genres: {stats['shared_genres']}\n")
    
    recommendations_result = service.get_recommendations_for_both_users(
        username1, username2, n_recommendations=20, max_artist_repeats=3
    )
    
    if "error" not in recommendations_result:
        recommendations = recommendations_result.get('recommendations', [])
        diversity_stats = recommendations_result.get('diversity_stats', {})
        
        print(f"Top {len(recommendations)} Recommendations:\n")
        
        for i, rec in enumerate(recommendations, 1):
            artists_str = ", ".join(rec.get('artists', [])) or "Unknown"
            genres_str = ", ".join(rec.get('genres', [])[:3]) or "No genres"
            
            print(f"{i:2d}. {rec['title']}")
            print(f"     {artists_str} | {genres_str} | Similarity: {rec['similarity']:.3f}")
        
        if diversity_stats:
            print(f"\nUnique artists: {diversity_stats.get('unique_artists', 0)}")
    else:
        print(f"ERROR: {recommendations_result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
