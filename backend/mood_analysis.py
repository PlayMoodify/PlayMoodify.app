import pandas as pd

# ==============================
# FEATURE AUDIO
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
# MOOD CALCULATION
# ==============================

# Prevediamo il mood delle singole tracce e calcoliamo statistiche complessive
def calculate_moods(csv_with_features: str, model):
    df = pd.read_csv(csv_with_features)

    # Controlliamo che tutte le colonne feature siano presenti
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        print(f"[MOOD] ⚠️ Colonne feature mancanti: {missing}")
        raise ValueError(f"Colonne feature mancanti: {missing}")

    # Verifica che ci siano tracce da analizzare
    if len(df) == 0:
        raise ValueError("Nessuna traccia disponibile per l'analisi del mood")

    # Estrazione delle feature audio dal csv
    X = df[FEATURE_COLUMNS]

    # Tramite il modello prevediamo il mood per ogni traccia
    df["label"] = model.predict(X).astype(int)

    # Calcolo delle statistiche sul mood della playlist
    overall = {
        "mood_mode": int(df["label"].mode()[0]),
        "mood_distribution": df["label"].value_counts(normalize=True).to_dict(),
        "total_tracks": int(len(df))
    }

    # Salviamo le etichette nel CSV
    df.to_csv(csv_with_features, index=False)

    return df, overall
