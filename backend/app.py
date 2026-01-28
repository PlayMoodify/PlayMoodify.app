import subprocess
import sys
import pandas as pd
import numpy as np
import os
import requests
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils import load_model

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================
# CLEANUP CSV TEMPORANEI
# ==============================

def cleanup_csv_files():
    """Elimina i file CSV temporanei dopo l'elaborazione."""
    csv_files = [
        os.path.join(BASE_DIR, "playlist_tracks.csv"),
        os.path.join(BASE_DIR, "playlist_with_uuid.csv"),
        os.path.join(BASE_DIR, "playlist_with_features.csv")
    ]
    
    for csv_file in csv_files:
        try:
            if os.path.exists(csv_file):
                os.remove(csv_file)
                print(f"[CLEANUP] Deleted: {csv_file}")
        except Exception as e:
            print(f"[CLEANUP] Error deleting {csv_file}: {e}")

# ==============================
# SESSION POOLING (Connection reuse)
# ==============================

def _create_session_with_retry() -> requests.Session:
    """Crea session con connection pooling e retry automatico."""
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Session globale riutilizzata
_session = _create_session_with_retry()

# ==============================
# INPUT API
# ==============================

class PlaylistRequest(BaseModel):
    playlist_url: str

# ==============================
# FEATURE ORDER (CRITICO)
# ==============================

FEATURE_COLUMNS = [
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo"
]

# ==============================
# MOOD MAPPING
# ==============================

MOOD_LABELS = {
    0: "sad",
    1: "happy",
    2: "energetic",
    3: "calm"
}

MOOD_SEARCH_KEYWORDS = {
    0: "sad",
    1: "happy",
    2: "energetic",
    3: "calm"
}

MOOD_FALLBACK_KEYWORDS = {
    0: ["melancholy", "blue", "sad songs", "depression", "lonely", "sorrowful", "heartbreak", "blues"],
    1: ["joy", "uplifting", "feel good", "happy songs", "cheerful", "optimistic", "vibrant", "sunny"],
    2: ["dance", "party", "electronic", "energetic", "uptempo", "electro", "bass", "workout"],
    3: ["relaxation", "ambient", "chill", "peaceful", "meditation", "calm", "zen", "mellow"]
}

# ==============================
# CARICA MODELLO
# ==============================

model = load_model()

# ==============================
# PIPELINE ORCHESTRATOR
# ==============================

def run_pipeline(playlist_url: str):

    csv_1 = os.path.join(BASE_DIR, "playlist_tracks.csv")
    csv_2 = os.path.join(BASE_DIR, "playlist_with_uuid.csv")
    csv_3 = os.path.join(BASE_DIR, "playlist_with_features.csv")

    # Esegui step 1 (link -> CSV)
    print(f"[PIPELINE] Step 1: Converting playlist URL to CSV...")
    p1 = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "linktocsvconverter.py"), playlist_url, csv_1],
        check=False,
        capture_output=True,
        text=True,
    )
    if p1.returncode != 0:
        print(f"[PIPELINE] Step 1 FAILED:")
        print(f"STDOUT: {p1.stdout}")
        print(f"STDERR: {p1.stderr}")
        raise subprocess.CalledProcessError(p1.returncode, p1.args, output=p1.stdout, stderr=p1.stderr)
    print(f"[PIPELINE] Step 1 OK\n{p1.stdout}")

    # Step 2 (CSV -> UUID)
    print(f"[PIPELINE] Step 2: Adding UUIDs...")
    p2 = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "uuidfromname.py"), csv_1, csv_2],
        check=False,
        capture_output=True,
        text=True,
    )
    if p2.returncode != 0:
        print(f"[PIPELINE] Step 2 FAILED:")
        print(f"STDOUT: {p2.stdout}")
        print(f"STDERR: {p2.stderr}")
        raise subprocess.CalledProcessError(p2.returncode, p2.args, output=p2.stdout, stderr=p2.stderr)
    print(f"[PIPELINE] Step 2 OK\n{p2.stdout}")

    # Step 3 (UUID -> features)
    print(f"[PIPELINE] Step 3: Fetching audio features...")
    p3 = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "soundcharts.py"), csv_2, csv_3],
        check=False,
        capture_output=True,
        text=True,
    )
    if p3.returncode != 0:
        print(f"[PIPELINE] Step 3 FAILED:")
        print(f"STDOUT: {p3.stdout}")
        print(f"STDERR: {p3.stderr}")
        raise subprocess.CalledProcessError(p3.returncode, p3.args, output=p3.stdout, stderr=p3.stderr)
    print(f"[PIPELINE] Step 3 OK\n{p3.stdout}")

    print(f"[PIPELINE] Pipeline completed successfully!")
    # If all ok, return final CSV path
    return csv_3

