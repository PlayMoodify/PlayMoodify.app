import csv
from spotify_scraper import SpotifyClient


def spotify_playlist_to_csv(playlist_url, output_csv_path):
    client = SpotifyClient()
    playlist = client.get_playlist_info(playlist_url)

    tracks = []

    for track in playlist.get("tracks", []):
        # Skip elementi non musicali o incompleti
        if not track.get("artists") or not track.get("name"):
            continue

        title = track.get("name", "").strip()
        artist = ", ".join([a.get("name", "").strip() for a in track.get("artists", [])])

        tracks.append({
            "title": title,
            "artist": artist
        })

    # Scrittura CSV
    fieldnames = ["title", "artist"]

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tracks)

    print(f"✅ Salvate {len(tracks)} canzoni in {output_csv_path}")
    return output_csv_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python linktocsvconverter.py <playlist_url> <output_csv>")
        sys.exit(1)
    
    playlist_url = sys.argv[1]
    output_csv = sys.argv[2]
    
    try:
        spotify_playlist_to_csv(playlist_url, output_csv)
    except Exception as e:
        print(f"Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

