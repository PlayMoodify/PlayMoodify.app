import requests
import csv
from typing import Optional, List, Dict
from urllib.parse import quote
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

@lru_cache(maxsize=512)
def get_uuid_from_soundcharts(song_name: str, artist_name: Optional[str] = None) -> Optional[str]:
    """
    Ricerca una canzone su SoundCharts API e restituisce l'UUID (CACHED).
    
    Args:
        song_name: Nome della canzone
        artist_name: Nome dell'artista (opzionale)
        
    Returns:
        UUID della canzone oppure None se non trovato
    """
    try:
        # Prepara il parametro di ricerca
        query = song_name
        if artist_name:
            query = f"{song_name} {artist_name}"
        
        # Encode il query nell'URL
        encoded_query = quote(query)
        
        # Endpoint di ricerca SoundCharts con query nell'URL
        url = f"https://customer.api.soundcharts.com/api/v2/song/search/{encoded_query}"
        
        headers = {
            'x-app-id': 'BPANICO-API_F564F184',
            'x-api-key': '98bd73bdcbdcf5aa',
        }

        params = {
            'offset': '0',
            'limit': '20',
        }
        
        response = _session.get(url, headers=headers, params=params, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            
            # Estrai l'UUID dal primo risultato dalla chiave "items"
            if data and "items" in data and len(data["items"]) > 0:
                uuid = data["items"][0].get("uuid")
                print(f"UUID trovato: {uuid}")
                return uuid
            else:
                print("Nessuna canzone trovata")
                return None
        else:
            print(f"Errore SoundCharts: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Errore nella ricerca: {e}")
        return None

def _process_single_track(row: Dict) -> Dict[str, str]:
    """Worker function per ricercare UUID di UN brano in parallelo."""
    title = row.get('title', '').strip()
    artist = row.get('artist', '').strip()
    
    if not title:
        print(f"Riga ignorata: title vuoto")
        return None
    
    print(f"Ricerca: {title} - {artist}")
    uuid = get_uuid_from_soundcharts(title, artist)
    
    return {
        'title': title,
        'artist': artist,
        'uuid': uuid if uuid else 'N/A'
    }

def process_csv_and_get_uuids(csv_file_path: str, output_file_path: str) -> List[Dict[str, str]]:
    """
    Legge un file CSV contenente title e artist, 
    recupera l'UUID per ogni canzone (PARALLELO) e salva i risultati in un nuovo CSV.
    
    Args:
        csv_file_path: Percorso del file CSV di input (colonne: title, artist)
        output_file_path: Percorso del file CSV di output
        
    Returns:
        Lista di dizionari con title, artist e uuid
    """
    results = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)
        
        print(f"[UUIDFROMNAME] Processing {len(rows)} tracks in parallel (6 workers)...")
        start_time = time.time()
        
        # Parallelize con 6 worker threads
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(_process_single_track, row)
                for row in rows
            ]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        elapsed = time.time() - start_time
        print(f"[UUIDFROMNAME] Parallel processing completed in {elapsed:.2f}s")
        
        # Salva i risultati in un nuovo CSV
        with open(output_file_path, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['title', 'artist', 'uuid']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nRisultati salvati in: {output_file_path}")
        return results
        
    except FileNotFoundError:
        print(f"Errore: File {csv_file_path} non trovato")
        return []
    except Exception as e:
        print(f"Errore nel processamento del CSV: {e}")
        return []


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python uuidfromname.py <input_csv> <output_csv>")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2]
    
    try:
        results = process_csv_and_get_uuids(input_csv, output_csv)
        print(f"Done. Processed {len(results)} tracks")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
