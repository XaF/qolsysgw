class QolsysException(Exception):
    pass

class QolsysGwConfigIncomplete(QolsysException):
    pass

class QolsysGwConfigError(QolsysException):
    pass

class UnableToParseEventException(QolsysException):
    pass

class UnknownQolsysControlException(QolsysException):
    pass

class UnknownQolsysEventException(QolsysException):
    pass

class UnknownQolsysSensorException(QolsysException):
    pass

class MissingDisarmCodeException(QolsysException):
    pass

class InvalidArmDisarmCodeException(QolsysException):
    pass
