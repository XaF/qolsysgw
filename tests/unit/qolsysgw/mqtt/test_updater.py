import unittest

from unittest import mock

import tests.unit.qolsysgw.mqtt.testenv  # noqa: F401

from mqtt.updater import MqttUpdater
from mqtt.updater import MqttWrapperFactory
from mqtt.updater import MqttWrapperQolsysState
from mqtt.updater import MqttWrapperQolsysPartition
from mqtt.updater import MqttWrapperQolsysSensor
from qolsys.config import QolsysGatewayConfig
from qolsys.state import QolsysState
from qolsys.partition import QolsysPartition
from qolsys.sensors import QolsysSensor


import logging
logging.basicConfig(level=logging.DEBUG)


class TestUnitMqttUpdater(unittest.TestCase):

    def test_unit_init_register_for_state_updates(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        state.register.assert_called_once_with(updater, updater._state_update)

    def test_unit_state_update_register_for_partition_updates(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        partition1 = mock.create_autospec(QolsysPartition)
        partition2 = mock.create_autospec(QolsysPartition)
        state.partitions = [partition1, partition2]

        updater._state_update(state, change=QolsysState.NOTIFY_UPDATE_PARTITIONS)

        partition1.register.assert_called_once_with(updater, updater._partition_update)
        partition2.register.assert_called_once_with(updater, updater._partition_update)

    def test_unit_state_update_configures_partitions(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        partition1 = mock.create_autospec(QolsysPartition)
        partition2 = mock.create_autospec(QolsysPartition)
        state.partitions = [partition1, partition2]

        wrapped = {
            partition1: mock.create_autospec(MqttWrapperQolsysPartition),
            partition2: mock.create_autospec(MqttWrapperQolsysPartition),
        }
        factory.wrap.side_effect = lambda obj: wrapped[obj]

        updater._state_update(state, change=QolsysState.NOTIFY_UPDATE_PARTITIONS)

        # Checked we wrapped the partitions using the factory
        wrap_calls = [
            mock.call(partition1),
            mock.call(partition2),
        ]
        factory.wrap.assert_has_calls(wrap_calls, any_order=True)
        assert factory.wrap.call_count == len(wrap_calls)

        # And that for each wrap we configured the partition
        wrapped[partition1].configure.assert_called_once_with()
        wrapped[partition2].configure.assert_called_once_with()

    def test_unit_state_update_register_for_sensor_updates(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        partition1 = mock.create_autospec(QolsysPartition)
        partition2 = mock.create_autospec(QolsysPartition)
        state.partitions = [partition1, partition2]

        sensor1 = mock.create_autospec(QolsysSensor)
        sensor2 = mock.create_autospec(QolsysSensor)
        sensor3 = mock.create_autospec(QolsysSensor)
        partition1.sensors = [sensor1, sensor2]
        partition2.sensors = [sensor3]

        updater._state_update(state, change=QolsysState.NOTIFY_UPDATE_PARTITIONS)

        for sensor in [sensor1, sensor2, sensor3]:
            sensor.register.assert_called_once_with(updater, updater._sensor_update)

    def test_unit_state_update_configures_sensors(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        partition1 = mock.create_autospec(QolsysPartition)
        partition2 = mock.create_autospec(QolsysPartition)
        state.partitions = [partition1, partition2]

        sensor1 = mock.create_autospec(QolsysSensor)
        sensor2 = mock.create_autospec(QolsysSensor)
        sensor3 = mock.create_autospec(QolsysSensor)
        partition1.sensors = [sensor1, sensor2]
        partition2.sensors = [sensor3]

        wrapped = {
            partition1: mock.create_autospec(MqttWrapperQolsysPartition),
            partition2: mock.create_autospec(MqttWrapperQolsysPartition),
            sensor1: mock.create_autospec(MqttWrapperQolsysSensor),
            sensor2: mock.create_autospec(MqttWrapperQolsysSensor),
            sensor3: mock.create_autospec(MqttWrapperQolsysSensor),
        }
        factory.wrap.side_effect = lambda obj: wrapped[obj]

        updater._state_update(state, change=QolsysState.NOTIFY_UPDATE_PARTITIONS)

        # Checked we wrapped the partitions using the factory
        wrap_calls = [
            mock.call(partition1),
            mock.call(partition2),
            mock.call(sensor1),
            mock.call(sensor2),
            mock.call(sensor3),
        ]
        factory.wrap.assert_has_calls(wrap_calls, any_order=True)
        assert factory.wrap.call_count == len(wrap_calls)

        # And that for each wrap we configured the partition
        wrapped[sensor1].configure.assert_called_once_with(partition=partition1)
        wrapped[sensor2].configure.assert_called_once_with(partition=partition1)
        wrapped[sensor3].configure.assert_called_once_with(partition=partition2)

    def test_unit_partition_update_add_sensor_configures_sensor(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        partition = mock.create_autospec(QolsysPartition)
        partition.name = f'TestPartition ({id(partition)})'

        new_sensor = mock.create_autospec(QolsysSensor)

        wrapped = {
            new_sensor: mock.create_autospec(MqttWrapperQolsysSensor),
        }
        factory.wrap.side_effect = lambda obj: wrapped[obj]

        updater._partition_update(partition,
                                  change=QolsysPartition.NOTIFY_ADD_SENSOR,
                                  new_value=new_sensor)

        new_sensor.register.assert_called_once_with(updater, callback=updater._sensor_update)
        wrapped[new_sensor].configure.assert_called_once_with(partition=partition)

    def test_unit_partition_update_update_status_updates_partition_state(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        partition = mock.create_autospec(QolsysPartition)
        partition.name = f'TestPartition ({id(partition)})'

        wrapped = {
            partition: mock.create_autospec(MqttWrapperQolsysPartition),
        }
        factory.wrap.side_effect = lambda obj: wrapped[obj]

        updater._partition_update(partition,
                                  change=QolsysPartition.NOTIFY_UPDATE_STATUS)

        wrapped[partition].update_state.assert_called_once_with()

    def test_unit_partition_update_update_secure_arm_configures_partition(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        partition = mock.create_autospec(QolsysPartition)
        partition.name = f'TestPartition ({id(partition)})'

        wrapped = {
            partition: mock.create_autospec(MqttWrapperQolsysPartition),
        }
        factory.wrap.side_effect = lambda obj: wrapped[obj]

        updater._partition_update(partition,
                                  change=QolsysPartition.NOTIFY_UPDATE_SECURE_ARM)

        wrapped[partition].configure.assert_called_once_with()

    def test_unit_partition_update_update_alarm_type_updates_attributes(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        partition = mock.create_autospec(QolsysPartition)
        partition.name = f'TestPartition ({id(partition)})'

        wrapped = {
            partition: mock.create_autospec(MqttWrapperQolsysPartition),
        }
        factory.wrap.side_effect = lambda obj: wrapped[obj]

        updater._partition_update(partition,
                                  change=QolsysPartition.NOTIFY_UPDATE_ALARM_TYPE)

        wrapped[partition].update_attributes.assert_called_once_with()

    def test_unit_sensor_update_update_status_updates_sensor_state(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        sensor = mock.create_autospec(QolsysSensor)
        sensor.name = f'TestSensor ({id(sensor)})'

        wrapped = {
            sensor: mock.create_autospec(MqttWrapperQolsysSensor),
        }
        factory.wrap.side_effect = lambda obj: wrapped[obj]

        updater._sensor_update(sensor,
                               change=QolsysSensor.NOTIFY_UPDATE_STATUS)

        wrapped[sensor].update_state.assert_called_once_with()

    def test_unit_sensor_update_update_attributes_updates_attributes(self):
        state = mock.create_autospec(QolsysState)
        factory = mock.create_autospec(MqttWrapperFactory)

        updater = MqttUpdater(state, factory)

        sensor = mock.create_autospec(QolsysSensor)
        sensor.name = f'TestSensor ({id(sensor)})'

        wrapped = {
            sensor: mock.create_autospec(MqttWrapperQolsysSensor),
        }
        factory.wrap.side_effect = lambda obj: wrapped[obj]

        updater._sensor_update(sensor,
                               change=QolsysSensor.NOTIFY_UPDATE_ATTRIBUTES)

        wrapped[sensor].update_attributes.assert_called_once_with()


class TestUnitMqttWrapperQolsys(unittest.TestCase):

    def setUp(self):
        # Configuration objects
        mqtt_publish = mock.MagicMock()
        session_token = 'TestSessionToken'

        # Mock plugin configuration
        mqtt_plugin_cfg = mock.MagicMock()
        self.mqtt_plugin_cfg_get = {
            'birth_topic': 'appdaemon',
            'will_topic': 'appdaemon',
            'birth_payload': 'online',
            'will_payload': 'offline',
        }

        def mqtt_plugin_cfg_get(cfg):
            return self.mqtt_plugin_cfg_get[cfg]

        mqtt_plugin_cfg.get.side_effect = mqtt_plugin_cfg_get

        # Mock app configuration
        cfg = mock.create_autospec(QolsysGatewayConfig)
        for k, v in QolsysGatewayConfig._DEFAULT_CONFIG.items():
            if v is not QolsysGatewayConfig._SENTINEL:
                setattr(cfg, k, v)

        cfg.panel_host = '127.0.0.1'
        cfg.panel_token = 'ToKeN'

        # Objects and their wrapped versions
        state = mock.create_autospec(QolsysState)
        wrapped_state = MqttWrapperQolsysState(
            state=state, mqtt_publish=mqtt_publish, cfg=cfg,
            mqtt_plugin_cfg=mqtt_plugin_cfg, session_token=session_token)

        partition = mock.create_autospec(QolsysPartition)
        partition.name = 'TestPartition'
        partition.id = 42
        wrapped_partition = MqttWrapperQolsysPartition(
            partition=partition, mqtt_publish=mqtt_publish, cfg=cfg,
            mqtt_plugin_cfg=mqtt_plugin_cfg, session_token=session_token)

        sensor = mock.create_autospec(QolsysSensor)
        sensor.name = 'TestSensor'
        sensor.partition_id = partition.id
        sensor.zone_id = 69
        wrapped_sensor = MqttWrapperQolsysSensor(
            sensor=sensor, mqtt_publish=mqtt_publish, cfg=cfg,
            mqtt_plugin_cfg=mqtt_plugin_cfg, session_token=session_token)

        # Make those available
        self.mqtt_publish = mqtt_publish
        self.session_token = session_token
        self.mqtt_plugin_cfg = mqtt_plugin_cfg
        self.cfg = cfg

        self.state = state
        self.wrapped_state = wrapped_state

        self.partition = partition
        self.wrapped_partition = wrapped_partition

        self.sensor = sensor
        self.wrapped_sensor = wrapped_sensor

        self.wrappers = {
            # 'state': wrapped_state,
            'partition': wrapped_partition,
            'sensor': wrapped_sensor,
        }

    def test_unit_partition_configure_payload(self):
        self.maxDiff = None

        actual = self.wrapped_partition.configure_payload()

        expected = {
            'availability': [
                {
                    'payload_available': 'online',
                    'payload_not_available': 'offline',
                    'topic': ('homeassistant/alarm_control_panel/qolsys_panel/'
                              'availability'),
                },
                {
                    'payload_available': 'online',
                    'payload_not_available': 'offline',
                    'topic': ('homeassistant/alarm_control_panel/qolsys_panel/'
                              'testpartition/availability'),
                },
                {
                    'payload_available': 'online',
                    'payload_not_available': 'offline',
                    'topic': 'appdaemon',
                },
            ],
            'availability_mode': 'all',
            'code_arm_required': True,
            'code_disarm_required': False,
            'code_trigger_required': True,
            'command_template': ('{"partition_id": "42", '
                                 '"action": "{{ action }}", '
                                 '"session_token": "TestSessionToken"}'),
            'command_topic': ('{discovery_topic}/alarm_control_panel/'
                              '{panel_unique_id}/set'),
            'device': {
                'identifiers': [
                    'qolsys_panel',
                ],
                'manufacturer': 'Qolsys',
                'model': 'IQ Panel 2+',
                'name': 'Qolsys Panel',
            },
            'json_attributes_topic': ('homeassistant/alarm_control_panel/'
                                      'qolsys_panel/testpartition/attributes'),
            'name': 'TestPartition',
            'state_topic': ('homeassistant/alarm_control_panel/qolsys_panel/'
                            'testpartition/state'),
            'unique_id': 'qolsys_panel_p42',
        }

        self.assertDictEqual(expected, actual)

    def test_unit_sensor_ha_device_class(self):
        for cls, device_class in MqttWrapperQolsysSensor.QOLSYS_TO_HA_DEVICE_CLASS.items():
            class SubCls(cls):
                def __init__(self):
                    pass

            sensor = SubCls()

            wrapped_sensor = MqttWrapperQolsysSensor(
                sensor=sensor, mqtt_publish=self.mqtt_publish, cfg=self.cfg,
                mqtt_plugin_cfg=self.mqtt_plugin_cfg,
                session_token=self.session_token)

            actual = wrapped_sensor.ha_device_class
            expected = device_class

            self.assertEqual(expected, actual, f'for sensor class {cls.__name__}')

    def test_unit_sensor_configure_payload(self):
        self.maxDiff = None

        actual = self.wrapped_sensor.configure_payload(
            partition=self.partition)

        expected = {
            'availability': [
                {
                    'payload_available': 'online',
                    'payload_not_available': 'offline',
                    'topic': ('homeassistant/alarm_control_panel/qolsys_panel/'
                              'availability'),
                },
                {
                    'payload_available': 'online',
                    'payload_not_available': 'offline',
                    'topic': ('homeassistant/binary_sensor/'
                              'testsensor/availability'),
                },
                {
                    'payload_available': 'online',
                    'payload_not_available': 'offline',
                    'topic': 'appdaemon',
                },
            ],
            'availability_mode': 'all',
            'device': {
                'identifiers': [
                    'qolsys_panel',
                ],
                'manufacturer': 'Qolsys',
                'model': 'IQ Panel 2+',
                'name': 'Qolsys Panel',
            },
            'device_class': 'safety',
            'json_attributes_topic': ('homeassistant/binary_sensor/'
                                      'testsensor/attributes'),
            'name': 'TestSensor',
            'payload_off': 'Closed',
            'payload_on': 'Open',
            'state_topic': ('homeassistant/binary_sensor/'
                            'testsensor/state'),
            'unique_id': 'qolsys_panel_p42z69',
        }

        self.assertDictEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
