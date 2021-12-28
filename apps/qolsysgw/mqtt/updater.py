import json
import logging
import re
import posixpath

from mqtt.exceptions import UnknownDeviceClassException
from mqtt.exceptions import UnknownMqttWrapperException
from mqtt.utils import get_mac_from_host

from qolsys.config import QolsysGatewayConfig
from qolsys.partition import QolsysPartition
from qolsys.sensors import QolsysSensor
from qolsys.sensors import QolsysSensorBluetooth
from qolsys.sensors import QolsysSensorCODetector
from qolsys.sensors import QolsysSensorDoorWindow
from qolsys.sensors import QolsysSensorGlassBreak
from qolsys.sensors import QolsysSensorMotion
from qolsys.sensors import QolsysSensorSmokeDetector
from qolsys.sensors import QolsysSensorWater
from qolsys.state import QolsysState
from qolsys.utils import defaultLoggerCallback
from qolsys.utils import find_subclass


LOGGER = logging.getLogger(__name__)


class MqttUpdater(object):
    def __init__(self, state: QolsysState, factory: 'MqttWrapperFactory',
                 callback: callable=None, logger=None):
        self._factory = factory
        self._callback = callback or defaultLoggerCallback
        self._logger = logger or LOGGER

        state.register(self, callback=self._state_update)

    def _state_update(self, state: QolsysState, change, prev_value=None, new_value=None):
        self._logger.debug(f"Received update from state for CHANGE={change}")

        if change == QolsysState.NOTIFY_UPDATE_PARTITIONS:
            # The partitions have been updated, make sure we are registered for
            # all those partitions
            for partition in state.partitions:
                partition.register(self, callback=self._partition_update)
                self._factory.wrap(partition).configure()
                # The partition might already have sensors on it, so register
                # for each sensor individually too
                for sensor in partition.sensors:
                    sensor.register(self, callback=self._sensor_update)
                    self._factory.wrap(sensor).configure(partition=partition)

    def _partition_update(self, partition: QolsysPartition, change, prev_value=None, new_value=None):
        self._logger.debug(f"Received update from partition "\
                f"'{partition.name}' for CHANGE={change}, from "\
                f"prev_value={prev_value} to new_value={new_value}")

        if change == QolsysPartition.NOTIFY_ADD_SENSOR:
            sensor = new_value
            sensor.register(self, callback=self._sensor_update)
            self._factory.wrap(sensor).configure(partition=partition)
        elif change == QolsysPartition.NOTIFY_UPDATE_STATUS:
            self._factory.wrap(partition).update_state()
        elif change == QolsysPartition.NOTIFY_UPDATE_SECURE_ARM:
            self._factory.wrap(partition).configure()
        elif change == QolsysPartition.NOTIFY_UPDATE_ALARM_TYPE:
            self._factory.wrap(partition).update_attributes()

    def _sensor_update(self, sensor: QolsysSensor, change, prev_value=None, new_value=None):
        self._logger.debug(f"Received update from sensor '{sensor.name}' for "\
                f"CHANGE={change}, from prev_value={prev_value} to "\
                f"new_value={new_value}")

        if change == QolsysSensor.NOTIFY_UPDATE_STATUS:
            self._factory.wrap(sensor).update_state()
        elif change == QolsysSensor.NOTIFY_UPDATE_ATTRIBUTES:
            self._factory.wrap(sensor).update_attributes()


