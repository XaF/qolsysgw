import json
import logging

from enum import Enum
from types import SimpleNamespace

from qolsys.exceptions import UnableToParseEventException
from qolsys.exceptions import UnknownQolsysEventException
from qolsys.exceptions import UnknownQolsysSensorException
from qolsys.partition import QolsysPartition
from qolsys.utils import find_subclass
from qolsys.sensors import QolsysSensor

LOGGER = logging.getLogger(__name__)


class QolsysEvent(object):

    __SUBCLASSES_CACHE = {}

    def __init__(self, request_id: str, raw_event: dict) -> None:
        self._request_id = request_id
        self._raw_event = raw_event

    @property
    def request_id(self):
        return self._request_id

    @property
    def raw(self):
        return self._raw_event

    @property
    def raw_str(self):
        return json.dumps(self.raw)

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            data = json.loads(data)

        event_type = data.get('event')
        klass = find_subclass(cls, event_type, cache=cls.__SUBCLASSES_CACHE)
        if not klass:
            raise UnknownQolsysEventException

        return klass.from_json(data)


class QolsysEventInfo(QolsysEvent):

    __INFOCLASSES_CACHE = {}

    @classmethod
    def from_json(cls, data):
        event_type = data.get('event')
        if event_type != 'INFO':
            raise UnableToParseEventException(f"Cannot parse event '{event_type}'")

        info_type = data.get('info_type')
        klass = find_subclass(cls, info_type, cache=cls.__INFOCLASSES_CACHE)
        if not klass:
            raise UnknownQolsysEventException

        return klass.from_json(data)


