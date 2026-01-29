import requests
import csv
from typing import Optional, List, Dict
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==============================
# API SOUNDCHARTS
# ==============================

# Ricerca l'UUID di una canzone tramite il titolo e l'artista su SoundCharts API
def get_uuid_from_soundcharts(song_name: str, artist_name: Optional[str] = None) -> Optional[str]:
    try:
        query = song_name
        if artist_name:
            query = f"{song_name} {artist_name}"
        
        # Correggiamo l'encoding della query per URL
        encoded_query = quote(query)
        
        url = f"https://customer.api.soundcharts.com/api/v2/song/search/{encoded_query}"
        
        headers = {
            'x-app-id': 'MBIANCHI-API_12DD631F',
            'x-api-key': '0214335ba5236638',
        }

        params = {
            'offset': '0',
            'limit': '20',
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            
            # Estrai l'UUID dal primo risultato
            if data and "items" in data and len(data["items"]) > 0:
                uuid = data["items"][0].get("uuid")
                return uuid
            else:
                return None
        else:
            return None
            
    except Exception as e:
        print(f"Errore nella ricerca: {e}")
        return None

# ==============================
# CSV PROCESSOR
# ==============================

# Elabora una singola traccia e cerca l'UUID
def process_single_track(row: Dict) -> Optional[Dict[str, str]]:
    
    title = row.get('title', '').strip()
    artist = row.get('artist', '').strip()
    
    if not title:
        return None
    
    uuid = get_uuid_from_soundcharts(title, artist)
    
    return {
        'title': title,
        'artist': artist,
        'uuid': uuid if uuid else 'N/A'
    }

# Ricerca gli UUID per tutte le tracce in un CSV
def process_csv_and_get_uuids(csv_file_path: str, output_file_path: str) -> List[Dict[str, str]]:
    # Leggiamo il CSV di input
    rows = []
    with open(csv_file_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)
    
    if len(rows) == 0:
        return []
    
    results = []
    
    # Utilizziamo ThreadPoolExecutor per elaborare in parallelo
    with ThreadPoolExecutor(max_workers=6) as executor:
        tasks = [
            executor.submit(process_single_track, row)
            for row in rows
        ]
        
        # Raccogliamo i risultati man mano
        for future in as_completed(tasks):
            result = future.result()
            if result:
                results.append(result)

    with open(output_file_path, 'w', newline='', encoding='utf-8') as outfile:
        fieldnames = ['title', 'artist', 'uuid']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python uuidfromname.py <input_csv> <output_csv>")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2]
    
    try:
        results = process_csv_and_get_uuids(input_csv, output_csv)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
