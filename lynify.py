import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from bottle import route, run, request
from datetime import datetime
import sqlite3
import threading
import time
import json

SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_CURRENTLY_PLAYING = 'https://api.spotify.com/v1/me/player/currently-playing'
SPOTIFY_API_URL = 'https://api.spotify.com/v1/'


# config from json file
with open('config.json') as f:
    config = json.load(f)
SPOTIFY_CLIENT_ID = config['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = config['SPOTIFY_CLIENT_SECRET']
SPOTIFY_USER_ID = config['SPOTIFY_USER_ID']
SPOTIPY_REDIRECT_URI = config['SPOTIPY_REDIRECT_URI']


class ArtistTable:
    """
    A class used to interface to a sql table of artists"""
    def __init__(self) -> None:
        token_success, token_result = check_for_token()
        self.access_token = token_result
        if not self.table_exists():
            self.create_table()
    
    def table_exists(self):
        conn = sqlite3.connect('lynify.db')
        c = conn.cursor()
        c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='artists'")
        if c.fetchone()[0] == 1:
            conn.close()
            return True
        else:
            conn.close()
            return False

    def create_table(self):
        conn = sqlite3.connect('lynify.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS artists
                     (artist_id text, artist_name text, artist_genres text, artist_popularity integer, artist_followers integer)''')
        conn.commit()
        conn.close()

    def has_artist(self, artist_id):
        conn = sqlite3.connect('lynify.db')
        c = conn.cursor()
        c.execute("SELECT count(*) FROM artists WHERE artist_id = '" + artist_id + "'")
        if c.fetchone()[0] == 1:
            conn.close()
            return True
        else:
            conn.close()
            return False

    def add_artist(self, artist):
        if self.has_artist(artist.artist_id):
            return
        conn = sqlite3.connect('lynify.db')
        c = conn.cursor()
        c.execute("INSERT INTO artists VALUES (?, ?, ?, ?, ?)", (artist.artist_id, artist.artist_name, str(artist.artist_genres), artist.artist_popularity, artist.artist_followers))
        conn.commit()
        conn.close()

    def get_artist(self, artist_id):
        conn = sqlite3.connect('lynify.db')
        c = conn.cursor()
        c.execute("SELECT * FROM artists WHERE artist_id = '" + artist_id + "'")
        result = c.fetchall()
        # get the artist from the Spotify API if it doesn't exist in the table
        if len(result) == 0:
            token_success, token_result = check_for_token()
            self.access_token = token_result
            artist = Artist.from_id(artist_id, access_token=self.access_token)
            self.add_artist(artist)
            c.execute("SELECT * FROM artists WHERE artist_id = '" + artist_id + "'")
            result = c.fetchall()
        conn.close()
        return result


class Artist:
    """
    A class used to represent a Spotify artist"""
    def __init__(self) -> None:
        self.artist_id = ''
        self.artist_name = ''
        self.artist_genres = []
        self.artist_popularity = 0
        self.artist_followers = 0
    
    @staticmethod
    def from_response(response: dict) -> 'Artist':
        """
        Creates an Artist object from a Spotify API response
        :param response: Spotify API response
        :return: Artist object
        """
        artist = Artist()
        artist.artist_id = response['id']
        artist.artist_name = response['name']
        artist.artist_genres = response['genres']
        artist.artist_popularity = response['popularity']
        artist.artist_followers = response['followers']['total']
        return artist

    @staticmethod
    def from_id(artist_id: str, access_token: str) -> 'Artist':
        """
        Creates an Artist object from a Spotify artist ID
        :param artist_id: Spotify artist ID
        :param access_token: Spotify access token
        :return: Artist object
        """
        response = requests.get(SPOTIFY_API_URL + 'artists/' + artist_id, headers={'Authorization': 'Bearer ' + access_token})
        return Artist.from_response(response.json())

    @staticmethod
    def from_sql(artist_id: str) -> 'Artist':
        """
        Creates an Artist object from a Spotify artist ID
        :param artist_id: Spotify artist ID
        :return: Artist object
        """
        artist = Artist()
        artist_table = ArtistTable()
        result = artist_table.get_artist(artist_id)
        artist.artist_id = result[0][0]
        artist.artist_name = result[0][1]
        artist.artist_genres = result[0][2]
        artist.artist_popularity = result[0][3]
        artist.artist_followers = result[0][4]
        return artist

    def __str__(self):
        ret = self.artist_name
        ret += "\nGenres: " + str(self.artist_genres)
        ret += "\nPopularity: " + str(self.artist_popularity)
        ret += "\nFollowers: " + str(self.artist_followers)
        return ret

class TrackTable:
    """
    A class used to interface to a sql table of tracks"""
    def __init__(self, artist_table: 'ArtistTable') -> None:
        self.artist_table = artist_table
        if not self.table_exists():
            self.create_table()

    def table_exists(self):
        conn = sqlite3.connect('lynify.db')
        c = conn.cursor()
        c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='tracks'")
        if c.fetchone()[0] == 1:
            conn.close()
            return True
        else:
            conn.close()
            return False

    def create_table(self):
        conn = sqlite3.connect('lynify.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS tracks
                     (track_id text, track_name text, track_artist text, track_album text, track_duration integer, track_popularity integer, track_release_date text, track_explicit integer, artist_genres text, artist_ids text, timestamp text, date text)''')
        conn.commit()
        conn.close()

    def get_most_recent(self):
        conn = sqlite3.connect('lynify.db')
        c = conn.cursor()
        c.execute("SELECT * FROM tracks ORDER BY timestamp DESC LIMIT 1")
        result = c.fetchall()
        conn.close()
        return result

    def add_track(self, track):
        # check if the track already exists in the table
        most_recent = self.get_most_recent()
        if len(most_recent) > 0 and TrackEntry.from_sql_result(most_recent[0]) == track:
            return
        # add the artists to the artist table if they don't exist
        for artist in track.track_artists:
            self.artist_table.add_artist(artist)
        conn = sqlite3.connect('lynify.db')
        c = conn.cursor()
        c.execute("INSERT INTO tracks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (track.track_id, track.track_name, track.track_artist, track.track_album, track.track_duration, track.track_popularity, track.track_release_date, track.track_explicit, str(track.artist_genres), str(track.artist_ids), str(track.timestamp), str(track.date)))
        conn.commit()
        conn.close()


class TrackEntry:
    """
    A class used to represent a played track"""
    def __init__(self) -> None:
        self.track_id = ''
        self.track_name = ''
        self.track_artists = []
        self.track_artist = ''
        self.track_album = ''
        self.track_duration = 0
        self.track_popularity = 0
        self.track_release_date = ''
        self.track_explicit = False
        self.artist_genres = []
        self.artist_ids = []
        self.timestamp = 0
        self.date = ''

    @staticmethod
    def from_response(response: dict, access_token: str) -> 'Track':
        """
        Creates a Track object from a Spotify API response
        :param response: Spotify API response
        :return: Track object
        """
        track = TrackEntry()
        item = response['item']
        track.track_id = item['id']
        track.track_name = item['name']
        track.artist_ids = [artist['id'] for artist in item['artists']]
        track.track_artists = [Artist.from_id(artist_id, access_token) for artist_id in track.artist_ids]
        track.track_artist = item['artists'][0]['name']
        track.track_album = item['album']['name']
        track.track_duration = item['duration_ms']
        track.track_popularity = item['popularity']
        track.track_release_date = item['album']['release_date']
        track.track_explicit = item['explicit']
        track.artist_genres = set()
        for artist in track.track_artists:
            track.artist_genres = track.artist_genres.union(set(artist.artist_genres))
        track.timestamp = response['timestamp']
        track.date = datetime.fromtimestamp(int(track.timestamp)/1000.0).strftime('%Y-%m-%d')
        return track

    @staticmethod
    def from_sql_result(result: tuple) -> 'Track':
        """
        Creates a Track object from a SQL result
        :param result: SQL result
        :return: Track object
        """
        track = TrackEntry()
        track.track_id = result[0]
        track.track_name = result[1]
        track.track_artist = result[2]
        track.track_album = result[3]
        track.track_duration = result[4]
        track.track_popularity = result[5]
        track.track_release_date = result[6]
        track.track_explicit = result[7]
        track.artist_genres = result[8]
        track.artist_ids = result[9]
        track.timestamp = result[10]
        track.date = datetime.fromtimestamp(int(track.timestamp)/1000.0).strftime('%Y-%m-%d')
        return track

    def __str__(self):
        ret = self.track_name + ' by ' + self.track_artist + ' from the album ' + self.track_album
        ret += "\nDuration: " + str(self.track_duration) + "ms"
        ret += "\nGenres: " + str(self.artist_genres)
        ret += "\nArtists: " + ", ".join([artist.artist_name for artist in self.track_artists])
        ret += "\nPlayed at: " + datetime.fromtimestamp(int(self.timestamp)/1000.0).strftime('%H:%M:%S') + " on " + self.date
        return ret

    def __eq__(self, other):
        return self.track_id == other.track_id and abs(int(self.timestamp) - int(other.timestamp)) < int(self.track_duration)

def table_exists(table_name):
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='" + table_name + "'")
    if c.fetchone()[0] == 1:
        conn.close()
        return True
    else:
        conn.close()
        return False

def create_playing_history_table():
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS playing_history
                 (timestamp text, artist text, song text, album text, date text)''')
    conn.commit()
    conn.close()

def insert_playing_history(timestamp, artist, song, album, date):
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute("INSERT INTO playing_history VALUES ('" + timestamp + "', '" + artist + "', '" + song + "', '" + album + "', '" + date + "')")
    conn.commit()
    conn.close()

def get_playing_history():
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute("SELECT * FROM playing_history")
    result = c.fetchall()
    conn.close()
    return result

def get_playing_history_by_date(date):
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute("SELECT * FROM playing_history WHERE date = '" + date + "'")
    result = c.fetchall()
    conn.close()
    return result

def get_playing_history_by_song(song):
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute("SELECT * FROM playing_history WHERE song = '" + song + "'")
    result = c.fetchall()
    conn.close()
    return result

def get_playing_history_by_artist(artist):
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute("SELECT * FROM playing_history WHERE artist = '" + artist + "'")
    result = c.fetchall()
    conn.close()
    return result

def get_playing_history_by_album(album):
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute("SELECT * FROM playing_history WHERE album = '" + album + "'")
    result = c.fetchall()
    conn.close()
    return result

def get_playing_history_by_date_range(start_date, end_date):
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute("SELECT * FROM playing_history WHERE date >= '" + start_date + "' AND date <= '" + end_date + "'")
    result = c.fetchall()
    conn.close()
    return result

def get_most_recent():
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    c.execute("SELECT * FROM playing_history ORDER BY timestamp DESC LIMIT 1")
    result = c.fetchall()
    conn.close()
    return result

def check_if_duplicate(timestamp, artist, song, album, date):
    # check if there are any entries in the table
    if len(get_playing_history()) == 0:
        return False
    conn = sqlite3.connect('lynify.db')
    c = conn.cursor()
    # get the most recent entry
    c.execute("SELECT * FROM playing_history ORDER BY timestamp DESC LIMIT 1")
    result = c.fetchall()
    conn.close()
    # check if artist, album, song are the same
    if result[0][1] == artist and result[0][2] == song and result[0][3] == album:
        # check if timestamp is within 6 minutes
        if int(timestamp) - int(result[0][0]) < 360000:
            print('Duplicate entry detected')
            return True
    return False

def request_access_token(client_id, client_secret):
    payload = {'grant_type': 'client_credentials'}
    response = requests.post(SPOTIFY_TOKEN_URL, data=payload, auth=(client_id, client_secret))
    return response.json()['access_token']

def get_currently_playing(access_token):
    response = Spotify(access_token).current_user_playing_track()
    return response

def check_for_token():
    oauth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope='user-read-currently-playing')
    token = oauth.get_cached_token()
    if token:
        return True, token['access_token']
    else:
        url = request.url
        code = oauth.parse_response_code(url)
        if code != url:
            token = oauth.get_access_token(code)
            if token:
                return True, token['access_token']
        else:
            auth_url = oauth.get_authorize_url()
            htmlLoginButton = "<a href='" + auth_url + "'>Login to Spotify</a>"
            return False, htmlLoginButton

def display_currently_playing(token):
    currently_playing = get_currently_playing(token)
    if not currently_playing['is_playing']:
        return 'Not playing anything'
    else:
        timestamp = currently_playing['timestamp']
        artist = currently_playing['item']['artists'][0]['name']
        song = currently_playing['item']['name']
        album = currently_playing['item']['album']['name']
        dt = datetime.fromtimestamp(timestamp/1000.0)
        date = dt.strftime('%Y-%m-%d')

        return 'Currently playing: ' + song + ' by ' + artist + ' from the album ' + album + ' at ' + dt.strftime('%H:%M:%S') + ' on ' + date

def poll_for_playing_history(token, ttable, atable):
    currently_playing = get_currently_playing(token)
    if currently_playing['is_playing']:
        track = TrackEntry.from_response(currently_playing, token)
        ttable.add_track(track)
        timestamp = currently_playing['timestamp']
        artist = currently_playing['item']['artists'][0]['name']
        song = currently_playing['item']['name']
        album = currently_playing['item']['album']['name']
        dt = datetime.fromtimestamp(timestamp/1000.0)
        date = dt.strftime('%Y-%m-%d')
        if not check_if_duplicate(str(timestamp), artist, song, album, date):
            insert_playing_history(str(timestamp), artist, song, album, date)

def get_playing_history_html():
    result = get_playing_history()
    html = '<table><tr><th>Timestamp</th><th>Artist</th><th>Song</th><th>Album</th><th>Date</th></tr>'
    for row in result:
        html += '<tr>'
        for col in row:
            html += '<td>' + col + '</td>'
        html += '</tr>'
    html += '</table>'
    return html

def polling_loop():
    atable = ArtistTable()
    ttable = TrackTable(atable)
    while True:
        try:
            token_success, token_result = check_for_token()
            if not token_success:
                print("Failed to get token")
                time.sleep(60)
                continue
            poll_for_playing_history(token_result, ttable, atable)
            print('Polled for playing history')
        except Exception as e:
            print(e)
        time.sleep(60)

@route('/')
def index():
    token_success, token_result = check_for_token()
    if not token_success:
        return token_result

    return display_currently_playing(token_result)


if not table_exists('playing_history'):
    create_playing_history_table()
threading.Thread(target=polling_loop).start()
run(host='localhost', port=8080)