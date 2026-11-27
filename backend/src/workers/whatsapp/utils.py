import threading
from collections.abc import Callable

from neonize.proto.Neonize_pb2 import JID


def plain_jid(jid: JID) -> str:
    """'user@server' without the device part, safe to store and turn back into a JID."""
    return f"{jid.User}@{jid.Server}"


class VoteSettler:
    """Waits for a burst of events to stop before acting once.

    Each tap on a multi-select poll arrives as a separate vote. settle(key, action)
    schedules `action` to run `delay` seconds from now; another call with the same key
    before then replaces it. So three quick taps run the action once, with the last vote.
    """

    def __init__(self, delay: float):
        self.delay = delay
        self._timers: dict[str, threading.Timer] = {}
        self._guard = threading.Lock()

    def settle(self, key: str, action: Callable[[], object]) -> None:
        with self._guard:
            self._cancel(key)
            timer = threading.Timer(self.delay, self._fire, args=(key, action))
            timer.daemon = True
            self._timers[key] = timer
            timer.start()

    def cancel(self, key: str) -> None:
        with self._guard:
            self._cancel(key)

    def shutdown(self) -> None:
        with self._guard:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()

    def _fire(self, key: str, action: Callable[[], object]) -> None:
        with self._guard:
            self._timers.pop(key, None)
        action()

    def _cancel(self, key: str) -> None:
        if (timer := self._timers.pop(key, None)) is not None:
            timer.cancel()
