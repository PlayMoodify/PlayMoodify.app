import requests
from typing import Optional
from urllib.parse import quote

def get_uuid_from_soundcharts(song_name: str, artist_name: Optional[str] = None) -> Optional[str]:
    """
    Ricerca una canzone su SoundCharts API e restituisce l'UUID.
    
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
            'x-app-id': 'AMICHELE-API_70A2065B',
            'x-api-key': 'db90801903d86cfe',
        }

        params = {
            'offset': '0',
            'limit': '20',
        }
        
        response = requests.get(url, headers=headers, params=params)
        
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
            print(f"Errore SoundCharts: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Errore nella ricerca: {e}")
        return None


# Esempio di utilizzo
if __name__ == "__main__":
    # Test ricerca
    uuid = get_uuid_from_soundcharts("Blinding Lights", "The Weeknd")
    if uuid:
        print(f"UUID della canzone: {uuid}")
    else:
        print("UUID non trovato")

    
