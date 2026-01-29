import os
import joblib
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv

# ==============================
# CARICAMENTO MODELLO
# ==============================

load_dotenv()

MODEL_REPO = "Alepnc04/PlayMoodifyModel"
MODEL_FILE = "PlayMoodify.pkl"

_model = None

# Carica il modello ML da HuggingFace Hub
def load_model():
    global _model
    if _model is None:
        model_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            token=os.environ.get("HF_TOKEN")
        )
        _model = joblib.load(model_path)
    return _model

# ==============================
# FILE CLEANUP
# ==============================


# Eliminiamo i file CSV temporanei dopo l'elaborazione.
def cleanup_csv_files(base_dir: str = None):
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    csv_files = [
        os.path.join(base_dir, "playlist_tracks.csv"),
        os.path.join(base_dir, "playlist_with_uuid.csv"),
        os.path.join(base_dir, "playlist_with_features.csv")
    ]
    
    for csv_file in csv_files:
        try:
            if os.path.exists(csv_file):
                os.remove(csv_file)
        except Exception as e:
            print(f"[CLEANUP] Error deleting {csv_file}: {e}")
