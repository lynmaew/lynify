import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lynify.settings")
import django

django.setup()
import time

from lynify.models.history import HistoryModel
from lynify.models.tokens import AccessToken
from lynify.models.tracks import TrackModel

"""
Polling script for use outside of manage.py
"""


def poll_for_playing_history():
    print("Polling for playing history")

    token = AccessToken.get_token()
    if token is None:
        print("Failed to get token")
        return False
    currently_playing = token.get_currently_playing()
    if currently_playing is None:
        print("No currently playing track")
        return False
    elif isinstance(currently_playing, Exception):
        print("Issue with token: " + str(currently_playing))
        return False
    elif currently_playing["is_playing"]:
        TrackModel.from_spotify(currently_playing["item"]["id"])
        HistoryModel.from_spotify(currently_playing)
    return True


def polling_loop():
    while True:
        try:
            if poll_for_playing_history():
                print("Polled for playing history")
        except Exception as e:
            print(e)
        time.sleep(60)


if __name__ == "__main__":
    polling_loop()
