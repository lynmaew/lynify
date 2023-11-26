from datetime import datetime

from src.database.database import Database
from src.database.tracks import TrackTable
from src.utils import singleton


@singleton
class HistoryTable:
    """
    A class used to interface to a sql table of playing history
    """

    def __init__(self) -> None:
        self.columns = ["timestamp text", "track_id text", "date text"]
        self.database = Database()
        self.table_name = "playing_history"
        if not self.database.table_exists(self.table_name):
            self.database.create_table(self.table_name, self.columns)
        self.track_table = TrackTable()

    def table_exists(self):
        return self.database.table_exists(self.table_name)

    def create_table(self):
        self.database.create_table(self.table_name, self.columns)

    def add_entry(self, response: dict):
        entry = PlayingHistoryEntry.from_response(response)
        if self.has_entry(entry):
            return
        values = [entry.timestamp, entry.track_id, entry.date]
        self.database.add_entry(self.table_name, self.columns, values)

    def has_entry(self, entry: "PlayingHistoryEntry"):
        recent_entry = self.get_most_recent()
        if len(recent_entry) == 0:
            return False
        return len(recent_entry) > 0 and PlayingHistoryEntry.from_sql_result(recent_entry[0]) == entry

    def get_most_recent(self):
        return self.database.get_most_recent(self.table_name)

    def get_all(self):
        return self.database.get_all(self.table_name, "timestamp")

    def get_all_limit(self, limit: int):
        return self.database.get_all_limit(self.table_name, limit, "timestamp")

    def get_all_limit_offset(self, limit: int, offset: int):
        return self.database.get_all_limit_offset(self.table_name, limit, offset, "timestamp")

    def get_track_count(self):
        query = "SELECT COUNT(*) FROM " + self.table_name
        conn = self.database.connect()
        c = conn.cursor()
        c.execute(query)
        result = c.fetchall()
        conn.close()
        return int(result[0][0])


class PlayingHistoryEntry:
    """
    A class to represent a played track"""

    def __init__(self) -> None:
        self.timestamp = 0
        self.track_id = ""
        self.date = ""

    @staticmethod
    def from_response(response: dict) -> "PlayingHistoryEntry":
        """
        Creates a PlayingHistoryEntry object from a Spotify API response
        :param response: Spotify API response
        :return: PlayingHistoryEntry object
        """
        entry = PlayingHistoryEntry()
        entry.timestamp = response["timestamp"]
        entry.track_id = response["item"]["id"]
        entry.date = datetime.fromtimestamp(int(entry.timestamp) / 1000.0).strftime("%Y-%m-%d")
        return entry

    @staticmethod
    def from_sql_result(result: tuple) -> "PlayingHistoryEntry":
        """
        Creates a PlayingHistoryEntry object from a SQL result
        :param result: SQL result
        :return: PlayingHistoryEntry object
        """
        entry = PlayingHistoryEntry()
        entry.timestamp = result[0]
        entry.track_id = result[1]
        entry.date = result[2]
        return entry

    def get_track(self):
        if TrackTable().has_track(self.track_id):
            return TrackTable().get_track(self.track_id)
        else:
            return None

    def __str__(self):
        track = self.get_track()
        if track is None:
            return "Track not found"
        ret = track.track_name + " by " + track.track_artist + " from the album " + track.track_album
        ret += (
            "Played at: "
            + datetime.fromtimestamp(int(self.timestamp) / 1000.0).strftime("%H:%M:%S")
            + " on "
            + self.date
        )
        return ret

    def __eq__(self, other: "PlayingHistoryEntry"):
        track = self.get_track()
        if track is None:
            return False
        return self.track_id == other.track_id and abs(int(self.timestamp) - int(other.timestamp)) < int(
            track.track_duration
        )
