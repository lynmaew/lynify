from django.db import models
from spotipy import Spotify

from lynify.models.tokens import AccessToken


class ArtistModel(models.Model):
    artist_id = models.TextField(primary_key=True)
    artist_name = models.TextField(blank=True, null=True)
    artist_genres = models.TextField(blank=True, null=True)
    artist_popularity = models.IntegerField(blank=True, null=True)
    artist_followers = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "artists"
        ordering = ["-artist_followers"]

    @staticmethod
    def from_spotify(artist_id):
        access_token = AccessToken.get_token()
        if access_token is None:
            return None
        artist_response = Spotify(access_token.access_token).artist(artist_id)
        if artist_response is None:
            return None
        artist = ArtistModel()
        artist.artist_id = artist_response["id"]
        artist.artist_name = artist_response["name"]
        artist.artist_genres = str(artist_response["genres"])
        artist.artist_popularity = artist_response["popularity"]
        artist.artist_followers = artist_response["followers"]["total"]
        artist.save()
        return artist
