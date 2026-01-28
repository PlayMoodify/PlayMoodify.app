import requests
import pandas as pd
from typing import Optional, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

# ==============================
# MOOD MAPPING
# ==============================

MOOD_LABELS = {
    0: "sad",
    1: "happy",
    2: "energetic",
    3: "calm"
}

MOOD_SEARCH_KEYWORDS = {
    0: "sad",
    1: "happy",
    2: "energetic",
    3: "calm"
}

# ==============================
# FALLBACK RECOMMENDATIONS (GUARANTEED)
# ==============================

FALLBACK_RECOMMENDATIONS = {
    "sad": {
        "track": "Someone Like You",
        "artist": "Adele",
        "strategy": "fallback"
    },
    "happy": {
        "track": "Walking on Sunshine",
        "artist": "Katrina & The Waves",
        "strategy": "fallback"
    },
    "energetic": {
        "track": "Shut Up and Dance",
        "artist": "Walk the Moon",
        "strategy": "fallback"
    },
    "calm": {
        "track": "Weightless",
        "artist": "Marconi Union",
        "strategy": "fallback"
    }
}

# ==============================
# LASTFM API FUNCTIONS
# ==============================

# Ricerca tracce su Last.fm per keyword
def search_lastfm_track(search_keyword: str, lastfm_api_key: str, limit: int = 5):

    max_retries = 2
    for attempt in range(max_retries):
        try:
            url = "https://ws.audioscrobbler.com/2.0/"
            params = {
                "method": "track.search",
                "track": search_keyword,
                "api_key": lastfm_api_key,
                "format": "json",
                "limit": limit
            }
            
            response = requests.get(url, params=params, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get("results", {}).get("trackmatches", {}).get("track", [])
                
                if isinstance(tracks, list):
                    return tracks
                elif tracks:
                    return [tracks]
                else:
                    return []
            
            return []
            
        except Exception as e:
            print(f"[LASTFM-SEARCH] Tentativo {attempt+1}/{max_retries} fallito per '{search_keyword}': {e}")
            if attempt < max_retries - 1:
                time.sleep(0.5)
    
    return []

# Ricerca traccia simile su Last.fm con API
def get_similar_track(title: str, artist: str, lastfm_api_key: str):
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            url = "https://ws.audioscrobbler.com/2.0/"
            params = {
                "method": "track.getSimilar",
                "artist": artist,
                "track": title,
                "api_key": lastfm_api_key,
                "format": "json",
                "limit": 5
            }
            
            response = requests.get(url, params=params, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                similar_tracks = data.get("similartracks", {}).get("track", [])
                
                # Prendi il primo risultato
                if isinstance(similar_tracks, list) and len(similar_tracks) > 0:
                    return similar_tracks[0]
                elif similar_tracks:
                    return similar_tracks
            
            return None
            
        except Exception as e:
            print(f"[LASTFM-SIMILAR] Tentativo {attempt+1}/{max_retries} fallito per '{title}': {e}")
            if attempt < max_retries - 1:
                time.sleep(0.5)
    return None

# Raccomandazione per un singolo mood con strategie multiple e fallback
def fetch_mood_recommendation(mood_id: int, mood_name: str, df: pd.DataFrame, lastfm_api_key: str, already_recommended: Set[str]) -> Dict:
    recommendations = {}
    
    # Tracce nel playlist con questo mood
    mood_tracks = df[df["label"] == mood_id]
    
    # STRATEGIA 1: Se mood è nella playlist, ricerca simile
    if len(mood_tracks) > 0:
        first_track = mood_tracks.iloc[0]
        title = first_track["title"]
        artist = first_track["artist"]
        
        similar_track = get_similar_track(title, artist, lastfm_api_key)
        
        if similar_track:
            track_name = similar_track.get('name', '')
            artist_name = similar_track.get('artist', {})
            if isinstance(artist_name, dict):
                artist_name = artist_name.get('name', '')
            
            track_key = f"{track_name} - {artist_name}".lower()
            
            if track_key and track_key not in already_recommended:
                recommendations[mood_name] = {
                    "track": track_name,
                    "artist": artist_name,
                    "strategy": "similar"
                }
                already_recommended.add(track_key)
                return recommendations
    
    # Ricerca per keyword nel caso in cui la prima non riuscisse
    keyword = MOOD_SEARCH_KEYWORDS.get(mood_id, mood_name)
    tracks = search_lastfm_track(keyword, lastfm_api_key, limit=5)
    
    if tracks and len(tracks) > 0:
        track = tracks[0]
        track_name = track.get("name", "")
        artist_name = track.get("artist", "")
        track_key = f"{track_name} - {artist_name}".lower()
        
        if track_key and track_key not in already_recommended:
            recommendations[mood_name] = {
                "track": track_name,
                "artist": artist_name,
                "strategy": "keyword"
            }
            already_recommended.add(track_key)
            return recommendations
    
    # FALLBACK in caso di fallimento delle precedenti due fa una raccomandazione semi-statica
    fallback = FALLBACK_RECOMMENDATIONS.get(mood_name)
    if fallback:
        track_key = f"{fallback['track']} - {fallback['artist']}".lower()
        if track_key not in already_recommended:
            recommendations[mood_name] = fallback
            already_recommended.add(track_key)
    
    return recommendations

# Ricerca raccomandazioni per tutti i 4 mood in parallelo.
def get_similar_songs_by_mood(csv_with_features: str, lastfm_api_key: str = "481d0ece35e3d695d07d399427f5ef04"):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time
    
    if not lastfm_api_key:
        import os
        lastfm_api_key = os.getenv("LASTFM_API_KEY", "481d0ece35e3d695d07d399427f5ef04")
    
    # Leggi il CSV con i mood
    try:
        df = pd.read_csv(csv_with_features)
        mood_counts = df["label"].value_counts().sort_index().to_dict()
    except Exception as e:
        print(f"[REC] ⚠️ Errore lettura CSV: {e}")
        print(f"[REC] Uso fallback garantito per tutti i mood")
        return FALLBACK_RECOMMENDATIONS.copy()
    
    start_time = time.time()
    already_recommended = set()
    recommendations = {}
    
    #  Ricerca per ogni mood in parallelo
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = {
            executor.submit(fetch_mood_recommendation, mood_id, MOOD_LABELS[mood_id], df, lastfm_api_key, already_recommended): mood_id
            for mood_id in range(4)
        }
        
        # Raccogli risultati
        for future in as_completed(tasks):
            try:
                result = future.result(timeout=10)
                if result:
                    recommendations.update(result)
            except Exception as e:
                print(f"[REC] Errore thread: {e}")
    
    elapsed = time.time() - start_time
    
    # Aggiunta di mood mancanti con fallback
    for mood_id, mood_name in MOOD_LABELS.items():
        if mood_name not in recommendations:
            recommendations[mood_name] = FALLBACK_RECOMMENDATIONS[mood_name]
    
    return recommendations
