import os
import threading

from django.apps import AppConfig

from lynify.server.polling import polling_loop


class LynifyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lynify"
    is_polling = False

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return

        print("Starting polling thread")
        self.is_polling = True
        thr = threading.Thread(target=polling_loop)
        thr.daemon = True
        thr.start()
