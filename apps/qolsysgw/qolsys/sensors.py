import json
import logging
import time

from qolsys.exceptions import UnableToParseSensorException
from qolsys.exceptions import UnknownQolsysSensorException
from qolsys.observable import QolsysObservable
from qolsys.utils import find_subclass


LOGGER = logging.getLogger(__name__)


class QolsysSensor(QolsysObservable):
    NOTIFY_UPDATE_PATTERN = 'update_{attr}'
    NOTIFY_UPDATE_STATUS = 'update_status'
    NOTIFY_UPDATE_ATTRIBUTES = 'update_attributes'

    __SUBCLASSES_CACHE = {}
    _common_keys = [
        'name',
        'status',
        'zone_id',
        'partition_id',
    ]
    ATTRIBUTES = [
        'group',
        'state',
        'zone_type',
        'zone_physical_type',
        'zone_alarm_type',
        'tampered',
    ]

    def __init__(self, sensor_id: str, name: str, group: str, status: str,
                 state: str, zone_id: int, zone_type: int,
                 zone_physical_type: int, zone_alarm_type: int,
                 partition_id: int) -> None:
        super().__init__()

        self._id = sensor_id
        self._name = name
        self._group = group
        self._status = status
        self._state = state
        self._zone_id = zone_id
        self._zone_type = zone_type
        self._zone_physical_type = zone_physical_type
        self._zone_alarm_type = zone_alarm_type
        self._partition_id = partition_id

        self._tampered = False
        self._last_open_tampered_at = None
        self._last_closed_tampered_at = None

    def update(self, sensor: 'QolsysSensor'):
        if self.id != sensor.id:
            LOGGER.warning(f"Updating sensor '{self.id}' ({self.name}) with "
                           f"sensor '{sensor.id}' (different id)")

        # Because any of the attributes might have changed and we want to
        # be able to notify of all of those changes separately and only if they
        # happened, we have to add a bit of smart in there
        attributes_updated = False
        for attr in ['id'] + self._common_keys + self.ATTRIBUTES:
            local_attr = f'_{attr}'
            prev_value = getattr(self, local_attr)
            new_value = getattr(sensor, attr)
            if prev_value != new_value:
                setattr(self, local_attr, new_value)
                self.notify(change=self.NOTIFY_UPDATE_PATTERN.format(attr=attr),
                            prev_value=prev_value, new_value=new_value)

                if attr in self.ATTRIBUTES:
                    attributes_updated = True

        if attributes_updated:
            self.notify(change=self.NOTIFY_UPDATE_ATTRIBUTES)

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def group(self):
        return self._group

    @property
    def status(self):
        return self._status

    @property
    def state(self):
        return self._state

    @property
    def zone_id(self):
        return self._zone_id

    @property
    def zone_type(self):
        return self._zone_type

    @property
    def zone_physical_type(self):
        return self._zone_physical_type

    @property
    def zone_alarm_type(self):
        return self._zone_alarm_type

    @property
    def partition_id(self):
        return self._partition_id

    @property
    def tampered(self):
        return self._tampered

    @property
    def is_open(self):
        return self._status == 'Open'

    @property
    def is_closed(self):
        return self._status == 'Closed'

    @status.setter
    def status(self, value):
        new_value = value.capitalize()
        if new_value not in ['Open', 'Closed']:
            raise AttributeError(f"Invalid value '{value}' for attribute 'status'")

        if self._status != new_value:
            LOGGER.debug(f"Sensor '{self.id}' ({self.name}) status updated to '{new_value}'")
            prev_value = self._status

            self._status = new_value

            self.notify(change=self.NOTIFY_UPDATE_STATUS,
                        prev_value=prev_value, new_value=new_value)

    @tampered.setter
    def tampered(self, value):
        new_value = bool(value)

        if self._tampered != new_value:
            LOGGER.debug(f"Sensor '{self.id}' ({self.name}) tampered updated to '{new_value}'")
            prev_value = self._tampered

            self._tampered = new_value

            self.notify(change=self.NOTIFY_UPDATE_PATTERN.format(attr='tampered'),
                        prev_value=prev_value, new_value=new_value)
            self.notify(change=self.NOTIFY_UPDATE_ATTRIBUTES)

    def _next_status_update_is_status(self):
        # When we are back from a tamper setting, we get two updates
        # subsequently as an open, and then a close, in the same second
        return (self._last_open_tampered_at is not None and
                self._last_closed_tampered_at is not None and
                self._last_closed_tampered_at - self._last_open_tampered_at < 1)

    def open(self):
        if self.is_open and not self._next_status_update_is_status():
            self._last_open_tampered_at = time.time()
            self.tampered = True
        else:
            self.status = 'Open'

    def closed(self):
        if self.tampered:
            self._last_closed_tampered_at = time.time()
            self.tampered = False
        else:
            self.status = 'Closed'

    def __str__(self):
        return (f"<{type(self).__name__} id={self.id} name={self.name} "
                f"group={self.group} status={self.status} "
                f"state={self.state} zone_id={self.zone_id} "
                f"zone_type={self.zone_type} "
                f"zone_physical_type={self.zone_physical_type} "
                f"zone_alarm_type={self.zone_alarm_type} "
                f"partition_id={self.partition_id}>")

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            data = json.loads(data)

        sensor_type = data.get('type')
        if not sensor_type:
            raise UnknownQolsysSensorException(
                f'Sensor type not found for sensor {data}'
            )

        klass = find_subclass(cls, sensor_type, cache=cls.__SUBCLASSES_CACHE,
                              preserve_capitals=True)
        if not klass:
            raise UnknownQolsysSensorException(
                f"Sensor type '{sensor_type}' unsupported for sensor {data}"
            )

        return klass.from_json(data, common=cls.from_json_common_data(data))

    @classmethod
    def from_json_common_data(cls, data):
        common_data = {k: v for k, v in data.items()
                       if k in cls._common_keys or k in cls.ATTRIBUTES}
        common_data['sensor_id'] = data['id']
        return common_data

    @classmethod
    def from_json_subclass(cls, subtype, data, common=None):
        sensor_type = data.get('type')
        if sensor_type != subtype:
            raise UnableToParseSensorException(
                f"Cannot parse sensor '{sensor_type}'")

        if common is None:
            common = cls.from_json_common_data(data)

        return cls(**common)


class _QolsysSensorWithoutUpdates(object):
    pass


class QolsysSensorDoorWindow(QolsysSensor):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('Door_Window', data, common)


class QolsysSensorMotion(QolsysSensor):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('Motion', data, common)


class QolsysSensorPanelMotion(QolsysSensorMotion):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('Panel Motion', data, common)


class QolsysSensorGlassBreak(QolsysSensor):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('GlassBreak', data, common)


class QolsysSensorPanelGlassBreak(QolsysSensorGlassBreak, _QolsysSensorWithoutUpdates):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('Panel Glass Break', data, common)


class QolsysSensorBluetooth(QolsysSensor, _QolsysSensorWithoutUpdates):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('Bluetooth', data, common)


class QolsysSensorSmokeDetector(QolsysSensor):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('SmokeDetector', data, common)


class QolsysSensorCODetector(QolsysSensor):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('CODetector', data, common)


class QolsysSensorWater(QolsysSensor):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('Water', data, common)


class QolsysSensorFreeze(QolsysSensor):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('Freeze', data, common)


class QolsysSensorHeat(QolsysSensor):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('Heat', data, common)


class QolsysSensorTilt(QolsysSensor):
    @classmethod
    def from_json(cls, data, common=None):
        return cls.from_json_subclass('Tilt', data, common)
