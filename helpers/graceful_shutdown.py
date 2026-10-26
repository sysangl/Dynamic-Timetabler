# shutdown_logger.py
import atexit
import logging
import os
import signal
import threading
from datetime import datetime

server_logger = logging.getLogger('server')

_shutting_down = threading.Event()


def _log_shutdown(reason: str) -> None:
    if _shutting_down.is_set():
        return
    _shutting_down.set()

    pid = os.getpid()
    when = datetime.now().isoformat() + "Z"
    server_logger.info("Flask server shutting down (pid=%s) - %s - %s", pid, reason, when)

    for h in server_logger.handlers:
        h.flush()

def _install_signal_handlers() -> None:
    def _handler(signum, frame):
        name = signal.Signals(signum).name
        _log_shutdown(f"caught signal {name}")

        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    for sig in ("SIGINT", "SIGTERM", "SIGBREAK"):
        if hasattr(signal, sig):
            signal.signal(getattr(signal, sig), _handler)


def _install_atexit_hook() -> None:
    @atexit.register
    def _on_exit():
        if not _shutting_down.is_set():
            _log_shutdown("normal interpreter exit (atexit)")


def _install_flask_teardown(app) -> None:
    @app.teardown_appcontext
    def _flask_teardown(exception):
        if not _shutting_down.is_set():
            _log_shutdown("Flask app context tearing down")


def enable_graceful_shutdown_logging(app):
    _install_signal_handlers()
    _install_atexit_hook()
    _install_flask_teardown(app)
