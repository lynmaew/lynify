from django.db import models
from spotipy import Spotify

from lynify.models.tokens import AccessToken

from .artists import ArtistModel


class TrackModel(models.Model):
    track_id = models.TextField(primary_key=True)
    track_name = models.TextField(blank=True, null=True)
    track_album = models.TextField(blank=True, null=True)
    track_duration = models.IntegerField(blank=True, null=True)
    track_popularity = models.IntegerField(blank=True, null=True)
    track_release_date = models.DateField(blank=True, null=True)
    track_explicit = models.BooleanField(blank=True, null=True)
    track_artists = models.ManyToManyField(ArtistModel)

    class Meta:
        managed = True
        db_table = "tracks"
        ordering = ["-track_popularity"]

    @staticmethod
    def from_spotify(track_id):
        # if the track is already in the database, return it
        try:
            track = TrackModel.objects.get(track_id=track_id)
            return track
        except TrackModel.DoesNotExist:
            pass
        access_token = AccessToken.get_token()
        if access_token is None:
            return None
        track_response = Spotify(auth=access_token.access_token).track(track_id)
        if track_response is None:
            return None
        track = TrackModel()
        track.track_id = track_response["id"]
        track.track_name = track_response["name"]
        track.track_album = track_response["album"]["name"]
        track.track_duration = track_response["duration_ms"]
        track.track_popularity = track_response["popularity"]
        track.track_release_date = track_response["album"]["release_date"]
        track.track_explicit = track_response["explicit"]
        track.save()
        # get artists from track
        artists = []
        for artist in track_response["artists"]:
            artist_model = ArtistModel.from_spotify(artist["id"])
            artists.append(artist_model)
        track.track_artists.set(artists)
        track.save()
        return track
