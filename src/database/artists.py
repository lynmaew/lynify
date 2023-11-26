import requests

from src.config import SPOTIFY_API_URL
from src.database.database import Database
from src.database.tokens import AccessToken
from src.utils import singleton


@singleton
class ArtistTable:
    """
    A class used to interface to a sql table of artists"""

    def __init__(self) -> None:
        self.database = Database()
        self.table_name = "artists"
        self.columns = [
            "artist_id text",
            "artist_name text",
            "artist_genres text",
            "artist_popularity integer",
            "artist_followers integer",
        ]
        if not self.database.table_exists(self.table_name):
            self.database.create_table(self.table_name, self.columns)

    def table_exists(self):
        return self.database.table_exists(self.table_name)

    def create_table(self):
        self.database.create_table(self.table_name, self.columns)

    def has_artist(self, artist_id):
        result = self.database.get_entry(self.table_name, ["artist_id"], [artist_id])
        return len(result) > 0

    def add_artist(self, artist):
        if self.has_artist(artist.artist_id):
            return
        values = [
            artist.artist_id,
            artist.artist_name,
            str(artist.artist_genres),
            artist.artist_popularity,
            artist.artist_followers,
        ]
        self.database.add_entry(self.table_name, self.columns, values)

    def get_artist(self, artist_id):
        result = self.database.get_entry(self.table_name, ["artist_id"], [artist_id])
        # get the artist from the Spotify API if it doesn't exist in the table
        if len(result) == 0:
            token_success, token_result = AccessToken().get_token()
            if not token_success:
                print("Failed to get token")
                return None
            self.access_token = token_result
            artist = Artist.from_id(artist_id, access_token=self.access_token)
            if artist is None:
                return None
            self.add_artist(artist)
            result = self.database.get_entry(self.table_name, ["artist_id"], [artist_id])
            if len(result) == 0:
                return None
        return result

    def get_all(self):
        return self.database.get_all(self.table_name, "artist_followers")

    def get_all_limit(self, limit: int):
        return self.database.get_all_limit(self.table_name, limit, "artist_followers")

    def get_all_limit_offset(self, limit: int, offset: int):
        return self.database.get_all_limit_offset(self.table_name, limit, offset, "artist_followers")

    def get_artist_count(self):
        query = "SELECT COUNT(*) FROM " + self.table_name
        conn = self.database.connect()
        c = conn.cursor()
        c.execute(query)
        result = c.fetchall()
        conn.close()
        return int(result[0][0])


class Artist:
    """
    A class used to represent a Spotify artist"""

    def __init__(self) -> None:
        self.artist_id = ""
        self.artist_name = ""
        self.artist_genres = []
        self.artist_popularity = 0
        self.artist_followers = 0

    @staticmethod
    def from_response(response: dict) -> "Artist":
        """
        Creates an Artist object from a Spotify API response
        :param response: Spotify API response
        :return: Artist object
        """
        artist = Artist()
        artist.artist_id = response["id"]
        artist.artist_name = response["name"]
        artist.artist_genres = response["genres"]
        artist.artist_popularity = response["popularity"]
        artist.artist_followers = response["followers"]["total"]
        return artist

    @staticmethod
    def from_id(artist_id: str, access_token: str) -> "Artist":
        """
        Creates an Artist object from a Spotify artist ID
        :param artist_id: Spotify artist ID
        :param access_token: Spotify access token
        :return: Artist object
        """
        response = requests.get(
            SPOTIFY_API_URL + "artists/" + artist_id, headers={"Authorization": "Bearer " + access_token}
        )
        return Artist.from_response(response.json())

    @staticmethod
    def from_sql(artist_id: str) -> "Artist":
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
