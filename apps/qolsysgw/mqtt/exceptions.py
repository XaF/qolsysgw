from datetime import datetime, timezone


class MqttException(Exception):
    STATE = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._at = datetime.now(timezone.utc).isoformat()

        if self.STATE:
            self.STATE.last_exception = self

    @property
    def at(self):
        self._at


class UnknownMqttWrapperException(MqttException):
    pass


class UnknownDeviceClassException(MqttException):
    pass


class MqttPluginUnavailableException(MqttException):
    pass
