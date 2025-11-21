import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
import musicbrainzngs

# ---
# 1. SETUP
# ---
load_dotenv()
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
if not supabase_url or not supabase_key:
    raise Exception("Supabase URL or Service Key is missing in .env file")
supabase: Client = create_client(supabase_url, supabase_key)

# Configure MusicBrainz
# Set your application name and version (required by MusicBrainz)
musicbrainzngs.set_useragent("Wavvy-ISWC-Ingest", "1.0", "https://github.com/yourusername/wavvy")
# Set rate limiting (1 request per second to be respectful)
musicbrainzngs.set_rate_limit(limit_or_interval=1.0)

# ---
# 2. MUSICBRAINZ HELPER FUNCTIONS
# ---
def search_iswc_by_isrc(isrc):
    """
    Search for ISWC data using ISRC code.
    Returns ISWC code if found, None otherwise.
    """
    try:
        # Search for recordings by ISRC
        result = musicbrainzngs.search_recordings(isrc=isrc, limit=1)
        
        if result and 'recording-list' in result and len(result['recording-list']) > 0:
            recording = result['recording-list'][0]
            recording_id = recording['id']
            
            # Get full recording details including works
            recording_details = musicbrainzngs.get_recording_by_id(recording_id, includes=['work-rels'])
            
            # Look for ISWC in work relationships
            if 'recording' in recording_details:
                recording_data = recording_details['recording']
                if 'work-relation-list' in recording_data:
                    for work_rel in recording_data['work-relation-list']:
                        if 'work' in work_rel:
                            work = work_rel['work']
                            if 'iswc' in work and work['iswc']:
                                return work['iswc']
                            
                            # If no ISWC in relation, try to get work details
                            if 'id' in work:
                                work_id = work['id']
                                try:
                                    work_details = musicbrainzngs.get_work_by_id(work_id)
                                    if 'work' in work_details and 'iswc-list' in work_details['work']:
                                        iswc_list = work_details['work']['iswc-list']
                                        if iswc_list and len(iswc_list) > 0:
                                            return iswc_list[0]
                                except:
                                    pass
        
        return None
    except Exception as e:
        print(f"    > Error searching by ISRC {isrc}: {e}")
        return None

def search_iswc_by_title_artist(title, artist_name):
    """
    Search for ISWC data using track title and artist name.
    Returns ISWC code if found, None otherwise.
    """
    try:
        # Search for works by title and artist
        result = musicbrainzngs.search_works(work=title, artist=artist_name, limit=5)
        
        if result and 'work-list' in result:
            for work in result['work-list']:
                # Check if ISWC exists
                if 'iswc-list' in work and work['iswc-list']:
                    return work['iswc-list'][0]
        
        # Alternative: search recordings and then get works
        result = musicbrainzngs.search_recordings(recording=title, artist=artist_name, limit=3)
        
        if result and 'recording-list' in result:
            for recording in result['recording-list'][:3]:  # Check top 3 matches
                recording_id = recording['id']
                try:
                    recording_details = musicbrainzngs.get_recording_by_id(
                        recording_id, 
                        includes=['work-rels']
                    )
                    
                    if 'recording' in recording_details:
                        recording_data = recording_details['recording']
                        if 'work-relation-list' in recording_data:
                            for work_rel in recording_data['work-relation-list']:
                                if 'work' in work_rel:
                                    work = work_rel['work']
                                    if 'iswc-list' in work and work['iswc-list']:
                                        return work['iswc-list'][0]
                                    
                                    # Try to get full work details
                                    if 'id' in work:
                                        work_id = work['id']
                                        try:
                                            work_details = musicbrainzngs.get_work_by_id(work_id)
                                            if 'work' in work_details and 'iswc-list' in work_details['work']:
                                                iswc_list = work_details['work']['iswc-list']
                                                if iswc_list and len(iswc_list) > 0:
                                                    return iswc_list[0]
                                        except:
                                            pass
                except:
                    continue
        
        return None
    except Exception as e:
        print(f"    > Error searching by title/artist ({title}, {artist_name}): {e}")
        return None

