import time
from datetime import datetime
from typing import Tuple

from spotipy.oauth2 import SpotifyOAuth

from lynify.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_USER_ID, SPOTIPY_REDIRECT_URI
from lynify.models.tokens import AccessToken


def nav_bar() -> str:
    html = '<div class="w3-bar w3-black">'
    html += '<a href="/" class="w3-bar-item w3-button">Currently Playing</a>'
    html += '<a href="/history" class="w3-bar-item w3-button">History</a>'
    html += '<a href="/artists" class="w3-bar-item w3-button">Artists</a>'
    html += '<a href="/tracks" class="w3-bar-item w3-button">Tracks</a>'
    html += "</div>"
    return html


def header() -> str:
    html = "<head>"
    html += '<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">'
    html += '<link rel="shortcut icon" href="images/favicon.ico" type="image/svg">'
    html += "</head>"
    html += "<style>table, th, td {border: 1px solid black;}</style>"
    html += "<style>table {border-collapse: collapse;}</style>"
    html += "<style>th, td {padding: 5px;}</style>"
    html += "<style>th {text-align: left;}</style>"
    html += "<style>tr:nth-child(even) {background-color: #f2f2f2;}</style>"
    html += nav_bar()
    return html


def SpotifyLoginButton() -> str:
    oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-currently-playing",
    )
    auth_url = oauth.get_authorize_url()
    htmlLoginButton = "<a href='" + auth_url + "'>Login to Spotify</a>"
    return htmlLoginButton


def display_currently_playing() -> str:
    """
    Returns a string of html containing the currently playing track
    If there is a spotify api error, returns a login button
    """
    currently_playing = AccessToken().get_currently_playing()
    html = "<h1>Currently Playing</h1>"
    if currently_playing is None:
        return html + "No currently playing track"
    elif isinstance(currently_playing, Exception):
        html += "Issue with token: " + str(currently_playing)
        html += SpotifyLoginButton()
        return html
    elif not currently_playing["is_playing"]:
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
    Returns True and an access token if available
    Returns False and a login button if otherwise
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
        print("parsing response code")
        code = oauth.parse_response_code(request_url)
        print(code)
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
