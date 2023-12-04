import datetime

from django.db import models

from .tracks import TrackModel


class HistoryModel(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    track = models.ForeignKey(TrackModel, on_delete=models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = "history"
        ordering = ["-timestamp"]

    @staticmethod
    def from_spotify(history):
        history_model = HistoryModel()
        history_model.timestamp = datetime.datetime.fromtimestamp(history["timestamp"] / 1000.0, tz=datetime.UTC)
        history_model.track = TrackModel.from_spotify(history["item"]["id"])
        # get most recent entry in history
        try:
            most_recent = HistoryModel.objects.all()[0]
            # if the most recent track is the same, check duration
            if most_recent.track.track_id == history_model.track.track_id:
                # if the duration is the same, don't save
                if (history_model.timestamp - most_recent.timestamp) < datetime.timedelta(
                    milliseconds=history_model.track.track_duration
                ):
                    return most_recent
        except IndexError:
            pass
        history_model.save()
        return history_model
