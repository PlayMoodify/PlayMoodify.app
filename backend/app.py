import os
import joblib
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv
from pydantic import BaseModel
import numpy as np
from soundcharts import get_audio_features_by_song_name

load_dotenv()  # carica .env in locale

app = FastAPI()

# CORS per permettere richieste dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modello di input per le API
class AudioFeatures(BaseModel):
    acousticness: float
    danceability: float
    energy: float
    instrumentalness: float
    liveness: float
    speechiness: float
    tempo: float
    valence: float

class SongRequest(BaseModel):
    song_name: str
    artist_name: str = None

MODEL_REPO = "Alepnc04/PlayMoodifyModel"
MODEL_FILE = "PlayMoodify.pkl"

def load_model():
    model_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
        token=os.environ.get("HF_TOKEN")
    )

    model = joblib.load(model_path)
    return model

model = load_model()

@app.post("/predict")
def predict_mood(song: SongRequest):
    """
    Predice l'umore di una canzone dal suo nome.
    Ricerca le feature audio su SoundCharts e fa la predizione.
    """
    try:
        # Ricerca le feature audio della canzone
        features_dict = get_audio_features_by_song_name(song.song_name, song.artist_name)
        
        if not features_dict:
            return {"error": "Feature audio non trovate per questa canzone"}
        
        # Prepara l'array per il modello
        X = np.array([[
            features_dict["acousticness"],
            features_dict["danceability"],
            features_dict["energy"],
            features_dict["instrumentalness"],
            features_dict["liveness"],
            features_dict["speechiness"],
            features_dict["tempo"],
            features_dict["valence"]
        ]])
        
        # Fai la predizione
        mood = model.predict(X)[0]
        
        return {
            "song": song.song_name,
            "artist": song.artist_name or "Unknown",
            "mood": str(mood),
            "features": features_dict
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/predict-features")
def predict_mood_with_features(audio: AudioFeatures):
    """
    Predice l'umore fornendo direttamente le feature audio.
    """
    try:
        # Prepara l'array per il modello
        X = np.array([[
            audio.acousticness,
            audio.danceability,
            audio.energy,
            audio.instrumentalness,
            audio.liveness,
            audio.speechiness,
            audio.tempo,
            audio.valence
        ]])
        
        # Fai la predizione
        mood = model.predict(X)[0]
        
        return {
            "mood": str(mood),
            "features": audio.dict()
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def root():
    """Endpoint di test"""
    return {"message": "PlayMoodify API is running"}

@app.get("/docs")
def docs_info():
    """Info su come usare l'API"""
    return {
        "message": "PlayMoodify API",
        "endpoints": {
            "POST /predict": "Predice il mood di una canzone. Invia un JSON con song_name",
            "GET /": "Test endpoint",
            "/docs": "Documentazione interattiva (FastAPI Swagger)"
        },
        "swagger": "http://localhost:8000/docs"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)