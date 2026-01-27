import subprocess
import sys
import pandas as pd
import numpy as np
import os
import requests

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
    0: "sad songs",
    1: "happy uplifting",
    2: "energetic dance",
    3: "calm relaxing"
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

def get_similar_songs_by_mood(csv_with_features: str, lastfm_api_key: str = "481d0ece35e3d695d07d399427f5ef04"):
    """
    Ricerca 1 canzone per ogni mood usando l'API di Last.fm.
    - Se il mood è presente nella playlist: canzone simile alla prima del mood
    - Se il mood non è presente: canzone generica basata su keyword del mood
    
    Args:
        csv_with_features: Percorso del CSV con le feature e i label
        lastfm_api_key: API key di Last.fm
    
    Returns:
        Dict con canzoni per ogni mood (0-3)
    """
    if not lastfm_api_key:
        lastfm_api_key = os.getenv("LASTFM_API_KEY")
    
    if not lastfm_api_key:
        print("⚠️ Last.fm API key non configurata")
        return {}
    
    df = pd.read_csv(csv_with_features)
    print(f"[LASTFM] Loaded CSV with {len(df)} rows")
    print(f"[LASTFM] Unique moods: {sorted(df['label'].unique().tolist())}")
    
    result = {}
    
    # Itera su tutti i 4 mood (0, 1, 2, 3)
    for mood_id in range(4):
        mood_name = MOOD_LABELS.get(mood_id, "unknown")
        mood_tracks = df[df["label"] == mood_id]
        
        print(f"[LASTFM] Processing mood {mood_id} ({mood_name}) - {len(mood_tracks)} tracks")
        
        if len(mood_tracks) > 0:
            # Se il mood è presente nella playlist, cercare simile
            first_track = mood_tracks.iloc[0]
            title = first_track.get("title", "")
            artist = first_track.get("artist", "")
            print(f"[LASTFM]   Found in playlist, looking for similar to: {title} - {artist}")
            
            try:
                url = "https://ws.audioscrobbler.com/2.0/"
                params = {
                    "method": "track.getSimilar",
                    "artist": artist,
                    "track": title,
                    "api_key": lastfm_api_key,
                    "format": "json",
                    "limit": 1
                }
                
                response = requests.get(url, params=params, timeout=5)
                print(f"[LASTFM]   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    similar_tracks = data.get("similartracks", {}).get("track", [])
                    
                    if similar_tracks:
                        if isinstance(similar_tracks, list):
                            similar = similar_tracks[0]
                        else:
                            similar = similar_tracks
                        
                        result[f"mood_{mood_id}_{mood_name}"] = {
                            "mood_id": mood_id,
                            "mood_name": mood_name,
                            "source": "similar_track",
                            "original_track": f"{title} - {artist}",
                            "recommended_track": f"{similar.get('name', '')} - {similar.get('artist', {}).get('name', '')}",
                            "similarity": float(similar.get('match', 0))
                        }
                    else:
                        result[f"mood_{mood_id}_{mood_name}"] = {
                            "mood_id": mood_id,
                            "mood_name": mood_name,
                            "source": "similar_track",
                            "error": "No similar tracks found on Last.fm"
                        }
                else:
                    result[f"mood_{mood_id}_{mood_name}"] = {
                        "mood_id": mood_id,
                        "mood_name": mood_name,
                        "source": "similar_track",
                        "error": f"Last.fm API error: {response.status_code}"
                    }
                    
            except Exception as e:
                print(f"[LASTFM]   Exception: {str(e)}")
                result[f"mood_{mood_id}_{mood_name}"] = {
                    "mood_id": mood_id,
                    "mood_name": mood_name,
                    "source": "similar_track",
                    "error": str(e)
                }
        else:
            # Se il mood non è nella playlist, cercare una canzone generica per quel mood
            print(f"[LASTFM]   Not found in playlist, searching generic keyword...")
            search_keyword = MOOD_SEARCH_KEYWORDS.get(mood_id, mood_name)
            
            try:
                url = "https://ws.audioscrobbler.com/2.0/"
                params = {
                    "method": "track.search",
                    "track": search_keyword,
                    "api_key": lastfm_api_key,
                    "format": "json",
                    "limit": 1
                }
                
                response = requests.get(url, params=params, timeout=5)
                print(f"[LASTFM]   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    tracks = data.get("results", {}).get("trackmatches", {}).get("track", [])
                    
                    if tracks:
                        if isinstance(tracks, list):
                            track = tracks[0]
                        else:
                            track = tracks
                        
                        result[f"mood_{mood_id}_{mood_name}"] = {
                            "mood_id": mood_id,
                            "mood_name": mood_name,
                            "source": "generic_search",
                            "recommended_track": f"{track.get('name', '')} - {track.get('artist', '')}",
                            "listeners": int(track.get('listeners', 0))
                        }
                    else:
                        result[f"mood_{mood_id}_{mood_name}"] = {
                            "mood_id": mood_id,
                            "mood_name": mood_name,
                            "source": "generic_search",
                            "error": "No tracks found for this mood keyword"
                        }
                else:
                    result[f"mood_{mood_id}_{mood_name}"] = {
                        "mood_id": mood_id,
                        "mood_name": mood_name,
                        "source": "generic_search",
                        "error": f"Last.fm API error: {response.status_code}"
                    }
                    
            except Exception as e:
                print(f"[LASTFM]   Exception: {str(e)}")
                result[f"mood_{mood_id}_{mood_name}"] = {
                    "mood_id": mood_id,
                    "mood_name": mood_name,
                    "source": "generic_search",
                    "error": str(e)
                }
    
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

        return {
            "status": "success",
            "playlist_url": req.playlist_url,
            "overall_mood": overall,
            "similar_songs_by_mood": similar_songs,
            "tracks": df.to_dict(orient="records")
        }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": f"Errore script: {str(e)}"}

    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/")
def root():
    return {"message": "PlayMoodify Playlist Pipeline API is running"}

