import requests
import sys
import pandas as pd
import csv
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ==============================
# API SOUNDCHARTS
# ==============================

# Recuperiamo le feature audio da SoundCharts API usando l'UUID della traccia.
def get_audio_features_by_uuid(uuid: str) -> Optional[Dict]:
    
    try:
        url = f"https://customer.api.soundcharts.com/api/v2.25/song/{uuid}"

        headers = {
            'x-app-id': 'PLEOPARDI-API_52D50A96',
            'x-api-key': '31fb4ecb77abe4e9',
        }

        response = requests.get(url, headers=headers, timeout=2)

        if response.status_code != 200:
            return None

        data = response.json()

        # Estraiamo le feature audio
        audio = data.get("object", {}).get("audio")
        if not audio:
            return None

        features = {
            "danceability": audio.get("danceability"),
            "energy": audio.get("energy"),
            "speechiness": audio.get("speechiness"),
            "acousticness": audio.get("acousticness"),
            "instrumentalness": audio.get("instrumentalness"),
            "liveness": audio.get("liveness"),
            "valence": audio.get("valence"),
            "tempo": audio.get("tempo")
        }

        return features

    except Exception as e:
        print(f"Errore recupero feature UUID {uuid}: {e}")
        return None

# ==============================
# CSV PROCESSOR
# ==============================

# Elaboriamo una singola riga del CSV per recuperare le feature audio
def process_single_uuid(row: Dict, index: int) -> Optional[Dict]:
    title = row.get('title', '').strip()
    artist = row.get('artist', '').strip()
    uuid = row.get('uuid', '').strip()
    
    # Saltiamo la riga se l'UUID è mancante
    if not uuid or uuid == 'N/A':
        return None
    
    features = get_audio_features_by_uuid(uuid)
    
    if not features:
        return None
    
    # Aggiungiamo le feature al risultato
    result = {
        "title": title,
        "artist": artist,
        "uuid": uuid,
        **features
    }
    
    return result


# Funzione principale per lettura del CSV e ricavo delle feature audio
def process_csv_and_get_audio_features(csv_file_path: str, output_file_path: str) -> List[Dict]:
    rows = []
    with open(csv_file_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)
    
    results = []
    
    # Elaboriamo le tracce in parallelo con 8 worker
    with ThreadPoolExecutor(max_workers=8) as executor:
        tasks = [
            executor.submit(process_single_uuid, row, i + 1)
            for i, row in enumerate(rows)
        ]
        
        for future in as_completed(tasks):
            result = future.result()
            if result:
                results.append(result)
    
    # Scriviamo i risultati nel CSV di output
    fieldnames = [
        "title", "artist", "uuid",
        "danceability", "energy", "speechiness", "acousticness",
        "instrumentalness", "liveness", "valence", "tempo"
    ]

    with open(output_file_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        if results:
            writer.writerows(results)

    return results


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 2:
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "playlist_with_features.csv"

    if not os.path.exists(input_csv):
        sys.exit(2)

    try:
        results = process_csv_and_get_audio_features(input_csv, output_csv)
    except Exception as e:
        print(f"Error processing CSV: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
