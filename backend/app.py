import subprocess
import sys
import os
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils import load_model, cleanup_csv_files
from recommendations import get_similar_songs_by_mood
from mood_analysis import calculate_moods

# ==============================
# FASTAPI SETUP
# ==============================

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
# CARICA MODELLO
# ==============================

model = load_model()

# ==============================
# PIPELINE ORCHESTRATOR
# ==============================

# Esegue la pipeline completa
def run_pipeline(playlist_url: str):
    
    # Definiamo i percorsi dei file CSV temporanei
    csv_1 = os.path.join(BASE_DIR, "playlist_tracks.csv")
    csv_2 = os.path.join(BASE_DIR, "playlist_with_uuid.csv")
    csv_3 = os.path.join(BASE_DIR, "playlist_with_features.csv")

    # Otteniamo il CSV dalla playlist Spotify
    p1 = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "linktocsvconverter.py"), playlist_url, csv_1],
        check=False,
        capture_output=True,
        text=True,
    )
    if p1.returncode != 0:
        raise subprocess.CalledProcessError(p1.returncode, p1.args, output=p1.stdout, stderr=p1.stderr)

    # Otteniamo gli UUID per le ogni traccia
    p2 = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "uuidfromname.py"), csv_1, csv_2],
        check=False,
        capture_output=True,
        text=True,
    )
    if p2.returncode != 0:
        raise subprocess.CalledProcessError(p2.returncode, p2.args, output=p2.stdout, stderr=p2.stderr)

    # Otteniamo le feature audio per ogni traccia
    p3 = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "soundcharts.py"), csv_2, csv_3],
        check=False,
        capture_output=True,
        text=True,
    )
    if p3.returncode != 0:
        raise subprocess.CalledProcessError(p3.returncode, p3.args, output=p3.stdout, stderr=p3.stderr)

    return csv_3

# ==============================
# API ENDPOINTS
# ==============================

@app.post("/process-playlist")

# Esegue l'intera pipeline per una playlist Spotify
def process_playlist(req: PlaylistRequest):
    try:
        final_csv = run_pipeline(req.playlist_url)
        df, overall = calculate_moods(final_csv, model)
        similar_songs = get_similar_songs_by_mood(final_csv)

        response_data = {
            "status": "success",
            "playlist_url": req.playlist_url,
            "overall_mood": overall,
            "similar_songs_by_mood": similar_songs,
            "tracks": df.to_dict(orient="records")
        }
        
        cleanup_csv_files(BASE_DIR)
        
        return response_data

    except subprocess.CalledProcessError as e:
        cleanup_csv_files(BASE_DIR)
        return {"status": "error", "error": f"Errore script: {str(e)}"}

    except Exception as e:
        cleanup_csv_files(BASE_DIR)
        return {"status": "error", "error": str(e)}