class MqttWrapper(object):

    def __init__(self, mqtt_publish: callable, cfg: QolsysGatewayConfig,
                 mqtt_plugin_cfg, session_token: str) -> None:
        self._mqtt_publish = mqtt_publish
        self._cfg = cfg

        self._birth_topic = mqtt_plugin_cfg.get('birth_topic')
        self._will_topic = mqtt_plugin_cfg.get('will_topic')
        self._birth_payload = mqtt_plugin_cfg.get('birth_payload')
        self._will_payload = mqtt_plugin_cfg.get('will_payload')

        self._session_token = session_token

        # This is an interesting thing: we can improve the behavior of the
        # plugin by using retain=True, but we need to be able to depend on
        # AppDaemon's status (and LWT message) to tell us when the connection
        # to the system is offline. This approach might also create weird
        # behaviors if we remove or add sensors between runs, so there is
        # a configuration option to plainly disable it.
        self._mqtt_retain = self._cfg.mqtt_retain and \
                (self._birth_topic == self._will_topic)

    @property
    def entity_id(self):
        return re.compile('\W').sub('_', self.name).lower()

    @property
    def config_topic(self):
        return posixpath.join(self._cfg.discovery_topic,
                              self.topic_path, 'config')

    @property
    def state_topic(self):
        return posixpath.join(self._cfg.discovery_topic,
                              self.topic_path, 'state')

    @property
    def attributes_topic(self):
        return posixpath.join(self._cfg.discovery_topic,
                              self.topic_path, 'attributes')

    @property
    def availability_topic(self):
        return posixpath.join(self._cfg.discovery_topic,
                              self.topic_path, 'availability')

    @property
    def device_availability_topic(self):
        return posixpath.join(self._cfg.discovery_topic,
                              'alarm_control_panel',
                              self._cfg.panel_unique_id or 'qolsys',
                              'availability')

    @property
    def payload_available(self):
        return 'online'

    @property
    def payload_unavailable(self):
        return 'offline'

    @property
    def configure_availability(self):
        availability = [
            {
                'topic': self.device_availability_topic,
                'payload_available': self.payload_available,
                'payload_not_available': self.payload_unavailable,
            },
            {
                'topic': self.availability_topic,
                'payload_available': self.payload_available,
                'payload_not_available': self.payload_unavailable,
            },
        ]

        # If we the birth and will topic of the MQTT plugin are the same,
        # we can take advantage of this to consider that the panel is offline
        # when AppDaemon is (since updates won't work at this point)
        if self._will_topic == self._birth_topic:
            availability.append({
                'topic': self._will_topic,
                'payload_available': self._birth_payload,
                'payload_not_available': self._will_payload,
            })

        return availability

    def configure(self, **kwargs):
        self._mqtt_publish(
            namespace=self._cfg.mqtt_namespace,
            topic=self.config_topic,
            retain=True,
            payload=json.dumps(self.configure_payload(**kwargs)),
        )

        self.set_available()
        self.update_state()
        self.update_attributes()

    def update_attributes(self):
        pass

    def update_state(self):
        pass

    def set_available(self):
        self._mqtt_publish(
            namespace=self._cfg.mqtt_namespace,
            topic=self.availability_topic,
            retain=self._mqtt_retain,
            payload=self.payload_available,
        )

    def set_unavailable(self):
        self._mqtt_publish(
            namespace=self._cfg.mqtt_namespace,
            topic=self.availability_topic,
            retain=True,
            payload=self.payload_unavailable,
        )


