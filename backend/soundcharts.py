import requests
import sys
import pandas as pd
import csv
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import lru_cache
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# ==============================
# SESSION POOLING
# ==============================

def _create_session_with_retry() -> requests.Session:
    """Crea session con connection pooling."""
    session = requests.Session()
    retry = Retry(
        total=1,
        backoff_factor=0.2,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=15, pool_maxsize=15)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

_session = _create_session_with_retry()

# ==============================
# API SOUNDCHARTS (con cache)
# ==============================

@lru_cache(maxsize=512)
def get_audio_features_by_uuid(uuid: str) -> Optional[Dict]:
    """
    Recupera le feature audio da SoundCharts API (CACHED).
    """
    try:
        url = f"https://customer.api.soundcharts.com/api/v2.25/song/{uuid}"

        headers = {
            'x-app-id': 'APANICO-API1_D6B65B3F',
            'x-api-key': '47408a8357d3837a',
        }

        response = _session.get(url, headers=headers, timeout=2)

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
# CSV PROCESSOR (UUID ONLY) - PARALLELIZZATO
# ==============================

def _process_single_uuid(row: Dict, index: int) -> Optional[Dict]:
    """Worker function per processare UN UUID in parallelo."""
    title = row.get('title', '').strip()
    artist = row.get('artist', '').strip()
    uuid = row.get('uuid', '').strip()
    
    if not uuid or uuid == 'N/A':
        print(f"[{index}] SKIP (UUID mancante): {title} - {artist}")
        return None
    
    print(f"[{index}] Elaborando UUID {uuid} → {title} - {artist}")
    
    features = get_audio_features_by_uuid(uuid)
    
    if not features:
        print(f"  ✗ Feature non trovate, skip")
        return None
    
    result = {
        "title": title,
        "artist": artist,
        "uuid": uuid,
        **features
    }
    print(f"  ✓ Feature aggiunte")
    return result

def process_csv_and_get_audio_features(csv_file_path: str, output_file_path: str) -> List[Dict]:
    """
    Legge CSV con UUID.
    Se UUID presente → aggiunge audio features (PARALLELO).
    Se UUID mancante → SKIP.
    
    IMPORTANTE: Crea sempre il CSV di output, anche se vuoto.
    """
    results = []
    rows = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)
    
    print(f"[SOUNDCHARTS] Processing {len(rows)} tracks in parallel (8 workers)...")
    start_time = time.time()
    
    # Parallelize con 8 worker threads
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(_process_single_uuid, row, i+1)
            for i, row in enumerate(rows)
        ]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    
    elapsed = time.time() - start_time
    print(f"[SOUNDCHARTS] Parallel processing completed in {elapsed:.2f}s")
    
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
