import time
from typing import Optional, Union

import spotipy
from django.db import models
from spotipy.oauth2 import SpotifyOAuth

from lynify.settings import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_USER_ID, SPOTIPY_REDIRECT_URI


class TokenException(Exception):
    """Raised when there is a problem with the access token"""

    pass


class AccessToken(models.Model):
    user_id = models.TextField(primary_key=True)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    expires_at = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tokens"

    def __str__(self):
        return f"Token for {self.user_id} expires at {self.expires_at}"

    def get_currently_playing(self) -> Union[dict, TokenException]:
        try:
            spotify = spotipy.Spotify(auth=self.access_token)
            response = spotify.current_user_playing_track()
        except spotipy.client.SpotifyException as e:
            print("SpotifyException", e)
            return e
        return response

    @staticmethod
    def from_spotify(user_id, access_token, refresh_token, expires_at) -> "AccessToken":
        token = AccessToken()
        token.user_id = user_id
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.expires_at = expires_at
        token.save()
        return token

    @staticmethod
    def get_token(user_id: Optional[str] = None) -> Union[str, None]:
        """
        Get the access token for a user.
        If the token has expired, refresh it.
        If the token has not been set, return None.
        """
        if user_id is None:
            user_id = SPOTIFY_USER_ID
        try:
            token = AccessToken.objects.get(user_id=user_id)
        except AccessToken.DoesNotExist:
            # try to get a cached token
            oauth = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIPY_REDIRECT_URI,
                scope="user-read-currently-playing",
            )
            token = oauth.get_cached_token()
            if token:
                token = AccessToken.from_spotify(
                    user_id,
                    token["access_token"],
                    token["refresh_token"],
                    int(time.time() * 1000) + token["expires_in"] * 1000,
                )
            else:
                return None

        if token.expires_at < int(time.time() * 1000):
            # refresh the token
            oauth = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIPY_REDIRECT_URI,
                scope="user-read-currently-playing",
            )
            refreshed_token = oauth.refresh_access_token(token.refresh_token)
            if refreshed_token is None:
                return None
            # update the token
            expires_at = int(time.time() * 1000) + refreshed_token["expires_in"] * 1000
            AccessToken.objects.update(
                access_token=refreshed_token["access_token"],
                refresh_token=refreshed_token["refresh_token"],
                expires_at=expires_at,
            )
            token = AccessToken.objects.get(user_id=user_id)
            return token

        return token
