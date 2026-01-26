import requests
import csv
from typing import Optional, Dict, List
from uuidfromname import get_uuid_from_soundcharts

def get_audio_features_by_uuid(uuid: str) -> Optional[Dict]:
    """
    Recupera le feature audio da SoundCharts API usando l'UUID della canzone.
    
    Args:
        uuid: UUID della canzone su SoundCharts
        
    Returns:
        Dict con le feature audio oppure None se errore
    """
    try:
        # Endpoint SoundCharts per ottenere le feature audio
        url = f"https://customer.api.soundcharts.com/api/v2.25/song/{uuid}"
        
        headers = {
            'x-app-id': 'APANICO-API_5645D799',
            'x-api-key': '0428d41225b3c115',
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Estrai le feature audio da object.audio
            if data and "object" in data and "audio" in data["object"]:
                audio_features = data["object"]["audio"]
                return {
                    "acousticness": audio_features.get("acousticness"),
                    "danceability": audio_features.get("danceability"),
                    "energy": audio_features.get("energy"),
                    "instrumentalness": audio_features.get("instrumentalness"),
                    "liveness": audio_features.get("liveness"),
                    "speechiness": audio_features.get("speechiness"),
                    "tempo": audio_features.get("tempo"),
                    "valence": audio_features.get("valence")
                }
            else:
                print("Feature audio non trovate nella risposta")
                return None
        else:
            print(f"Errore SoundCharts: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Errore nel recupero delle feature: {e}")
        return None


def get_audio_features_by_song_name(song_name: str, artist_name: Optional[str] = None) -> Optional[Dict]:
    """
    Funzione principale: ricerca la canzone per nome, ottiene l'UUID e recupera le feature audio.
    
    Args:
        song_name: Nome della canzone
        artist_name: Nome dell'artista (opzionale)
        
    Returns:
        Dict con le feature audio oppure None se errore
    """
    # Ricerca l'UUID da SoundCharts
    
    uuid =  get_uuid_from_soundcharts(song_name, artist_name)
    
    if not uuid:
        print("UUID non trovato")
        return None
    
    # Recupera le feature audio usando l'UUID
    features = get_audio_features_by_uuid(uuid)
    
    return features


def process_csv_and_get_audio_features(csv_file_path: str, output_file_path: str = "playlist_tracks_with_features.csv") -> List[Dict]:
    """
    Legge un file CSV contenente title, artist e uuid (opzionale),
    recupera le feature audio per ogni canzone e salva i risultati in un nuovo CSV.
    
    Se l'UUID non è disponibile, lo ricerca automaticamente dal titolo e artista.
    
    Args:
        csv_file_path: Percorso del file CSV di input con UUID (o title/artist)
        output_file_path: Percorso del file CSV di output con le feature audio
        
    Returns:
        Lista di dizionari con title, artist, uuid e feature audio
    """
    results = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            for i, row in enumerate(reader, 1):
                title = row.get('title', '').strip()
                artist = row.get('artist', '').strip()
                uuid = row.get('uuid', '').strip() if 'uuid' in row else None
                
                if not title:
                    print(f"Riga {i}: title vuoto, salto")
                    continue
                
                print(f"[{i}] Elaborando: {title} - {artist}")
                
                # Se UUID non disponibile, ricerca automaticamente
                if not uuid or uuid == 'N/A':
                    print(f"  ↳ UUID non disponibile, ricerca in corso...")
                    uuid = get_uuid_from_soundcharts(title, artist)
                
                result = {
                    'title': title,
                    'artist': artist,
                    'uuid': uuid if uuid else 'N/A'
                }
                
                # Recupera le feature audio
                if uuid and uuid != 'N/A':
                    print(f"  ↳ Recupero feature audio (UUID: {uuid})")
                    features = get_audio_features_by_uuid(uuid)
                    
                    if features:
                        result.update(features)
                        print(f"  ✓ Feature audio recuperate")
                    else:
                        # Se non trovate, aggiungi N/A per tutte le feature
                        result.update({
                            'acousticness': 'N/A',
                            'danceability': 'N/A',
                            'energy': 'N/A',
                            'instrumentalness': 'N/A',
                            'liveness': 'N/A',
                            'speechiness': 'N/A',
                            'tempo': 'N/A',
                            'valence': 'N/A'
                        })
                        print(f"  ✗ Feature audio non trovate")
                else:
                    # Se UUID non trovato, aggiungi N/A per tutte le feature
                    result.update({
                        'acousticness': 'N/A',
                        'danceability': 'N/A',
                        'energy': 'N/A',
                        'instrumentalness': 'N/A',
                        'liveness': 'N/A',
                        'speechiness': 'N/A',
                        'tempo': 'N/A',
                        'valence': 'N/A'
                    })
                    print(f"  ✗ UUID non trovato")
                
                results.append(result)
        
        # Salva i risultati in un nuovo CSV
        if results:
            fieldnames = ['title', 'artist', 'uuid', 'acousticness', 'danceability', 
                         'energy', 'instrumentalness', 'liveness', 'speechiness', 'tempo', 'valence']
            
            with open(output_file_path, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            print(f"\n✓ Risultati salvati in: {output_file_path}")
        
        return results
        
    except FileNotFoundError:
        print(f"✗ Errore: File {csv_file_path} non trovato")
        return []
    except Exception as e:
        print(f"✗ Errore nel processamento del CSV: {e}")
        import traceback
        traceback.print_exc()
        return []
