# Temporary Scripts

This folder contains temporary scripts for bulk data operations.

## bulk_artist_ingest.py

Bulk artist ingestion script that:
- Downloads the MTV Music Artists CSV from GitHub
- Randomly selects ~150 artists from the list
- For each artist:
  - Searches Spotify for the artist
  - Selects ONE random album from the artist's discography
  - Ingests the album, tracks, genres, labels, and album cover
  - Uses CSV genre as fallback if Spotify doesn't have genre data

### Usage

```bash
python temp_script/bulk_artist_ingest.py
```

### Features

- Randomly selects artists to avoid bias
- Randomly selects one album per artist
- Automatically fetches and stores album covers
- Uses CSV genre data as fallback
- Skips artists that already exist in database
- Limits to 10 tracks per album to keep ingestion manageable

### CSV Source

The script uses the MTV Music Artists CSV from:
https://gist.githubusercontent.com/mbejda/9912f7a366c62c1f296c/raw/dd94a25492b3062f4ca0dc2bb2cdf23fec0896ea/10000-MTV-Music-Artists-page-1.csv

