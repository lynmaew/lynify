import time
from datetime import datetime
from typing import Tuple

from spotipy.oauth2 import SpotifyOAuth

from src.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_USER_ID, SPOTIPY_REDIRECT_URI
from src.database.tokens import AccessToken


def nav_bar():
    html = '<div class="w3-bar w3-black">'
    html += '<a href="/" class="w3-bar-item w3-button">Currently Playing</a>'
    html += '<a href="/history" class="w3-bar-item w3-button">History</a>'
    html += '<a href="/artists" class="w3-bar-item w3-button">Artists</a>'
    html += '<a href="/tracks" class="w3-bar-item w3-button">Tracks</a>'
    html += "</div>"
    return html


def header():
    html = '<head><link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css"></head>'
    html += "<style>table, th, td {border: 1px solid black;}</style>"
    html += "<style>table {border-collapse: collapse;}</style>"
    html += "<style>th, td {padding: 5px;}</style>"
    html += "<style>th {text-align: left;}</style>"
    html += "<style>tr:nth-child(even) {background-color: #f2f2f2;}</style>"
    html += nav_bar()
    return html


def display_currently_playing():
    currently_playing = AccessToken().get_currently_playing()
    html = "<h1>Currently Playing</h1>"
    if currently_playing is None or not currently_playing["is_playing"]:
        return html + "No currently playing track"
    else:
        timestamp = currently_playing["timestamp"]
        artist = currently_playing["item"]["artists"][0]["name"]
        song = currently_playing["item"]["name"]
        album = currently_playing["item"]["album"]["name"]
        dt = datetime.fromtimestamp(timestamp / 1000.0)
        date = dt.strftime("%Y-%m-%d")
        # create a table of the track information
        html += "<table>"
        html += "<tr><th>Track</th><th>Artist</th><th>Album</th><th>Date</th><th>Time</th></tr>"
        html += "<tr>"
        cols = [song, artist, album, date, dt.strftime("%H:%M:%S")]
        for col in cols:
            html += "<td>" + col + "</td>"
        html += "</tr>"
        html += "</table>"
        return html


def SpotifyLogin(request_url) -> Tuple[bool, str]:
    """
    Checks if the user is logged into Spotify and returns an html login button if they are not
    """
    oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-currently-playing",
    )
    if AccessToken().has_token(SPOTIFY_USER_ID):
        token = AccessToken().get_token(SPOTIFY_USER_ID)
        return True, token
    token = oauth.get_cached_token()
    if token:
        AccessToken().add_token(
            SPOTIFY_USER_ID,
            token["access_token"],
            token["refresh_token"],
            int(time.time() * 1000) + token["expires_in"] * 1000,
        )
        return True, token["access_token"]
    else:
        code = oauth.parse_response_code(request_url)
        if code != request_url:
            token = oauth.get_access_token(code)
            if token:
                AccessToken().add_token(
                    SPOTIFY_USER_ID,
                    token["access_token"],
                    token["refresh_token"],
                    int(time.time() * 1000) + token["expires_in"] * 1000,
                )
                return True, token["access_token"]
        else:
            auth_url = oauth.get_authorize_url()
            htmlLoginButton = "<a href='" + auth_url + "'>Login to Spotify</a>"
            return False, htmlLoginButton
