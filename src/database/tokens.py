import time
from typing import Optional, Union

import spotipy
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

from src.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_USER_ID, SPOTIPY_REDIRECT_URI
from src.database.database import Database
from src.utils import singleton


class TokenException(Exception):
    """Raised when there is a problem with the access token"""

    pass


@singleton
class AccessToken:
    """
    A class to store and retrieve a Spotify access token in a sql table
    """

    def __init__(self) -> None:
        self.database = Database()
        self.table_name = "access_token"
        self.columns = ["user_id text", "access_token text", "refresh_token text", "expires_at bigint"]
        if not self.table_exists():
            self.create_table()

    def table_exists(self):
        return self.database.table_exists(self.table_name)

    def create_table(self):
        self.database.create_table(self.table_name, self.columns)

    def has_token(self, user_id: Optional[str] = None):
        if user_id is None:
            user_id = SPOTIFY_USER_ID
        if not self.table_exists():
            self.create_table()
        result = self.database.get_entry(self.table_name, ["user_id"], [user_id])
        return len(result) > 0

    def get_token(self, user_id: Optional[str] = None) -> Optional[str]:
        if user_id is None:
            user_id = SPOTIFY_USER_ID
        if not self.has_token(user_id):
            return None
        result = self.database.get_entry(self.table_name, ["user_id"], [user_id])
        # check if the token has expired
        if len(result) > 0 and int(result[0][3]) < int(time.time() * 1000):
            # refresh the token
            oauth = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIPY_REDIRECT_URI,
                scope="user-read-currently-playing",
            )
            token = oauth.refresh_access_token(result[0][2])
            # update the token
            expires_at = int(time.time() * 1000) + token["expires_in"] * 1000
            self.database.update_entry(
                self.table_name,
                ["access_token", "refresh_token", "expires_at"],
                [token["access_token"], token["refresh_token"], expires_at],
                ["user_id"],
                [user_id],
            )
            return token["access_token"]
        if len(result) == 0:
            return None
        return result[0][1]

    def add_token(self, user_id, access_token, refresh_token, expires_at):
        if not self.table_exists():
            self.create_table()

        if self.has_token(user_id):
            # update the token
            self.database.update_entry(
                self.table_name,
                ["access_token", "refresh_token", "expires_at"],
                [access_token, refresh_token, expires_at],
                ["user_id"],
                [user_id],
            )
            return
        values = [user_id, access_token, refresh_token, expires_at]
        self.database.add_entry(self.table_name, self.columns, values)

    def get_currently_playing(user_id: Optional[str] = None) -> Union[dict, Exception, None]:
        if user_id is None:
            user_id = SPOTIFY_USER_ID
        access_token = AccessToken().get_token(user_id)
        if access_token is None:
            return TokenException("No access token")
        try:
            response = Spotify(access_token).current_user_playing_track()
        except spotipy.client.SpotifyException as e:
            return e
        return response
