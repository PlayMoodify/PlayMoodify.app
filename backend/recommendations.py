import requests
import pandas as pd
from typing import Optional, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ========================================
# DEEZER API - Ricerca immagini tracce
# ========================================

def get_track_image_from_deezer(track_name: str, artist_name: str) -> Optional[str]:
    try:
        results = requests.get(
            "https://api.deezer.com/search",
            params={"q": f"{track_name} {artist_name}", "limit": 10},
            timeout=3
        ).json().get("data", [])
        
        track, artist = track_name.lower().strip(), artist_name.lower().strip()
        
        for result in results:
            if (track in result.get("title", "").lower().strip() or 
                result.get("title", "").lower().strip() in track) and \
               (artist in result.get("artist", {}).get("name", "").lower().strip() or 
                result.get("artist", {}).get("name", "").lower().strip() in artist):
                return _extract_cover_url(result.get("album", {}))
        
        return _extract_cover_url(results[0].get("album", {})) if results else None
                    
    except Exception:
        return None

def _extract_cover_url(album: dict) -> Optional[str]:
    return album.get("cover_big") or album.get("cover_medium") or album.get("cover")

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
        "image": "https://e-cdns-images.dzcdn.net/images/cover/2582df73d9c5436414b9eb8880e5be54/500x500-000000-80-0-0.jpg",
        "strategy": "fallback"
    },
    "happy": {
        "track": "Walking on Sunshine",
        "artist": "Katrina & The Waves",
        "image": "https://e-cdns-images.dzcdn.net/images/cover/4a3d98d6e5c2f5d5c5c5c5c5c5c5c5c5/500x500-000000-80-0-0.jpg",
        "strategy": "fallback"
    },
    "energetic": {
        "track": "Shut Up and Dance",
        "artist": "Walk the Moon",
        "image": "https://e-cdns-images.dzcdn.net/images/cover/3f0f4d7e1b9c5e5d5c5c5c5c5c5c5c5c/500x500-000000-80-0-0.jpg",
        "strategy": "fallback"
    },
    "calm": {
        "track": "Weightless",
        "artist": "Marconi Union",
        "image": "https://e-cdns-images.dzcdn.net/images/cover/5e8c9d1f0a7b5e5d5c5c5c5c5c5c5c5c/500x500-000000-80-0-0.jpg",
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
                    # Estrai immagini da ogni traccia
                    for track in tracks:
                        image_url = None
                        if "image" in track:
                            images = track["image"]
                            if isinstance(images, list):
                                for img in reversed(images):
                                    if img.get("size") == "extralarge" or img.get("size") == "large":
                                        image_url = img.get("#text", "")
                                        if image_url:
                                            break
                        track["image_url"] = image_url
                    return tracks
                elif tracks:
                    image_url = None
                    if "image" in tracks:
                        images = tracks["image"]
                        if isinstance(images, list):
                            for img in reversed(images):
                                if img.get("size") == "extralarge" or img.get("size") == "large":
                                    image_url = img.get("#text", "")
                                    if image_url:
                                        break
                    tracks["image_url"] = image_url
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
                    track = similar_tracks[0]
                    # Estrai l'immagine più grande disponibile
                    image_url = None
                    if "image" in track:
                        images = track["image"]
                        if isinstance(images, list):
                            for img in reversed(images):
                                if img.get("size") == "extralarge" or img.get("size") == "large":
                                    image_url = img.get("#text", "")
                                    if image_url:
                                        break
                    track["image_url"] = image_url
                    return track
                elif similar_tracks:
                    similar_tracks["image_url"] = None
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
    
    # Se mood è nella playlist, ricerchiamo simile
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
            
            image_url = get_track_image_from_deezer(track_name, artist_name)
            
            track_key = f"{track_name} - {artist_name}".lower()
            
            if track_key and track_key not in already_recommended:
                recommendations[mood_name] = {
                    "track": track_name,
                    "artist": artist_name,
                    "image": image_url,
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
            # Cerca immagine su Deezer
            image_url = get_track_image_from_deezer(track_name, artist_name)
            
            recommendations[mood_name] = {
                "track": track_name,
                "artist": artist_name,
                "image": image_url,
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
    
    if not lastfm_api_key:
        import os
        lastfm_api_key = os.getenv("LASTFM_API_KEY", "481d0ece35e3d695d07d399427f5ef04")
    
    # Leggi il CSV con i mood
    try:
        df = pd.read_csv(csv_with_features)
        mood_counts = df["label"].value_counts().sort_index().to_dict()
    except Exception as e:
        return FALLBACK_RECOMMENDATIONS.copy()
    
    already_recommended = set()
    recommendations = {}
    
    #  Ricerca per ogni mood in parallelo
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = {
            executor.submit(fetch_mood_recommendation, mood_id, MOOD_LABELS[mood_id], df, lastfm_api_key, already_recommended): mood_id
            for mood_id in range(4)
        }
        
        # Raccogliamo risultati
        for future in as_completed(tasks):
            try:
                result = future.result(timeout=10)
                if result:
                    recommendations.update(result)
            except Exception as e:
                print(f"[REC] Errore thread: {e}")
    
    # Aggiunta di mood mancanti con fallback
    for mood_id, mood_name in MOOD_LABELS.items():
        if mood_name not in recommendations:
            recommendations[mood_name] = FALLBACK_RECOMMENDATIONS[mood_name]
    
    return recommendations