# ---
# 3. MAIN ISWC INGESTION FUNCTION
# ---
def update_works_with_iswc(limit=None, track_id=None):
    """
    Updates Work records in the database with ISWC codes from MusicBrainz.
    
    Args:
        limit: Maximum number of tracks to process (None for all)
        track_id: Specific track_id to update (None for all tracks)
    """
    try:
        print("Starting ISWC data ingestion from MusicBrainz...")
        
        # Query tracks that have ISRC but their works don't have ISWC
        query = supabase.from_("Track").select("track_id, title, isrc")
        
        if track_id:
            query = query.eq("track_id", track_id)
        
        tracks_response = query.execute()
        
        if not tracks_response.data:
            print("No tracks found to process.")
            return
        
        tracks = tracks_response.data
        if limit:
            tracks = tracks[:limit]
        
        print(f"Found {len(tracks)} tracks to process.")
        
        updated_count = 0
        not_found_count = 0
        error_count = 0
        
        for idx, track in enumerate(tracks, 1):
            print(f"\n[{idx}/{len(tracks)}] Processing: {track['title']}")
            
            # Get the work associated with this track
            trackwork_response = supabase.from_("TrackWork").select(
                "work_id"
            ).eq("track_id", track['track_id']).limit(1).execute()
            
            if not trackwork_response.data or len(trackwork_response.data) == 0:
                print(f"  > No work found for track, skipping...")
                continue
            
            work_id = trackwork_response.data[0]['work_id']
            
            # Get work details
            work_response = supabase.from_("Work").select("*").eq("work_id", work_id).limit(1).execute()
            
            if not work_response.data:
                print(f"  > Work not found, skipping...")
                continue
            
            work_info = work_response.data[0]
            
            # Skip if ISWC already exists
            if work_info.get('iswc'):
                print(f"  > Work already has ISWC: {work_info['iswc']}")
                continue
            
            iswc = None
            
            # Try to find ISWC by ISRC first (most reliable)
            if track.get('isrc'):
                print(f"  > Searching by ISRC: {track['isrc']}")
                iswc = search_iswc_by_isrc(track['isrc'])
                time.sleep(1)  # Rate limiting
            
            # If not found by ISRC, try by title and artist
            if not iswc:
                print(f"  > Searching by title and artist...")
                # Get artist name from TrackArtist
                trackartist_response = supabase.from_("TrackArtist").select(
                    "artist_id"
                ).eq("track_id", track['track_id']).limit(1).execute()
                
                if trackartist_response.data:
                    artist_id = trackartist_response.data[0]['artist_id']
                    artist_response = supabase.from_("Artist").select("name").eq("artist_id", artist_id).limit(1).execute()
                    
                    if artist_response.data:
                        artist_name = artist_response.data[0].get('name')
                        if artist_name:
                            iswc = search_iswc_by_title_artist(track['title'], artist_name)
                            time.sleep(1)  # Rate limiting
            
            # Update work with ISWC if found
            if iswc:
                print(f"  > Found ISWC: {iswc}")
                update_response = supabase.from_("Work").update({
                    "iswc": iswc
                }).eq("work_id", work_id).execute()
                
                if update_response.data:
                    updated_count += 1
                    print(f"  > ✓ Successfully updated work with ISWC")
                else:
                    error_count += 1
                    print(f"  > ✗ Failed to update work")
            else:
                not_found_count += 1
                print(f"  > ✗ ISWC not found in MusicBrainz")
        
        print(f"\n{'='*50}")
        print(f"ISWC Ingestion Summary:")
        print(f"  Updated: {updated_count}")
        print(f"  Not Found: {not_found_count}")
        print(f"  Errors: {error_count}")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"An error occurred during ISWC ingestion: {e}")
        import traceback
        traceback.print_exc()

# ---
# 4. BATCH UPDATE FUNCTION (for ISWC Open Data)
# ---
def update_from_iswc_file(file_path):
    """
    Updates works from ISWC Open Data file.
    Note: You need to download the ISWC Open Data from https://www.iswc.org/open-data
    and agree to their terms and conditions.
    
    Args:
        file_path: Path to the ISWC data file (CSV format)
    """
    import csv
    
    try:
        print(f"Loading ISWC data from file: {file_path}")
        
        updated_count = 0
        not_found_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                iswc = row.get('ISWC', '').strip()
                title = row.get('Title', '').strip()
                
                if not iswc or not title:
                    continue
                
                # Find work by title
                work_response = supabase.from_("Work").select("*").eq("title", title).execute()
                
                if work_response.data:
                    for work in work_response.data:
                        if not work.get('iswc'):  # Only update if ISWC is missing
                            supabase.from_("Work").update({
                                "iswc": iswc
                            }).eq("work_id", work['work_id']).execute()
                            updated_count += 1
                            print(f"  > Updated: {title} -> {iswc}")
                else:
                    not_found_count += 1
        
        print(f"\n{'='*50}")
        print(f"ISWC File Update Summary:")
        print(f"  Updated: {updated_count}")
        print(f"  Not Found: {not_found_count}")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"An error occurred while processing ISWC file: {e}")
        import traceback
        traceback.print_exc()

# ---
# 5. RUN THE SCRIPT
# ---
if __name__ == "__main__":
    import sys
    
    print("ISWC Data Ingestion Script")
    print("=" * 50)
    print("\nOptions:")
    print("1. Update all tracks (MusicBrainz API)")
    print("2. Update specific number of tracks")
    print("3. Update specific track by ID")
    print("4. Update from ISWC Open Data file")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        update_works_with_iswc()
    elif choice == "2":
        limit = input("Enter number of tracks to process: ").strip()
        try:
            limit = int(limit)
            update_works_with_iswc(limit=limit)
        except ValueError:
            print("Invalid number")
    elif choice == "3":
        track_id = input("Enter track_id: ").strip()
        try:
            track_id = int(track_id)
            update_works_with_iswc(track_id=track_id)
        except ValueError:
            print("Invalid track_id")
    elif choice == "4":
        file_path = input("Enter path to ISWC data file: ").strip()
        update_from_iswc_file(file_path)
    else:
        print("Invalid choice")

