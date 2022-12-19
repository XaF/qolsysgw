import logging

LOGGER = logging.getLogger(__name__)


class QolsysObservable(object):
    def __init__(self):
        self._observers = dict()

    def register(self, observer, callback=None):
        LOGGER.debug(f"Registering {repr(observer)} to {self} updates")
        if callback is None:
            callback = getattr(observer, 'update')
        self._observers[observer] = callback

    def unregister(self, observer):
        LOGGER.debug(f"Unregistering {repr(observer)} from {self} updates")
        del self._observers[observer]

    def notify(self, **payload):
        LOGGER.debug(f"Notifying {self} observers with: {payload}")
        for observer, callback in self._observers.items():
            callback(self, **payload)
