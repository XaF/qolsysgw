class QolsysException(Exception):
    pass


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
