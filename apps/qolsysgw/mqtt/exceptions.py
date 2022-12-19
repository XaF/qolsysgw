class MqttException(Exception):
    pass


class UnknownMqttWrapperException(MqttException):
    pass


class UnknownDeviceClassException(MqttException):
    pass