class MqttWrapperQolsysState(MqttWrapper):
    def __init__(self, state: QolsysState, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._state = state

    @property
    def name(self):
        return self._cfg.panel_unique_id or 'qolsys'

    @property
    def availability_topic(self):
        return self.device_availability_topic

    @property
    def entity_id(self):
        raise AttributeError(f"Property {entity_id} is not "\
                f"available for {type(self).__name__}")

    @property
    def config_topic(self):
        raise AttributeError(f"Property {config_topic} is not "\
                f"available for {type(self).__name__}")

    @property
    def state_topic(self):
        raise AttributeError(f"Property {state_topic} is not "\
                f"available for {type(self).__name__}")

    def configure(self):
        raise AttributeError(f"Method {configure} is not available "\
                f"for {type(self).__name__}")

    @property
    def configure_availability(self):
        raise AttributeError(f"Property {configure_availability} is not "\
                f"available for {type(self).__name__}")


class MqttWrapperQolsysPartition(MqttWrapper):

    QOLSYS_TO_HA_STATUS = {
        'DISARM': 'disarmed',
        'ARM_STAY': 'armed_home',
        'ARM_AWAY': 'armed_away',
        #'ARM_NIGHT': 'armed_night',
        #'': 'armed_vacation',
        #'': 'armed_custom_bypass',
        'ENTRY_DELAY': 'pending',
        'ALARM': 'triggered',
        'EXIT_DELAY': 'arming',
        'ARM-AWAY-EXIT-DELAY': 'arming',
    }

    def __init__(self, partition: QolsysPartition, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._partition = partition

    @property
    def name(self):
        return self._partition.name

    @property
    def ha_status(self):
        status = self.QOLSYS_TO_HA_STATUS.get(self._partition.status)
        if not status:
            raise ValueError('We need to put a better error here, but '\
                    'we found an unsupported status: '\
                    f"'{self._partition.status}'")
        return status

    @property
    def topic_path(self):
        return posixpath.join(
            'alarm_control_panel',
            self._cfg.panel_unique_id or 'qolsys',
            self.entity_id,
        )

    def configure_payload(self, **kwargs):
        command_template = {
            'partition_id': str(self._partition.id),
            'action': '{{ action }}',
            'session_token': self._session_token,
        }
        if (self._cfg.code_arm_required or self._cfg.code_disarm_required) and\
                not self._cfg.ha_check_user_code:
            # It is the only situation where we actually need to transmit
            # the code regularly through mqtt. In any other situation, we can
            # use the session token for comparison, which will allow to avoid
            # sharing the code in MQTT after initialization
            command_template['code'] = '{{ code }}'

        secure_arm = (self._partition.secure_arm and
                      not self._cfg.panel_user_code)

        payload = {
            'name': self.name,
            'state_topic': self.state_topic,
            'code_arm_required': self._cfg.code_arm_required or secure_arm,
            'code_disarm_required': self._cfg.code_disarm_required,
            'code_trigger_required': self._cfg.code_trigger_required or secure_arm,
            'command_topic': self._cfg.control_topic,
            'command_template': json.dumps(command_template),
            'availability_mode': 'all',
            'availability': self.configure_availability,
            'json_attributes_topic': self.attributes_topic,
        }

        # If we have a unique ID for the panel, we can setup a unique ID for
        # the partition, and create a device to link all of our partitions
        # together; this will also allow to interact with the partition in
        # the UI, change it's name, assign it to areas, etc.
        if self._cfg.panel_unique_id:
            payload['unique_id'] = f"{self._cfg.panel_unique_id}_p{self._partition.id}"
            payload['device'] = {
                'name': self._cfg.panel_device_name or self.name,
                'identifiers': [
                    self._cfg.panel_unique_id,
                ],
                'manufacturer': 'Qolsys',
                'model': 'IQ Panel 2+',
            }

            # If we are able to resolve the mac address, this will allow to
            # link the device to other related elements in home assistant
            mac = get_mac_from_host(self._cfg.panel_host)
            if mac:
                payload['device']['connections'] = [
                    ['mac', mac],
                ]

        if self._cfg.default_trigger_command:
            payload['payload_trigger'] = self._cfg.default_trigger_command

        if self._cfg.code_arm_required or self._cfg.code_disarm_required:
            code = self._cfg.ha_user_code or self._cfg.panel_user_code
            if self._cfg.ha_check_user_code:
                payload['code'] = code
            elif code is None or code.isdigit():
                payload['code'] = 'REMOTE_CODE'
            else:
                payload['code'] = 'REMOTE_CODE_TEXT'

        return payload

    def update_attributes(self):
        self._mqtt_publish(
            namespace=self._cfg.mqtt_namespace,
            topic=self.attributes_topic,
            retain=self._mqtt_retain,
            payload=json.dumps({
                'secure_arm': self._partition.secure_arm,
                'alarm_type': self._partition.alarm_type,
            }),
        )

    def update_state(self):
        self._mqtt_publish(
            namespace=self._cfg.mqtt_namespace,
            topic=self.state_topic,
            retain=self._mqtt_retain,
            payload=self.ha_status,
        )


class MqttWrapperQolsysSensor(MqttWrapper):

    PAYLOAD_ON = 'Open'
    PAYLOAD_OFF = 'Closed'

    QOLSYS_TO_HA_DEVICE_CLASS = {
        QolsysSensorDoorWindow: 'door',
        QolsysSensorMotion: 'motion',
        QolsysSensorGlassBreak: 'vibration',
        QolsysSensorBluetooth: 'presence',
        QolsysSensorSmokeDetector: 'smoke',
        QolsysSensorCODetector: 'gas',
        QolsysSensorWater: 'moisture',
    }

    def __init__(self, sensor: QolsysSensor, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._sensor = sensor

    @property
    def name(self):
        return self._sensor.name

    @property
    def ha_device_class(self):
        for base in type(self._sensor).mro():
            device_class = self.QOLSYS_TO_HA_DEVICE_CLASS.get(base)
            if device_class:
                return device_class

        errormsg = 'Unable to find a device class to map for '\
                f"sensor type {type(self._sensor).__name__}"
        if self._cfg.default_sensor_device_class:
            LOGGER.warning(f"{errormsg}, defaulting to "\
                    f"'{self._cfg.default_sensor_device_class}' device class.")
            return self._cfg.default_sensor_device_class
        else:
            raise UnknownDeviceClassException(errormsg)

    @property
    def topic_path(self):
        return posixpath.join(
            'binary_sensor',
            self.entity_id,
        )

    def configure_payload(self, partition: QolsysPartition, **kwargs):
        payload = {
            'name': self.name,
            'device_class': self.ha_device_class,
            'state_topic': self.state_topic,
            'payload_on': self.PAYLOAD_ON,
            'payload_off': self.PAYLOAD_OFF,
            'availability_mode': 'all',
            'availability': self.configure_availability,
            'json_attributes_topic': self.attributes_topic,
        }

        # If we have a unique ID for the panel, we can setup a unique ID for
        # the partition, and create a device to link all of our partitions
        # together; this will also allow to interact with the partition in
        # the UI, change it's name, assign it to areas, etc.
        if self._cfg.panel_unique_id:
            payload['unique_id'] = f"{self._cfg.panel_unique_id}_"\
                    f"p{self._sensor.partition_id}"\
                    f"z{self._sensor.zone_id}"
            payload['device'] = {
                'name': self._cfg.panel_device_name or partition.name,
                'identifiers': [
                    self._cfg.panel_unique_id,
                ],
                'manufacturer': 'QOLSYS',
                'model': 'IQ Panel 2+',
            }
            # TODO: Should each sensor be its own device ?
            # payload['device'] = {
                # 'name': f'{self.name} Sensor',
                # 'identifiers': [
                    # self._sensor.id,
                # ],
                # 'via_device': self._cfg.panel_unique_id,
            # }

        return payload

    def update_attributes(self):
        attributes = {
            k: getattr(self._sensor, k)
            for k in self._sensor.ATTRIBUTES
        }

        self._mqtt_publish(
            namespace=self._cfg.mqtt_namespace,
            topic=self.attributes_topic,
            retain=self._mqtt_retain,
            payload=json.dumps(attributes),
        )

    def update_state(self):
        self._mqtt_publish(
            namespace=self._cfg.mqtt_namespace,
            topic=self.state_topic,
            retain=self._mqtt_retain,
            payload=self._sensor.status,
        )


class MqttWrapperFactory(object):

    __WRAPPERCLASSES_CACHE = {}

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def wrap(self, obj):
        # Search the class that corresponds to that type, and use all the
        # parents (in order, thanks to the call to mro()) to try and find
        # one that works by inheritance
        for base in type(obj).mro():
            klass = find_subclass(MqttWrapper, base.__name__,
                                  cache=self.__WRAPPERCLASSES_CACHE,
                                  normalize=False)
            if klass:
                break

        if not klass:
            raise UnknownMqttWrapperException

        return klass(obj, *self._args, **self._kwargs)

