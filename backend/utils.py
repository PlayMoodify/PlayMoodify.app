import os
import joblib
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv

load_dotenv()

MODEL_REPO = "Alepnc04/PlayMoodifyModel"
MODEL_FILE = "PlayMoodify.pkl"

_model = None

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