class QolsysEventInfoSummary(QolsysEventInfo):

    def __init__(self, partitions: list=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._partitions = partitions

    @property
    def partitions(self):
        return list(self._partitions)

    # @partitions.setter
    # def partitions(self, partitions):
        # self._partitions = partitions

    def __str__(self):
        return f"<{type(self).__name__} request_id={self.request_id} "\
                f"partitions({len(self.partitions)})="\
                f"[{', '.join([str(p) for p in self.partitions])}]>"

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            data = json.loads(data)

        info_type = data.get('info_type')
        if info_type != 'SUMMARY':
            raise UnableToParseEventException(
                f"Cannot parse event with info tyoe '{info_type}'")

        return QolsysEventInfoSummary(
            partitions=cls._parse_partitions(data),
            request_id=data.get('requestID'),
            raw_event=data,
        )

    @classmethod
    def _parse_partitions(cls, data):
        partitions = []

        partition_list = data['partition_list']
        for partition_info in partition_list:
            partition = QolsysPartition(
                partition_id=partition_info.get('partition_id'),
                name=partition_info.get('name'),
                status=partition_info.get('status'),
                secure_arm=partition_info.get('secure_arm'),
            )

            zone_list = partition_info['zone_list']
            for sensor_info in zone_list:
                try:
                    partition.add_sensor(QolsysSensor.from_json(sensor_info))
                except UnknownQolsysSensorException:
                    LOGGER.warning(f"sensor of unknown type: {sensor_info}")

            partitions.append(partition)

        return partitions


class QolsysEventInfoSecureArm(QolsysEventInfo):

    def __init__(self, partition_id: int, value: bool, version: int,
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._partition_id = partition_id
        self._value = value
        self._version = version

    @property
    def partition_id(self) -> int:
        return self._partition_id

    @property
    def value(self) -> bool:
        return self._value

    def __str__(self):
        return f"<{type(self).__name__} request_id={self.request_id} "\
                f"partition_id={self.partition_id} value={self.value}>"

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            data = json.loads(data)

        info_type = data.get('info_type')
        if info_type != 'SECURE_ARM':
            raise UnableToParseEventException(
                f"Cannot parse event with info tyoe '{info_type}'")

        return QolsysEventInfoSecureArm(
            partition_id=data.get('partition_id'),
            value=data.get('value'),
            version=data.get('version'),
            request_id=data.get('requestID'),
            raw_event=data,
        )


class QolsysEventZoneEvent(QolsysEvent):

    __ZONEEVENTCLASSES_CACHE = {}

    def __init__(self, version: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._version = version

    @property
    def zone(self):
        return None

    def __str__(self):
        return f"<{type(self).__name__} "\
                f"zone={self.zone} "\
                f"version={self._version}>"

    @classmethod
    def from_json(cls, data):
        event_type = data.get('event')
        if event_type != 'ZONE_EVENT':
            raise UnableToParseEventException(f"Cannot parse event '{event_type}'")

        zone_event_type = data.get('zone_event_type')
        if zone_event_type.startswith('ZONE_'):
            zone_event_type = zone_event_type[5:]
        klass = find_subclass(cls, zone_event_type, cache=cls.__ZONEEVENTCLASSES_CACHE)
        if not klass:
            raise UnknownQolsysEventException

        return klass.from_json(data)



class QolsysEventZoneEventActive(QolsysEventZoneEvent):

    def __init__(self, zone_id: int, zone_status: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._zone_id = zone_id
        self._zone_status = zone_status

    @property
    def zone(self):
        return SimpleNamespace(
            id=self._zone_id,
            status=self._zone_status,
        )

    @classmethod
    def from_json(cls, data):
        zone_event_type = data.get('zone_event_type')
        if zone_event_type != 'ZONE_ACTIVE':
            raise UnableToParseEventException(
                    f"Cannot parse zone event '{zone_event_type}'")

        return QolsysEventZoneEventActive(
            request_id=data.get('requestID'),
            version=data.get('version'),
            zone_id=data.get('zone', {}).get('zone_id'),
            zone_status=data.get('zone', {}).get('status'),
            raw_event=data,
        )


class QolsysEventZoneEventUpdate(QolsysEventZoneEvent):

    def __init__(self, zone: QolsysSensor, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._zone = zone

    @property
    def zone(self):
        return self._zone

    @classmethod
    def from_json(cls, data):
        zone_event_type = data.get('zone_event_type')
        if zone_event_type != 'ZONE_UPDATE':
            raise UnableToParseEventException(
                    f"Cannot parse zone event '{zone_event_type}'")

        zone = data.get('zone')
        try:
            sensor = QolsysSensor.from_json(zone)

            return QolsysEventZoneEventUpdate(
                request_id=data.get('requestID'),
                version=data.get('version'),
                zone=sensor,
                raw_event=data,
            )
        except UnknownQolsysSensorException:
            LOGGER.warning(f"sensor of unknown type: {zone}")
            raise UnableToParseEventException(
                f"Cannot parse zone event as unknown sensor type: {zone}")


class QolsysEventArming(QolsysEvent):

    def __init__(self, partition_id: int, arming_type: str, version: int,
                 delay: int=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._partition_id = partition_id
        self._arming_type = arming_type
        self._version = version
        self._delay = delay

    @property
    def partition_id(self):
        return self._partition_id

    @property
    def arming_type(self):
        return self._arming_type

    @property
    def delay(self):
        return self._delay

    def __str__(self):
        return f"<{type(self).__name__} "\
                f"partition_id={self.partition_id} "\
                f"arming_type={self.arming_type} "\
                f"delay{self.delay} "\
                f"version={self._version}>"

    @classmethod
    def from_json(cls, data):
        event_type = data.get('event')
        if event_type != 'ARMING':
            raise UnableToParseEventException(f"Cannot parse event '{event_type}'")

        return QolsysEventArming(
            request_id=data.get('requestID'),
            version=data.get('version'),
            partition_id=data.get('partition_id'),
            arming_type=data.get('arming_type'),
            delay=data.get('delay'),
            raw_event=data,
        )


class QolsysEventAlarm(QolsysEvent):

    def __init__(self, partition_id: int, alarm_type: str, version: int,
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._partition_id = partition_id
        self._alarm_type = alarm_type or None
        self._version = version

    @property
    def partition_id(self):
        return self._partition_id

    @property
    def alarm_type(self):
        return self._alarm_type

    @property
    def delay(self):
        return self._delay

    def __str__(self):
        return f"<{type(self).__name__} "\
                f"partition_id={self.partition_id} "\
                f"alarm_type={self.alarm_type} "\
                f"version={self._version}>"

    @classmethod
    def from_json(cls, data):
        event_type = data.get('event')
        if event_type != 'ALARM':
            raise UnableToParseEventException(f"Cannot parse event '{event_type}'")

        return QolsysEventAlarm(
            request_id=data.get('requestID'),
            version=data.get('version'),
            partition_id=data.get('partition_id'),
            alarm_type=data.get('alarm_type'),
            raw_event=data,
        )


# class QolsysEventError(QolsysEvent):
#    pass
