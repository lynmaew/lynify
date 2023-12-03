from spotipy import Spotify

from lynify.models.artists import Artist, ArtistTable
from lynify.models.database import Database
from lynify.models.tokens import AccessToken
from lynify.utils.utils import singleton


@singleton
class TrackTable:
    """
    A class used to interface to a sql table of tracks"""

    def __init__(self) -> None:
        self.columns = [
            "track_id text",
            "track_name text",
            "track_artist text",
            "track_album text",
            "track_duration integer",
            "track_popularity integer",
            "track_release_date text",
            "track_explicit boolean",
            "artist_genres text",
            "artist_ids text",
        ]
        self.database = Database()
        self.table_name = "tracks"
        if not self.database.table_exists(self.table_name):
            self.database.create_table(self.table_name, self.columns)

    def table_exists(self):
        return self.database.table_exists(self.table_name)

    def create_table(self):
        self.database.create_table(self.table_name, self.columns)

    def has_track(self, track_id):
        result = self.database.get_entry(self.table_name, ["track_id"], [track_id])
        return len(result) > 0

    def get_track(self, track_id):
        result = self.database.get_entry(self.table_name, ["track_id"], [track_id])
        # try to get the track from the Spotify API if it doesn't exist in the table
        if len(result) == 0:
            track = TrackEntry.from_id(track_id)
            if track is None:
                return None
            self.add_track(track)
            result = self.database.get_entry(self.table_name, ["track_id"], [track_id])
            if len(result) == 0:
                return None
        return TrackEntry.from_sql_result(result[0])

    def add_track(self, response: dict):
        token = AccessToken().get_token()
        if token is None:
            return
        track = TrackEntry.from_response(response, token)
        # check if the track already exists in the table
        if self.has_track(track.track_id):
            return
        # add the artists to the artist table if they don't exist
        artist_table = ArtistTable()
        for artist in track.track_artists:
            artist_table.add_artist(artist)
        values = [
            track.track_id,
            track.track_name,
            track.track_artist,
            track.track_album,
            track.track_duration,
            track.track_popularity,
            track.track_release_date,
            track.track_explicit,
            str(track.artist_genres),
            str(track.artist_ids),
        ]
        self.database.add_entry(self.table_name, self.columns, values)

    def get_all(self):
        return self.database.get_all(self.table_name, "track_popularity")

    def get_all_limit(self, limit: int):
        return self.database.get_all_limit(self.table_name, limit, "track_popularity")

    def get_all_limit_offset(self, limit: int, offset: int):
        return self.database.get_all_limit_offset(self.table_name, limit, offset, "track_popularity")

    def get_track_count(self):
        query = "SELECT COUNT(*) FROM " + self.table_name
        conn = self.database.connect()
        c = conn.cursor()
        c.execute(query)
        result = c.fetchall()
        conn.close()
        return int(result[0][0])


class TrackEntry:
    """
    A class used to represent a played track"""

    def __init__(self) -> None:
        self.track_id = ""
        self.track_name = ""
        self.track_artists = []
        self.track_artist = ""
        self.track_album = ""
        self.track_duration = 0
        self.track_popularity = 0
        self.track_release_date = ""
        self.track_explicit = False
        self.artist_genres = []
        self.artist_ids = []

    @staticmethod
    def from_response(response: dict, access_token: str) -> "TrackEntry":
        """
        Creates a Track object from a Spotify API response
        :param response: Spotify API response
        :return: Track object
        """
        track = TrackEntry()
        item = response["item"]
        track.track_id = item["id"]
        track.track_name = item["name"]
        track.artist_ids = [artist["id"] for artist in item["artists"]]
        track.track_artists = [Artist.from_id(artist_id, access_token) for artist_id in track.artist_ids]
        track.track_artist = item["artists"][0]["name"]
        track.track_album = item["album"]["name"]
        track.track_duration = item["duration_ms"]
        track.track_popularity = item["popularity"]
        track.track_release_date = item["album"]["release_date"]
        track.track_explicit = item["explicit"]
        track.artist_genres = set()
        for artist in track.track_artists:
            track.artist_genres = track.artist_genres.union(set(artist.artist_genres))
        return track

    @staticmethod
    def from_sql_result(result: tuple) -> "TrackEntry":
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
        return track

    @staticmethod
    def from_id(track_id: str) -> "TrackEntry":
        """
        Creates a Track object from a Spotify track ID
        :param track_id: Spotify track ID
        :param access_token: Spotify access token
        :return: Track object
        """
        access_token = AccessToken().get_token()
        if access_token is None:
            return None
        track_response = Spotify(access_token).track(track_id)
        if track_response is None:
            return None
        return TrackEntry.from_response(track_response, access_token)

    def __str__(self):
        ret = self.track_name + " by " + self.track_artist + " from the album " + self.track_album
        ret += "\nDuration: " + str(self.track_duration) + "ms"
        ret += "\nGenres: " + str(self.artist_genres)
        ret += "\nArtists: " + ", ".join([artist.artist_name for artist in self.track_artists])
        return ret

    def __eq__(self, other):
        return self.track_id == other.track_id
