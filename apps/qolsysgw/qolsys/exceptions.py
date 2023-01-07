from datetime import datetime, timezone


class QolsysException(Exception):
    STATE = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._at = datetime.now(timezone.utc).isoformat()

        if self.STATE:
            self.STATE.last_exception = self

    @property
    def at(self):
        return self._at


class QolsysGwConfigIncomplete(QolsysException):
    pass


class QolsysGwConfigError(QolsysException):
    pass


class UnableToParseEventException(QolsysException):
    pass


class UnableToParseSensorException(QolsysException):
    pass


class UnknownQolsysControlException(QolsysException):
    pass


class UnknownQolsysEventException(QolsysException):
    pass


class UnknownQolsysSensorException(QolsysException):
    pass


class MissingUserCodeException(QolsysException):
    pass


class InvalidUserCodeException(QolsysException):
    pass
