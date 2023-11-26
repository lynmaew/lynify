import threading

from src.index import run_app
from src.polling import polling_loop


def app():
    threading.Thread(target=polling_loop).start()
    run_app()


if __name__ == "__main__":
    app()
