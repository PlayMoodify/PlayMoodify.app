import requests
from typing import Optional, Dict
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


# Esempio di utilizzo
if __name__ == "__main__":
    # Test: ricerca canzone per nome e ottieni feature audio
    features = get_audio_features_by_song_name("Blinding Lights", "The Weeknd")
    if features:
        print(f"Feature audio trovate: {features}")
    else:
        print("Feature audio non trovate")
