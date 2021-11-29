import logging

from qolsys.observable import QolsysObservable


LOGGER = logging.getLogger(__name__)


class QolsysPartition(QolsysObservable):
    NOTIFY_ADD_SENSOR = 'add_sensor'
    NOTIFY_REMOVE_SENSOR = 'remove_sensor'
    NOTIFY_UPDATE_STATUS = 'update_status'

    def __init__(self, partition_id: int, name: str, status: str,
                 secure_arm: bool) -> None:
        super().__init__()

        self._id = partition_id
        self._name = name
        self._status = status
        self._secure_arm = secure_arm
        self._sensors = {}

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

    def triggered(self):
        self.status = 'ALARM'

    def zone(self, zone_id, default=None):
        return self._sensors.get(zone_id, default)

    def add_sensor(self, sensor):
        psensor = self._sensors.get(sensor.zone_id)
        if psensor is not None:
            LOGGER.error(f"Zone ID '{sensor.zone_id}' already used by sensor "\
                    f"'{psensor.id}' ({psensor.name}) but sensor "\
                    f"'{sensor.id}' ({sensor.name}) declares the same zone; "\
                    "skipping")
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
        zone = self.sensors[zone_id]
        
        del self.sensors[zone_id]
        
        self.notify(change=self.NOTIFY_REMOVE_SENSOR,
                    prev_value=zone)

    def __str__(self):
        return f"<QolsysPartition id={self.id} name={self.name} "\
                f"status={self.status} secure_arm={self.secure_arm} "\
                f"sensors({len(self.sensors)})="\
                f"[{', '.join([str(s) for s in self.sensors])}]>"

