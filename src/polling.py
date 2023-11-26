import time

from src.database.history import HistoryTable
from src.database.tokens import AccessToken
from src.database.tracks import TrackTable


def poll_for_playing_history():
    token = AccessToken().get_token()
    if token is None:
        print("Failed to get token")
        return False
    currently_playing = AccessToken().get_currently_playing()
    if currently_playing is None:
        print("No currently playing track")
        return False
    elif isinstance(currently_playing, Exception):
        print("Issue with token: " + str(currently_playing))
        return False
    elif currently_playing["is_playing"]:
        TrackTable().add_track(currently_playing)
        HistoryTable().add_entry(currently_playing)
    return True


def polling_loop():
    while True:
        try:
            if poll_for_playing_history():
                print("Polled for playing history")
        except Exception as e:
            print(e)
        time.sleep(60)
