import os
import threading
import time

from django.apps import AppConfig


class LynifyApp(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lynify"
    is_polling = False

    @staticmethod
    def poll_for_playing_history():
        print("Polling for playing history")
        from lynify.models.history import HistoryModel
        from lynify.models.tokens import AccessToken
        from lynify.models.tracks import TrackModel

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

    @staticmethod
    def polling_loop():
        while True:
            try:
                if LynifyApp.poll_for_playing_history():
                    print("Polled for playing history")
            except Exception as e:
                print(e)
            time.sleep(60)

    def ready(self):
        # avoid running multiple polling threads
        # doesn't work when running with gunicorn
        if not os.environ.get("RUN_MAIN"):
            return

        print("Starting polling thread")
        self.is_polling = True
        thr = threading.Thread(target=LynifyApp.polling_loop)
        thr.daemon = True
        thr.start()
