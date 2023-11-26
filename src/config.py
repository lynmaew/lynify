import os

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_CURRENTLY_PLAYING = "https://api.spotify.com/v1/me/player/currently-playing"
SPOTIFY_API_URL = "https://api.spotify.com/v1/"
DATABASE_NAME = "lynify"

DATABASE_URL = os.environ.get("DATABASE_URL")
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_USER_ID = os.environ.get("SPOTIFY_USER_ID")
SPOTIPY_REDIRECT_URI = os.environ.get("SPOTIPY_REDIRECT_URI")

# POSTGRES_USER = os.environ.get('POSTGRES_USER')
# POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
# POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
# POSTGRES_PORT = os.environ.get('POSTGRES_PORT')