# ==============================
# MOOD CALCULATION
# ==============================

def calculate_moods(csv_with_features: str):

    df = pd.read_csv(csv_with_features)

    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Colonne feature mancanti: {missing}")

    X = df[FEATURE_COLUMNS]

    # Predizione mood per brano
    df["label"] = model.predict(X).astype(int)

    # Mood playlist complessiva
    overall = {
        "mood_mean": float(df["label"].mean()),
        "mood_mode": int(df["label"].mode()[0]),
        "mood_distribution": df["label"].value_counts(normalize=True).to_dict(),
        "total_tracks": int(len(df))
    }

    # Sovrascrive CSV finale
    df.to_csv(csv_with_features, index=False)

    return df, overall

# ==============================
# LASTFM RECOMMENDATIONS
# ==============================

# ==============================
# LASTFM RECOMMENDATIONS (OTTIMIZZATO)
# ==============================

@lru_cache(maxsize=256)
def _search_lastfm_track(search_keyword: str, lastfm_api_key: str, limit: int = 5) -> dict:
    """
    Cached search su Last.fm con session pooling.
    """
    try:
        url = "https://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "track.search",
            "track": search_keyword,
            "api_key": lastfm_api_key,
            "format": "json",
            "limit": limit
        }
        
        response = _session.get(url, params=params, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            tracks = data.get("results", {}).get("trackmatches", {}).get("track", [])
            return {"tracks": tracks if isinstance(tracks, list) else [tracks] if tracks else []}
        
        return {"tracks": []}
        
    except Exception as e:
        print(f"[LASTFM] Search error for '{search_keyword}': {str(e)}")
        return {"tracks": []}

def _fetch_mood_recommendation(mood_id: int, mood_name: str, df: pd.DataFrame, lastfm_api_key: str):
    """
    Ricerca raccomandazione per UN mood con session pooling.
    """
    mood_tracks = df[df["label"] == mood_id]
    
    if len(mood_tracks) > 0:
        # Canzone simile dalla playlist
        first_track = mood_tracks.iloc[0]
        title = first_track.get("title", "")
        artist = first_track.get("artist", "")
        
        try:
            url = "https://ws.audioscrobbler.com/2.0/"
            params = {
                "method": "track.getSimilar",
                "artist": artist,
                "track": title,
                "api_key": lastfm_api_key,
                "format": "json",
                "limit": 5
            }
            
            response = _session.get(url, params=params, timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                similar_tracks = data.get("similartracks", {}).get("track", [])
                
                if similar_tracks:
                    track = similar_tracks[0] if isinstance(similar_tracks, list) else similar_tracks
                    
                    return {
                        f"mood_{mood_id}_{mood_name}": {
                            "mood_id": mood_id,
                            "mood_name": mood_name,
                            "source": "similar_track",
                            "original_track": f"{title} - {artist}",
                            "recommended_track": f"{track.get('name', '')} - {track.get('artist', {}).get('name', '')}",
                            "similarity": float(track.get('match', 0))
                        }
                    }
        except Exception as e:
            print(f"[LASTFM] Similar search error for mood {mood_id}: {str(e)}")
    
    # Fallback: ricerca generica per mood
    search_keywords = [MOOD_SEARCH_KEYWORDS.get(mood_id, mood_name)]
    search_keywords.extend(MOOD_FALLBACK_KEYWORDS.get(mood_id, []))
    random.shuffle(search_keywords)
    
    for search_keyword in search_keywords:
        result = _search_lastfm_track(search_keyword, lastfm_api_key, limit=5)
        tracks = result.get("tracks", [])
        
        if tracks:
            track = random.choice(tracks)
            
            return {
                f"mood_{mood_id}_{mood_name}": {
                    "mood_id": mood_id,
                    "mood_name": mood_name,
                    "source": "generic_search",
                    "recommended_track": f"{track.get('name', 'Unknown')} - {track.get('artist', 'Unknown')}",
                    "listeners": int(track.get('listeners', 0))
                }
            }
    
    # Fallback: artista casuale
    fallback_artists = {
        0: ["Radiohead", "Nick Cave", "Bon Iver", "The National", "Elliott Smith", "Tom Waits"],
        1: ["Pharrell Williams", "Walk the Moon", "MGMT", "Two Door Cinema Club", "Foster the People", "Phoenix"],
        2: ["Daft Punk", "The Chemical Brothers", "Fatboy Slim", "Prodigy", "Pendulum", "Deadmau5"],
        3: ["Bon Iver", "Sigur Rós", "Explosions in the Sky", "Tycho", "Ólafur Arnalds", "Nils Frahm"]
    }
    
    artist_list = fallback_artists.get(mood_id, [])
    if artist_list:
        artist = random.choice(artist_list)
        
        try:
            url = "https://ws.audioscrobbler.com/2.0/"
            params = {
                "method": "artist.getTopTracks",
                "artist": artist,
                "api_key": lastfm_api_key,
                "format": "json",
                "limit": 5
            }
            
            response = _session.get(url, params=params, timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get("toptracks", {}).get("track", [])
                
                if tracks:
                    track = random.choice(tracks) if isinstance(tracks, list) else tracks
                    track_artist = track.get('artist', {})
                    track_artist_name = track_artist.get('name', 'Unknown') if isinstance(track_artist, dict) else track_artist
                    
                    return {
                        f"mood_{mood_id}_{mood_name}": {
                            "mood_id": mood_id,
                            "mood_name": mood_name,
                            "source": "artist_fallback",
                            "recommended_track": f"{track.get('name', 'Unknown')} - {track_artist_name}",
                            "listeners": int(track.get('playcount', 0))
                        }
                    }
        except Exception as e:
            print(f"[LASTFM] Artist fallback error for mood {mood_id}: {str(e)}")
    
    # Ultimo fallback
    return {
        f"mood_{mood_id}_{mood_name}": {
            "mood_id": mood_id,
            "mood_name": mood_name,
            "source": "error",
            "error": "Unable to find recommendations"
        }
    }

def get_similar_songs_by_mood(csv_with_features: str, lastfm_api_key: str = "481d0ece35e3d695d07d399427f5ef04"):
    """
    Ricerca raccomandazioni in PARALLELO per tutti i 4 mood.
    """
    if not lastfm_api_key:
        lastfm_api_key = os.getenv("LASTFM_API_KEY")
    
    if not lastfm_api_key:
        print("⚠️ Last.fm API key non configurata")
        return {}
    
    df = pd.read_csv(csv_with_features)
    print(f"[LASTFM] Loaded CSV with {len(df)} rows")
    print(f"[LASTFM] Unique moods: {sorted(df['label'].unique().tolist())}")
    print(f"[LASTFM] Starting parallel mood recommendations...")
    
    result = {}
    start_time = time.time()
    
    # Parallelize 4 mood searches con ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_fetch_mood_recommendation, mood_id, MOOD_LABELS[mood_id], df, lastfm_api_key): mood_id
            for mood_id in range(4)
        }
        
        for future in as_completed(futures):
            try:
                mood_result = future.result()
                result.update(mood_result)
            except Exception as e:
                print(f"[LASTFM] Executor error: {str(e)}")
    
    elapsed = time.time() - start_time
    print(f"[LASTFM] Parallel recommendations completed in {elapsed:.2f}s")
    
    return result

# ==============================
# ENDPOINT PRINCIPALE
# ==============================

@app.post("/process-playlist")
def process_playlist(req: PlaylistRequest):
    try:
        final_csv = run_pipeline(req.playlist_url)
        df, overall = calculate_moods(final_csv)
        similar_songs = get_similar_songs_by_mood(final_csv)

        response_data = {
            "status": "success",
            "playlist_url": req.playlist_url,
            "overall_mood": overall,
            "similar_songs_by_mood": similar_songs,
            "tracks": df.to_dict(orient="records")
        }
        
        # Cleanup: Elimina file CSV temporanei
        cleanup_csv_files()
        
        return response_data

    except subprocess.CalledProcessError as e:
        cleanup_csv_files()  # Cleanup anche in caso di errore
        return {"status": "error", "error": f"Errore script: {str(e)}"}

    except Exception as e:
        cleanup_csv_files()  # Cleanup anche in caso di errore
        return {"status": "error", "error": str(e)}

@app.get("/")
def root():
    return {"message": "PlayMoodify Playlist Pipeline API is running"}

