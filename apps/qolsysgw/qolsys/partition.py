import logging

from qolsys.observable import QolsysObservable


LOGGER = logging.getLogger(__name__)


class QolsysPartition(QolsysObservable):

    NOTIFY_ADD_SENSOR = 'add_sensor'
    NOTIFY_REMOVE_SENSOR = 'remove_sensor'
    NOTIFY_UPDATE_ALARM_TYPE = 'update_alarm_type'
    NOTIFY_UPDATE_SECURE_ARM = 'update_secure_arm'
    NOTIFY_UPDATE_STATUS = 'update_status'

    def __init__(self, partition_id: int, name: str, status: str,
                 secure_arm: bool) -> None:
        super().__init__()

        self._id = partition_id
        self._name = name
        self._status = status
        self._secure_arm = secure_arm
        self._sensors = {}
        self._alarm_type = None

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def status(self):
        return self._status

    @property
    def secure_arm(self):
        return self._secure_arm

    @property
    def alarm_type(self):
        return self._alarm_type

    @property
    def sensors(self):
        return self._sensors.values()

    @status.setter
    def status(self, value):
        new_value = value.upper()
        if self._status != new_value:
            LOGGER.debug(f"Partition '{self.id}' ({self.name}) status updated to '{new_value}'")
            prev_value = self._status

            self._status = new_value

            self.notify(change=self.NOTIFY_UPDATE_STATUS,
                        prev_value=prev_value, new_value=new_value)

        self.alarm_type = None

    @secure_arm.setter
    def secure_arm(self, value):
        new_value = bool(value)
        if self._secure_arm != new_value:
            LOGGER.debug(f"Partition '{self.id}' ({self.name}) secure arm updated to '{new_value}'")
            prev_value = self._secure_arm
            self._secure_arm = new_value

            self.notify(change=self.NOTIFY_UPDATE_SECURE_ARM,
                        prev_value=prev_value, new_value=new_value)

    @alarm_type.setter
    def alarm_type(self, value):
        if value is not None:
            value = value.upper()

        if self._alarm_type != value:
            LOGGER.debug(f"Partition '{self.id}' ({self.name}) alarm type updated to '{value}'")
            prev_value = self._alarm_type
            self._alarm_type = value

            self.notify(change=self.NOTIFY_UPDATE_ALARM_TYPE,
                        prev_value=prev_value, new_value=value)

    def triggered(self, alarm_type: str = None):
        self.status = 'ALARM'
        self.alarm_type = alarm_type

    def zone(self, zone_id, default=None):
        return self._sensors.get(zone_id, default)

    def add_sensor(self, sensor):
        psensor = self._sensors.get(sensor.zone_id)
        if psensor is not None:
            LOGGER.error(f"Zone ID '{sensor.zone_id}' already used by sensor "
                         f"'{psensor.id}' ({psensor.name}) but sensor "
                         f"'{sensor.id}' ({sensor.name}) declares the same "
                         "zone; skipping")
            return

        self._sensors[sensor.zone_id] = sensor
        self.notify(change=self.NOTIFY_ADD_SENSOR, new_value=sensor)

    def update_sensor(self, sensor):
        psensor = self._sensors.get(sensor.zone_id)
        if psensor is None:
            return

        psensor.update(sensor)

    def remove_sensor(self, sensor):
        self.remove_zone(sensor.zone_id)

    def remove_zone(self, zone_id):
        zone = self._sensors[zone_id]

        del self._sensors[zone_id]

        self.notify(change=self.NOTIFY_REMOVE_SENSOR,
                    prev_value=zone)

    def __str__(self):
        return (f"<QolsysPartition id={self.id} name={self.name} "
                f"status={self.status} secure_arm={self.secure_arm} "
                f"sensors({len(self.sensors)})="
                f"[{', '.join([str(s) for s in self.sensors])}]>")
