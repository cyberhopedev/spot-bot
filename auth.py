from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id     = os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri  = os.getenv("SPOTIFY_REDIRECT_URI"),
    scope         = "playlist-modify-public playlist-modify-private",
))

# Test that auth worked by printing your Spotify username
print("Authenticated as:", sp.current_user()["display_name"])