import requests
import sys
import pandas as pd
import csv
from typing import Optional, Dict, List

# ==============================
# API SOUNDCHARTS
# ==============================

def get_audio_features_by_uuid(uuid: str) -> Optional[Dict]:
    """
    Recupera le feature audio da SoundCharts API usando l'UUID della canzone.
    """
    try:
        url = f"https://customer.api.soundcharts.com/api/v2.25/song/{uuid}"

        headers = {
            'x-app-id': 'APANICO-API_5645D799',
            'x-api-key': '0428d41225b3c115',
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Errore SoundCharts [{uuid}]: {response.status_code}")
            return None

        data = response.json()

        audio = data.get("object", {}).get("audio")
        if not audio:
            print(f"Feature audio mancanti per UUID {uuid}")
            return None

        return {
            "danceability": audio.get("danceability"),
            "energy": audio.get("energy"),
            "speechiness": audio.get("speechiness"),
            "acousticness": audio.get("acousticness"),
            "instrumentalness": audio.get("instrumentalness"),
            "liveness": audio.get("liveness"),
            "valence": audio.get("valence"),
            "tempo": audio.get("tempo")
        }

    except Exception as e:
        print(f"Errore recupero feature UUID {uuid}: {e}")
        return None

# ==============================
# CSV PROCESSOR (UUID ONLY)
# ==============================

def process_csv_and_get_audio_features(csv_file_path: str, output_file_path: str) -> List[Dict]:
    """
    Legge CSV con UUID.
    Se UUID presente → aggiunge audio features.
    Se UUID mancante → SKIP.
    
    IMPORTANTE: Crea sempre il CSV di output, anche se vuoto.
    """

    results = []

    with open(csv_file_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        for i, row in enumerate(reader, 1):
            title = row.get('title', '').strip()
            artist = row.get('artist', '').strip()
            uuid = row.get('uuid', '').strip()

            if not uuid or uuid == 'N/A':
                print(f"[{i}] SKIP (UUID mancante): {title} - {artist}")
                continue

            print(f"[{i}] Elaborando UUID {uuid} → {title} - {artist}")

            features = get_audio_features_by_uuid(uuid)

            if not features:
                print(f"  ✗ Feature non trovate, skip")
                continue

            result = {
                "title": title,
                "artist": artist,
                "uuid": uuid,
                **features
            }

            results.append(result)
            print(f"  ✓ Feature aggiunte")

    # ==============================
    # SCRITTURA CSV (SEMPRE)
    # ==============================

    fieldnames = [
        "title", "artist", "uuid",
        "danceability","energy","speechiness","acousticness","instrumentalness",
        "liveness","valence","tempo"
    ]

    with open(output_file_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        if results:
            writer.writerows(results)

    if results:
        print(f"\n✓ CSV feature salvato in: {output_file_path} ({len(results)} brani)")
    else:
        print(f"\n⚠️ CSV vuoto creato in: {output_file_path} (nessuna canzone valida)")

    return results


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: python soundcharts.py <input_csv> [output_csv]")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "playlist_with_features.csv"

    print(f"Input CSV: {input_csv}")
    print(f"Output CSV: {output_csv}")

    # Verifica che il file di input esista
    if not os.path.exists(input_csv):
        print(f"ERRORE: Il file di input '{input_csv}' non esiste.")
        print("Assicurati che lo script uuidfromname.py sia stato eseguito prima di questo.")
        sys.exit(2)

    try:
        results = process_csv_and_get_audio_features(input_csv, output_csv)
        print(f"Done. Processed {len(results)} tracks")
    except Exception as e:
        print(f"Error processing CSV: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
