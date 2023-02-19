from copy import deepcopy
from types import SimpleNamespace

from unittest import mock

import testenv  # noqa: F401
from testbase import TestQolsysGatewayBase

from testutils.mock_types import ISODATE

from qolsys.sensors import QolsysSensorAuxiliaryPendant
from qolsys.sensors import QolsysSensorBluetooth
from qolsys.sensors import QolsysSensorCODetector
from qolsys.sensors import QolsysSensorDoorWindow
from qolsys.sensors import QolsysSensorFreeze
from qolsys.sensors import QolsysSensorGlassBreak
from qolsys.sensors import QolsysSensorHeat
from qolsys.sensors import QolsysSensorKeyFob
from qolsys.sensors import QolsysSensorKeypad
from qolsys.sensors import QolsysSensorMotion
from qolsys.sensors import QolsysSensorPanelGlassBreak
from qolsys.sensors import QolsysSensorPanelMotion
from qolsys.sensors import QolsysSensorSiren
from qolsys.sensors import QolsysSensorSmokeDetector
from qolsys.sensors import QolsysSensorTilt
from qolsys.sensors import QolsysSensorWater


class TestIntegrationQolsysEvents(TestQolsysGatewayBase):

    async def _check_partition_mqtt_messages(self, gw, partition_flat_name,
                                             partition_state, expected_state):
        state = partition_state

        mqtt_prefix = ('homeassistant/alarm_control_panel/'
                       f'qolsys_panel/{partition_flat_name}')

        with self.subTest(msg=f'MQTT config of partition {state.id} is correct'):
            mqtt_config = await gw.find_last_mqtt_publish(
                filters={'topic': f'{mqtt_prefix}/config'},
                raise_if_not_found=True,
            )

            self.assertIsNotNone(mqtt_config)
            self.maxDiff = None
            self.assertJsonDictEqual(
                {
                    'name': state.name,
                    'state_topic': f'{mqtt_prefix}/state',
                    'command_topic': 'homeassistant/alarm_control_panel/'
                                     'qolsys_panel/set',
                    'command_template': mock.ANY,
                    'code': 'REMOTE_CODE',
                    'code_disarm_required': True,
                    'code_arm_required': False,
                    'code_trigger_required': False,
                    'availability_mode': 'all',
                    'availability': [
                        {
                            'topic': 'homeassistant/alarm_control_panel/'
                                     'qolsys_panel/availability',
                            'payload_available': 'online',
                            'payload_not_available': 'offline',
                        },
                        {
                            'topic': f'{mqtt_prefix}/availability',
                            'payload_available': 'online',
                            'payload_not_available': 'offline',
                        },
                        {
                            'topic': 'appdaemon/birth_and_will',
                            'payload_available': 'online',
                            'payload_not_available': 'offline',
                        },
                    ],
                    'json_attributes_topic': f'{mqtt_prefix}/attributes',
                    'unique_id': f'qolsys_panel_p{state.id}',
                    'device': mock.ANY,
                },
                mqtt_config['payload'],
            )

        with self.subTest(msg=f'MQTT availability of partition {state.id} is correct'):
            mqtt_availability = await gw.find_last_mqtt_publish(
                filters={'topic': f'{mqtt_prefix}/availability'},
                raise_if_not_found=True,
            )

            self.assertIsNotNone(mqtt_availability)
            self.assertEqual('online', mqtt_availability['payload'])

        with self.subTest(msg=f'MQTT state of partition {state.id} is correct'):
            mqtt_state = await gw.find_last_mqtt_publish(
                filters={'topic': f'{mqtt_prefix}/state'},
                raise_if_not_found=True,
            )

            self.assertIsNotNone(mqtt_state)
            self.assertEqual(expected_state, mqtt_state['payload'])

        with self.subTest(msg=f'MQTT attributes of partition {state.id} are correct'):
            mqtt_attributes = await gw.find_last_mqtt_publish(
                filters={'topic': f'{mqtt_prefix}/attributes'},
                raise_if_not_found=True,
            )

            self.assertIsNotNone(mqtt_attributes)
            self.maxDiff = None
            self.assertJsonDictEqual(
                {
                    'alarm_type': state.alarm_type,
                    'secure_arm': state.secure_arm,
                    'last_error_type': state.last_error_type,
                    'last_error_desc': state.last_error_desc,
                    'last_error_at': state.last_error_at,
                    'disarm_failed': state.disarm_failed,
                },
                mqtt_attributes['payload'],
            )

    async def _check_sensor_mqtt_messages(self, gw, sensor_flat_name,
                                          sensor_unique_id,
                                          sensor_state, expected_device_class,
                                          expected_enabled_by_default=True):
        state = sensor_state

        mqtt_prefix = f'homeassistant/binary_sensor/{sensor_flat_name}'

        with self.subTest(msg=f'MQTT config of sensor {state.zone_id} is correct'):
            mqtt_config = await gw.find_last_mqtt_publish(
                filters={'topic': f'{mqtt_prefix}/config'},
            )

            self.assertIsNotNone(mqtt_config)

            self.maxDiff = None
            self.assertJsonDictEqual(
                {
                    'name': state.name,
                    'device_class': expected_device_class,
                    'state_topic': f'{mqtt_prefix}/state',
                    'payload_on': 'Open',
                    'payload_off': 'Closed',
                    'availability_mode': 'all',
                    'availability': [
                        {
                            'topic': 'homeassistant/alarm_control_panel/'
                                     'qolsys_panel/availability',
                            'payload_available': 'online',
                            'payload_not_available': 'offline',
                        },
                        {
                            'topic': f'{mqtt_prefix}/availability',
                            'payload_available': 'online',
                            'payload_not_available': 'offline',
                        },
                        {
                            'topic': 'appdaemon/birth_and_will',
                            'payload_available': 'online',
                            'payload_not_available': 'offline',
                        },
                    ],
                    'json_attributes_topic': f'{mqtt_prefix}/attributes',
                    'unique_id': f'qolsys_panel_s{sensor_unique_id}',
                    'device': mock.ANY,
                    'enabled_by_default': expected_enabled_by_default,
                },
                mqtt_config['payload'],
            )

        with self.subTest(msg=f'MQTT availability of sensor {state.zone_id} is correct'):
            mqtt_availability = await gw.find_last_mqtt_publish(
                filters={'topic': f'{mqtt_prefix}/availability'},
            )

            self.assertIsNotNone(mqtt_availability)
            self.assertEqual('online', mqtt_availability['payload'])

        with self.subTest(msg=f'MQTT state of sensor {state.zone_id} is correct'):
            mqtt_state = await gw.find_last_mqtt_publish(
                filters={'topic': f'{mqtt_prefix}/state'},
            )

            self.assertIsNotNone(mqtt_state)
            self.assertEqual(state.status, mqtt_state['payload'])

        with self.subTest(msg=f'MQTT attributes of sensor {state.zone_id} is correct'):
            mqtt_attributes = await gw.find_last_mqtt_publish(
                filters={'topic': f'{mqtt_prefix}/attributes'},
            )

            self.assertIsNotNone(mqtt_attributes)
            self.assertJsonDictEqual(
                {
                    'group': state.group,
                    'state': state.state,
                    'zone_physical_type': state.zone_physical_type,
                    'zone_alarm_type': state.zone_alarm_type,
                    'zone_type': state.zone_type,
                    'tampered': state.tampered,
                },
                mqtt_attributes['payload'],
            )

    async def test_integration_event_info_summary_initializes_all_entities(self):
        panel, gw, entity_ids, topics = await self._ready_panel_and_gw()

        mqtt_publish_calls = []

        for partition in ['partition0', 'partition1']:
            for topic in topics:
                mqtt_publish_calls.append(mock.call(
                    (f'homeassistant/alarm_control_panel/'
                     f'qolsys_panel/{partition}/{topic}'),
                    mock.ANY,
                    namespace=mock.ANY,
                    retain=mock.ANY,
                ))

        for entity_id in entity_ids:
            for topic in topics:
                mqtt_publish_calls.append(mock.call(
                    f'homeassistant/binary_sensor/{entity_id}/{topic}',
                    mock.ANY,
                    namespace=mock.ANY,
                    retain=mock.ANY,
                ))

        # Now we can actually check if the topics have been published
        gw.mqtt_publish_func.assert_has_calls(
            mqtt_publish_calls, any_order=True)

        # Check that the client is still connected
        self.assertTrue(panel.is_client_connected)

        # Check the state information
        state = gw._state
        with self.subTest(msg='State has the right number of partitions'):
            self.assertEqual(2, len(state.partitions))

        # Check the partitions information
        with self.subTest(msg='Partition 0 is properly configured'):
            partition0 = state.partition(0)
            self.assertEqual(10, len(partition0.sensors))
            self.assertEqual(0, partition0.id)
            self.assertEqual('partition0', partition0.name)
            self.assertEqual('DISARM', partition0.status)
            self.assertEqual(False, partition0.secure_arm)
            self.assertIsNone(partition0.alarm_type)

            await self._check_partition_mqtt_messages(
                gw=gw,
                partition_flat_name='partition0',
                partition_state=partition0,
                expected_state='disarmed',
            )

        with self.subTest(msg='Partition 1 is properly configured'):
            partition1 = state.partition(1)
            self.assertEqual(8, len(partition1.sensors))
            self.assertEqual(1, partition1.id)
            self.assertEqual('partition1', partition1.name)
            self.assertEqual('DISARM', partition1.status)
            self.assertEqual(False, partition1.secure_arm)
            self.assertIsNone(partition1.alarm_type)

            await self._check_partition_mqtt_messages(
                gw=gw,
                partition_flat_name='partition1',
                partition_state=partition1,
                expected_state='disarmed',
            )

        # Check the sensors information
        with self.subTest(msg='Sensor 100 is properly configured'):
            sensor100 = partition0.zone(100)
            self.assertEqual(QolsysSensorDoorWindow, sensor100.__class__)
            self.assertEqual('001-0000', sensor100.id)
            self.assertEqual('My Door', sensor100.name)
            self.assertEqual('entryexitdelay', sensor100.group)
            self.assertEqual('Closed', sensor100.status)
            self.assertEqual('0', sensor100.state)
            self.assertEqual(100, sensor100.zone_id)
            self.assertEqual(1, sensor100.zone_physical_type)
            self.assertEqual(3, sensor100.zone_alarm_type)
            self.assertEqual(1, sensor100.zone_type)
            self.assertEqual(0, sensor100.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_door',
                sensor_unique_id='001_0000',
                sensor_state=sensor100,
                expected_device_class='door',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 101 is properly configured'):
            sensor101 = partition0.zone(101)
            self.assertEqual(QolsysSensorDoorWindow, sensor101.__class__)
            self.assertEqual('001-0001', sensor101.id)
            self.assertEqual('My Window', sensor101.name)
            self.assertEqual('entryexitlongdelay', sensor101.group)
            self.assertEqual('Open', sensor101.status)
            self.assertEqual('0', sensor101.state)
            self.assertEqual(101, sensor101.zone_id)
            self.assertEqual(1, sensor101.zone_physical_type)
            self.assertEqual(3, sensor101.zone_alarm_type)
            self.assertEqual(1, sensor101.zone_type)
            self.assertEqual(0, sensor101.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_window',
                sensor_unique_id='001_0001',
                sensor_state=sensor101,
                expected_device_class='door',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 110 is properly configured'):
            sensor110 = partition0.zone(110)
            self.assertEqual(QolsysSensorMotion, sensor110.__class__)
            self.assertEqual('001-0010', sensor110.id)
            self.assertEqual('My Motion', sensor110.name)
            self.assertEqual('awayinstantmotion', sensor110.group)
            self.assertEqual('Closed', sensor110.status)
            self.assertEqual('0', sensor110.state)
            self.assertEqual(110, sensor110.zone_id)
            self.assertEqual(2, sensor110.zone_physical_type)
            self.assertEqual(3, sensor110.zone_alarm_type)
            self.assertEqual(2, sensor110.zone_type)
            self.assertEqual(0, sensor110.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_motion',
                sensor_unique_id='001_0010',
                sensor_state=sensor110,
                expected_device_class='motion',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 111 is properly configured'):
            sensor111 = partition0.zone(111)
            self.assertEqual(QolsysSensorPanelMotion, sensor111.__class__)
            self.assertEqual('001-0011', sensor111.id)
            self.assertEqual('Panel Motion', sensor111.name)
            self.assertEqual('safetymotion', sensor111.group)
            self.assertEqual('Closed', sensor111.status)
            self.assertEqual('0', sensor111.state)
            self.assertEqual(111, sensor111.zone_id)
            self.assertEqual(1, sensor111.zone_physical_type)
            self.assertEqual(3, sensor111.zone_alarm_type)
            self.assertEqual(119, sensor111.zone_type)
            self.assertEqual(0, sensor111.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='panel_motion',
                sensor_unique_id='001_0011',
                sensor_state=sensor111,
                expected_device_class='motion',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 120 is properly configured'):
            sensor120 = partition0.zone(120)
            self.assertEqual(QolsysSensorGlassBreak, sensor120.__class__)
            self.assertEqual('001-0020', sensor120.id)
            self.assertEqual('My Glass Break', sensor120.name)
            self.assertEqual('glassbreakawayonly', sensor120.group)
            self.assertEqual('Closed', sensor120.status)
            self.assertEqual('0', sensor120.state)
            self.assertEqual(120, sensor120.zone_id)
            self.assertEqual(1, sensor120.zone_physical_type)
            self.assertEqual(0, sensor120.zone_alarm_type)
            self.assertEqual(116, sensor120.zone_type)
            self.assertEqual(0, sensor120.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_glass_break',
                sensor_unique_id='001_0020',
                sensor_state=sensor120,
                expected_device_class='vibration',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 121 is properly configured'):
            sensor121 = partition0.zone(121)
            self.assertEqual(QolsysSensorPanelGlassBreak, sensor121.__class__)
            self.assertEqual('001-0021', sensor121.id)
            self.assertEqual('Panel Glass Break', sensor121.name)
            self.assertEqual('glassbreakawayonly', sensor121.group)
            self.assertEqual('Closed', sensor121.status)
            self.assertEqual('0', sensor121.state)
            self.assertEqual(121, sensor121.zone_id)
            self.assertEqual(1, sensor121.zone_physical_type)
            self.assertEqual(0, sensor121.zone_alarm_type)
            self.assertEqual(116, sensor121.zone_type)
            self.assertEqual(0, sensor121.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='panel_glass_break',
                sensor_unique_id='001_0021',
                sensor_state=sensor121,
                expected_device_class='vibration',
                expected_enabled_by_default=False,
            )

        with self.subTest(msg='Sensor 130 is properly configured'):
            sensor130 = partition0.zone(130)
            self.assertEqual(QolsysSensorBluetooth, sensor130.__class__)
            self.assertEqual('001-0030', sensor130.id)
            self.assertEqual('My Phone', sensor130.name)
            self.assertEqual('mobileintrusion', sensor130.group)
            self.assertEqual('Closed', sensor130.status)
            self.assertEqual('0', sensor130.state)
            self.assertEqual(130, sensor130.zone_id)
            self.assertEqual(1, sensor130.zone_physical_type)
            self.assertEqual(1, sensor130.zone_alarm_type)
            self.assertEqual(115, sensor130.zone_type)
            self.assertEqual(0, sensor130.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_phone',
                sensor_unique_id='001_0030',
                sensor_state=sensor130,
                expected_device_class='presence',
                expected_enabled_by_default=False,
            )

        with self.subTest(msg='Sensor 140 is properly configured'):
            sensor140 = partition0.zone(140)
            self.assertEqual(QolsysSensorSmokeDetector, sensor140.__class__)
            self.assertEqual('001-0040', sensor140.id)
            self.assertEqual('My Smoke Detector', sensor140.name)
            self.assertEqual('smoke_heat', sensor140.group)
            self.assertEqual('Closed', sensor140.status)
            self.assertEqual('0', sensor140.state)
            self.assertEqual(140, sensor140.zone_id)
            self.assertEqual(9, sensor140.zone_physical_type)
            self.assertEqual(9, sensor140.zone_alarm_type)
            self.assertEqual(5, sensor140.zone_type)
            self.assertEqual(0, sensor140.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_smoke_detector',
                sensor_unique_id='001_0040',
                sensor_state=sensor140,
                expected_device_class='smoke',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 141 is properly configured'):
            sensor141 = partition0.zone(141)
            self.assertEqual(QolsysSensorCODetector, sensor141.__class__)
            self.assertEqual('001-0041', sensor141.id)
            self.assertEqual('My CO Detector', sensor141.name)
            self.assertEqual('entryexitdelay', sensor141.group)
            self.assertEqual('Closed', sensor141.status)
            self.assertEqual('0', sensor141.state)
            self.assertEqual(141, sensor141.zone_id)
            self.assertEqual(1, sensor141.zone_physical_type)
            self.assertEqual(3, sensor141.zone_alarm_type)
            self.assertEqual(1, sensor141.zone_type)
            self.assertEqual(0, sensor141.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_co_detector',
                sensor_unique_id='001_0041',
                sensor_state=sensor141,
                expected_device_class='gas',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 150 is properly configured'):
            sensor150 = partition0.zone(150)
            self.assertEqual(QolsysSensorWater, sensor150.__class__)
            self.assertEqual('001-0050', sensor150.id)
            self.assertEqual('My Water Detector', sensor150.name)
            self.assertEqual('WaterSensor', sensor150.group)
            self.assertEqual('Closed', sensor150.status)
            self.assertEqual('0', sensor150.state)
            self.assertEqual(150, sensor150.zone_id)
            self.assertEqual(8, sensor150.zone_physical_type)
            self.assertEqual(0, sensor150.zone_alarm_type)
            self.assertEqual(15, sensor150.zone_type)
            self.assertEqual(0, sensor150.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_water_detector',
                sensor_unique_id='001_0050',
                sensor_state=sensor150,
                expected_device_class='moisture',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 200 is properly configured'):
            sensor200 = partition1.zone(200)
            self.assertEqual(QolsysSensorDoorWindow, sensor200.__class__)
            self.assertEqual('002-0000', sensor200.id)
            self.assertEqual('My 2nd Door', sensor200.name)
            self.assertEqual('instantperimeter', sensor200.group)
            self.assertEqual('Closed', sensor200.status)
            self.assertEqual('0', sensor200.state)
            self.assertEqual(200, sensor200.zone_id)
            self.assertEqual(1, sensor200.zone_physical_type)
            self.assertEqual(3, sensor200.zone_alarm_type)
            self.assertEqual(1, sensor200.zone_type)
            self.assertEqual(1, sensor200.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_2nd_door',
                sensor_unique_id='002_0000',
                sensor_state=sensor200,
                expected_device_class='door',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 210 is properly configured'):
            sensor210 = partition1.zone(210)
            self.assertEqual(QolsysSensorFreeze, sensor210.__class__)
            self.assertEqual('002-0010', sensor210.id)
            self.assertEqual('My Freeze Sensor', sensor210.name)
            self.assertEqual('freeze', sensor210.group)
            self.assertEqual('Closed', sensor210.status)
            self.assertEqual('0', sensor210.state)
            self.assertEqual(210, sensor210.zone_id)
            self.assertEqual(6, sensor210.zone_physical_type)
            self.assertEqual(0, sensor210.zone_alarm_type)
            self.assertEqual(17, sensor210.zone_type)
            self.assertEqual(1, sensor210.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_freeze_sensor',
                sensor_unique_id='002_0010',
                sensor_state=sensor210,
                expected_device_class='cold',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 220 is properly configured'):
            sensor220 = partition1.zone(220)
            self.assertEqual(QolsysSensorHeat, sensor220.__class__)
            self.assertEqual('002-0020', sensor220.id)
            self.assertEqual('My Heat Sensor', sensor220.name)
            self.assertEqual('smoke_heat', sensor220.group)
            self.assertEqual('Closed', sensor220.status)
            self.assertEqual('0', sensor220.state)
            self.assertEqual(220, sensor220.zone_id)
            self.assertEqual(10, sensor220.zone_physical_type)
            self.assertEqual(0, sensor220.zone_alarm_type)
            self.assertEqual(8, sensor220.zone_type)
            self.assertEqual(1, sensor220.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_heat_sensor',
                sensor_unique_id='002_0020',
                sensor_state=sensor220,
                expected_device_class='heat',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 230 is properly configured'):
            sensor230 = partition1.zone(230)
            self.assertEqual(QolsysSensorTilt, sensor230.__class__)
            self.assertEqual('002-0030', sensor230.id)
            self.assertEqual('My Tilt Sensor', sensor230.name)
            self.assertEqual('garageTilt1', sensor230.group)
            self.assertEqual('Closed', sensor230.status)
            self.assertEqual('0', sensor230.state)
            self.assertEqual(230, sensor230.zone_id)
            self.assertEqual(1, sensor230.zone_physical_type)
            self.assertEqual(3, sensor230.zone_alarm_type)
            self.assertEqual(16, sensor230.zone_type)
            self.assertEqual(1, sensor230.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_tilt_sensor',
                sensor_unique_id='002_0030',
                sensor_state=sensor230,
                expected_device_class='garage_door',
                expected_enabled_by_default=True,
            )

        with self.subTest(msg='Sensor 240 is properly configured'):
            sensor240 = partition1.zone(240)
            self.assertEqual(QolsysSensorKeypad, sensor240.__class__)
            self.assertEqual('002-0040', sensor240.id)
            self.assertEqual('My Keypad Sensor', sensor240.name)
            self.assertEqual('fixedintrusion', sensor240.group)
            self.assertEqual('Closed', sensor240.status)
            self.assertEqual('0', sensor240.state)
            self.assertEqual(240, sensor240.zone_id)
            self.assertEqual(4, sensor240.zone_physical_type)
            self.assertEqual(0, sensor240.zone_alarm_type)
            self.assertEqual(104, sensor240.zone_type)
            self.assertEqual(1, sensor240.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_keypad_sensor',
                sensor_unique_id='002_0040',
                sensor_state=sensor240,
                expected_device_class='safety',
                expected_enabled_by_default=False,
            )

        with self.subTest(msg='Sensor 250 is properly configured'):
            sensor250 = partition1.zone(250)
            self.assertEqual(QolsysSensorAuxiliaryPendant, sensor250.__class__)
            self.assertEqual('002-0050', sensor250.id)
            self.assertEqual('My Auxiliary Pendant Sensor', sensor250.name)
            self.assertEqual('fixedmedical', sensor250.group)
            self.assertEqual('Closed', sensor250.status)
            self.assertEqual('0', sensor250.state)
            self.assertEqual(250, sensor250.zone_id)
            self.assertEqual(1, sensor250.zone_physical_type)
            self.assertEqual(0, sensor250.zone_alarm_type)
            self.assertEqual(21, sensor250.zone_type)
            self.assertEqual(1, sensor250.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_auxiliary_pendant_sensor',
                sensor_unique_id='002_0050',
                sensor_state=sensor250,
                expected_device_class='safety',
                expected_enabled_by_default=False,
            )

        with self.subTest(msg='Sensor 260 is properly configured'):
            sensor260 = partition1.zone(260)
            self.assertEqual(QolsysSensorSiren, sensor260.__class__)
            self.assertEqual('002-0060', sensor260.id)
            self.assertEqual('My Siren Sensor', sensor260.name)
            self.assertEqual('Siren', sensor260.group)
            self.assertEqual('Closed', sensor260.status)
            self.assertEqual('0', sensor260.state)
            self.assertEqual(260, sensor260.zone_id)
            self.assertEqual(1, sensor260.zone_physical_type)
            self.assertEqual(3, sensor260.zone_alarm_type)
            self.assertEqual(14, sensor260.zone_type)
            self.assertEqual(1, sensor260.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_siren_sensor',
                sensor_unique_id='002_0060',
                sensor_state=sensor260,
                expected_device_class='safety',
                expected_enabled_by_default=False,
            )

        with self.subTest(msg='Sensor 270 is properly configured'):
            sensor270 = partition1.zone(270)
            self.assertEqual(QolsysSensorKeyFob, sensor270.__class__)
            self.assertEqual('002-0070', sensor270.id)
            self.assertEqual('My KeyFob Sensor', sensor270.name)
            self.assertEqual('mobileintrusion', sensor270.group)
            self.assertEqual('Closed', sensor270.status)
            self.assertEqual('0', sensor270.state)
            self.assertEqual(270, sensor270.zone_id)
            self.assertEqual(3, sensor270.zone_physical_type)
            self.assertEqual(0, sensor270.zone_alarm_type)
            self.assertEqual(102, sensor270.zone_type)
            self.assertEqual(1, sensor270.partition_id)

            await self._check_sensor_mqtt_messages(
                gw=gw,
                sensor_flat_name='my_keyfob_sensor',
                sensor_unique_id='002_0070',
                sensor_state=sensor270,
                expected_device_class='safety',
                expected_enabled_by_default=False,
            )

    async def _test_integration_event_info_secure_arm(self, from_secure_arm,
                                                      to_secure_arm):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            secure_arm=from_secure_arm,
            partition_ids=[0],
            zone_ids=[100],
        )

        event = {
            'event': 'INFO',
            'info_type': 'SECURE_ARM',
            'partition_id': 0,
            'value': to_secure_arm,
            'version': 1,
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        # Wait until the attributes publish is done
        attributes = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/alarm_control_panel/'
                              'qolsys_panel/partition0/attributes'},
        )

        if from_secure_arm != to_secure_arm:
            self.assertIsNotNone(attributes)
            self.assertJsonSubDictEqual({'secure_arm': to_secure_arm}, attributes['payload'])
        else:
            self.assertIsNone(attributes)

        self.assertEqual(to_secure_arm, gw._state.partition(0).secure_arm)

        self.assertTrue(panel.is_client_connected)

    async def test_integration_event_info_secure_arm_true_if_false(self):
        await self._test_integration_event_info_secure_arm(
            from_secure_arm=False,
            to_secure_arm=True,
        )

    async def test_integration_event_info_secure_arm_true_if_true(self):
        await self._test_integration_event_info_secure_arm(
            from_secure_arm=True,
            to_secure_arm=True,
        )

    async def test_integration_event_info_secure_arm_false_if_true(self):
        await self._test_integration_event_info_secure_arm(
            from_secure_arm=True,
            to_secure_arm=False,
        )

    async def test_integration_event_info_secure_arm_false_if_false(self):
        await self._test_integration_event_info_secure_arm(
            from_secure_arm=False,
            to_secure_arm=False,
        )

    async def _test_integration_event_zone_event_zone_active_tampered_while_closed(self):
        # Using a sensor that's already closed
        zone_id = 100
        entity_id = 'my_door'

        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[zone_id],
        )

        sensor = gw._state.partition(0).zone(zone_id)

        event_open = {
            'event': 'ZONE_EVENT',
            'zone_event_type': 'ZONE_ACTIVE',
            'version': 1,
            'zone': {
                'status': 'Open',
                'zone_id': zone_id,
            },
            'requestID': '<request_id>',
        }

        event_closed = deepcopy(event_open)
        event_closed['zone']['status'] = 'Closed'

        with self.subTest(msg='Sensor is open on first open message'):
            await panel.writeline(event_open)

            state = await gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': f'homeassistant/binary_sensor/'
                                  f'{entity_id}/state'},
                raise_on_timeout=True,
            )

            self.assertTrue(sensor.is_open)
            self.assertEqual('Open', state['payload'])

        with self.subTest(msg='Sensor is tampered on second open message'):
            await panel.writeline(event_open)

            attributes = await gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': f'homeassistant/binary_sensor/'
                                  f'{entity_id}/attributes'},
                raise_on_timeout=True,
            )

            self.assertTrue(sensor.tampered)
            self.assertJsonSubDictEqual({'tampered': True}, attributes['payload'])

        return SimpleNamespace(
            panel=panel,
            gw=gw,
            zone_id=zone_id,
            entity_id=entity_id,
            event_open=event_open,
            event_closed=event_closed,
            sensor=sensor,
        )

    async def test_integration_event_zone_event_zone_active_tampered_while_closed_to_closed(self):
        data = await self._test_integration_event_zone_event_zone_active_tampered_while_closed()

        with self.subTest(msg='Sensor is untampered on first closed message'):
            await data.panel.writeline(data.event_closed)

            attributes = await data.gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': f'homeassistant/binary_sensor/'
                                  f'{data.entity_id}/attributes'},
                raise_on_timeout=True,
            )

            self.assertFalse(data.sensor.tampered)
            self.assertJsonSubDictEqual({'tampered': False}, attributes['payload'])

        with self.subTest(msg='Sensor is closed on second closed message'):
            await data.panel.writeline(data.event_closed)

            state = await data.gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': f'homeassistant/binary_sensor/'
                                  f'{data.entity_id}/state'},
                raise_on_timeout=True,
            )

            self.assertTrue(data.sensor.is_closed)
            self.assertEqual('Closed', state['payload'])

    async def test_integration_event_zone_event_zone_active_tampered_while_closed_to_open(self):
        data = await self._test_integration_event_zone_event_zone_active_tampered_while_closed()

        with self.subTest(msg='Sensor is untampered when receiving open and close in the same second'):
            await data.panel.writeline(data.event_open)
            await data.panel.writeline(data.event_closed)

            attributes = await data.gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': f'homeassistant/binary_sensor/'
                                  f'{data.entity_id}/attributes'},
                raise_on_timeout=True,
            )

            self.assertFalse(data.sensor.tampered)
            self.assertJsonSubDictEqual({'tampered': False}, attributes['payload'])

        with self.subTest(msg='Sensor is not tampered when receiving open message next'):
            await data.panel.writeline(data.event_open)

            attributes = await data.gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': f'homeassistant/binary_sensor/'
                                  f'{data.entity_id}/attributes'},
            )

            self.assertTrue(data.sensor.is_open)
            self.assertIsNone(attributes)

    async def _test_integration_event_zone_event_zone_active_tampered_while_open(self):
        # Using a sensor that's already open
        zone_id = 101
        entity_id = 'my_window'

        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[zone_id],
        )

        sensor = gw._state.partition(0).zone(zone_id)

        event_open = {
            'event': 'ZONE_EVENT',
            'zone_event_type': 'ZONE_ACTIVE',
            'version': 1,
            'zone': {
                'status': 'Open',
                'zone_id': zone_id,
            },
            'requestID': '<request_id>',
        }

        event_closed = deepcopy(event_open)
        event_closed['zone']['status'] = 'Closed'

        with self.subTest(msg='Sensor is tampered on second open message'):
            with mock.patch('time.time', mock.MagicMock(return_value=42)):
                await panel.writeline(event_open)

                attributes = await gw.wait_for_next_mqtt_publish(
                    timeout=self._TIMEOUT,
                    filters={'topic': f'homeassistant/binary_sensor/'
                                      f'{entity_id}/attributes'},
                    raise_on_timeout=True,
                )

            self.assertTrue(sensor.tampered)
            self.assertEqual(42, sensor._last_open_tampered_at)
            self.assertJsonSubDictEqual({'tampered': True}, attributes['payload'])

        with self.subTest(msg='Sensor is untampered when receiving open and close in the same second'):
            await panel.writeline(event_open)
            await panel.writeline(event_closed)

            attributes = await gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': f'homeassistant/binary_sensor/'
                                  f'{entity_id}/attributes'},
                raise_on_timeout=True,
            )

            self.assertFalse(sensor.tampered)
            self.assertJsonSubDictEqual({'tampered': False}, attributes['payload'])

        return SimpleNamespace(
            panel=panel,
            gw=gw,
            zone_id=zone_id,
            entity_id=entity_id,
            event_open=event_open,
            event_closed=event_closed,
            sensor=sensor,
        )

    async def test_integration_event_zone_event_zone_active_tampered_while_open_to_open(self):
        data = await self._test_integration_event_zone_event_zone_active_tampered_while_open()

        with self.subTest(msg='Sensor is not tampered when receiving open message next'):
            await data.panel.writeline(data.event_open)

            attributes = await data.gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': f'homeassistant/binary_sensor/'
                                  f'{data.entity_id}/attributes'},
            )

            self.assertFalse(data.sensor.tampered)
            self.assertTrue(data.sensor.is_open)
            self.assertIsNone(attributes)

    async def test_integration_event_zone_event_zone_active_tampered_while_open_to_closed(self):
        data = await self._test_integration_event_zone_event_zone_active_tampered_while_open()

        with self.subTest(msg='Sensor is closed when receiving closed message next'):
            await data.panel.writeline(data.event_closed)

            state = await data.gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': f'homeassistant/binary_sensor/'
                                  f'{data.entity_id}/state'},
                raise_on_timeout=True,
            )

            self.assertFalse(data.sensor.tampered)
            self.assertTrue(data.sensor.is_closed)
            self.assertEqual('Closed', state['payload'])

    async def _test_integration_event_zone_event_zone_active(self, from_status, to_status):
        if from_status == 'Closed':
            zone_id = 100
            entity_id = 'my_door'
        else:
            zone_id = 101
            entity_id = 'my_window'

        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[zone_id],
        )

        event = {
            'event': 'ZONE_EVENT',
            'zone_event_type': 'ZONE_ACTIVE',
            'version': 1,
            'zone': {
                'status': to_status,
                'zone_id': zone_id,
            },
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        state = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': f'homeassistant/binary_sensor/'
                              f'{entity_id}/state'},
        )

        if from_status != to_status:
            self.assertIsNotNone(state)
            self.assertEqual(to_status, state['payload'])
        else:
            self.assertIsNone(state)

        self.assertEqual(
            to_status,
            gw._state.partition(0).zone(zone_id).status,
        )

        self.assertTrue(panel.is_client_connected)

    async def test_integration_event_zone_event_zone_active_open_if_closed(self):
        await self._test_integration_event_zone_event_zone_active(
            from_status='Closed',
            to_status='Open',
        )

    async def test_integration_event_zone_event_zone_active_open_if_open(self):
        await self._test_integration_event_zone_event_zone_active(
            from_status='Open',
            to_status='Open',
        )

    async def test_integration_event_zone_event_zone_active_closed_if_open(self):
        await self._test_integration_event_zone_event_zone_active(
            from_status='Open',
            to_status='Closed',
        )

    async def test_integration_event_zone_event_zone_active_closed_if_closed(self):
        await self._test_integration_event_zone_event_zone_active(
            from_status='Closed',
            to_status='Closed',
        )

    async def test_integration_event_zone_event_zone_active_unknown_zone(self):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[101],
        )

        event = {
            'event': 'ZONE_EVENT',
            'zone_event_type': 'ZONE_ACTIVE',
            'version': 1,
            'zone': {
                'status': 'Closed',
                'zone_id': 100,
            },
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        state = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_door/state'},
        )

        self.assertIsNone(state)

        self.assertTrue(panel.is_client_connected)

    async def test_integration_event_zone_event_zone_update_existing_zone(self):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0, 1],
            zone_ids=[100, 200],
        )

        event = {
            'event': 'ZONE_EVENT',
            'zone_event_type': 'ZONE_UPDATE',
            'zone': {
                'id': '001-0000',
                'type': 'Door_Window',
                'name': 'My Door',
                'group': 'entryexitdelay',
                'status': 'Open',
                'state': '1',
                'zone_id': 100,
                'zone_physical_type': 60,
                'zone_alarm_type': 61,
                'zone_type': 62,
                'partition_id': 1,
            },
            'version': 1,
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        state = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_door/state'},
        )

        attributes = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_door/attributes'},
            continued=True,
        )

        self.assertIsNotNone(state)
        self.assertIsNotNone(attributes)

        self.assertEqual('Open', state['payload'])
        self.assertJsonDictEqual(
            {
                'group': 'entryexitdelay',
                'state': '1',
                'zone_physical_type': 60,
                'zone_alarm_type': 61,
                'zone_type': 62,
                'tampered': False,
            },
            attributes['payload'],
        )

        state = gw._state

        partition0 = state.partition(0)
        self.assertEqual(0, len(partition0.sensors))

        partition1 = state.partition(1)
        self.assertEqual(2, len(partition1.sensors))

        sensor = partition1.zone(100)
        self.assertEqual('1', sensor.state)
        self.assertEqual(60, sensor.zone_physical_type)
        self.assertEqual(61, sensor.zone_alarm_type)
        self.assertEqual(62, sensor.zone_type)
        self.assertEqual(1, sensor.partition_id)

        self.assertTrue(panel.is_client_connected)

    async def test_integration_event_zone_event_zone_update_unknown_zone(self):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[101],
        )

        event = {
            'event': 'ZONE_EVENT',
            'zone_event_type': 'ZONE_UPDATE',
            'zone': {
                'id': '001-0000',
                'type': 'Door_Window',
                'name': 'My Door',
                'group': 'entryexitdelay',
                'status': 'Open',
                'state': '1',
                'zone_id': 100,
                'zone_physical_type': 60,
                'zone_alarm_type': 61,
                'zone_type': 62,
                'partition_id': 0,
            },
            'version': 1,
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        error = await gw.wait_for_next_log(
            timeout=self._TIMEOUT,
            filters={'level': 'ERROR'},
            match='Exception: Zone not found for zone update',
        )

        self.assertIsNotNone(error)

        self.assertTrue(panel.is_client_connected)

    async def test_integration_event_zone_event_zone_add(self):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[100],
        )

        event = {
            'event': 'ZONE_EVENT',
            'zone_event_type': 'ZONE_ADD',
            'zone': {
                'id': '001-0010',
                'type': 'Motion',
                'name': 'My Motion',
                'group': 'awayinstantmotion',
                'status': 'Closed',
                'state': '0',
                'zone_id': 110,
                'zone_physical_type': 2,
                'zone_alarm_type': 3,
                'zone_type': 2,
                'partition_id': 0,
            },
            'version': 1,
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        config = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_motion/config'},
        )

        availability = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_motion/availability'},
            continued=True,
        )

        state = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_motion/state'},
            continued=True,
        )

        attributes = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_motion/attributes'},
            continued=True,
        )

        with self.subTest(msg='Check MQTT config of new sensor'):
            self.assertIsNotNone(config)
            self.maxDiff = None
            self.assertJsonDictEqual(
                {
                    'name': 'My Motion',
                    'device_class': 'motion',
                    'enabled_by_default': True,
                    'state_topic': 'homeassistant/binary_sensor/'
                                   'my_motion/state',
                    'payload_on': 'Open',
                    'payload_off': 'Closed',
                    'availability_mode': 'all',
                    'availability': [
                        {
                            'topic': 'homeassistant/alarm_control_panel/'
                                     'qolsys_panel/availability',
                            'payload_available': 'online',
                            'payload_not_available': 'offline',
                        },
                        {
                            'topic': 'homeassistant/binary_sensor/'
                                     'my_motion/availability',
                            'payload_available': 'online',
                            'payload_not_available': 'offline',
                        },
                        {
                            'topic': 'appdaemon/birth_and_will',
                            'payload_available': 'online',
                            'payload_not_available': 'offline',
                        },
                    ],
                    'json_attributes_topic': 'homeassistant/binary_sensor/'
                                             'my_motion/attributes',
                    'unique_id': 'qolsys_panel_s001_0010',
                    'device': mock.ANY,
                },
                config['payload'],
            )

        with self.subTest(msg='Check MQTT availability of new sensor'):
            self.assertIsNotNone(availability)
            self.assertEqual('online', availability['payload'])

        with self.subTest(msg='Check MQTT state of new sensor'):
            self.assertIsNotNone(state)
            self.assertEqual('Closed', state['payload'])

        with self.subTest(msg='Check MQTT attributes of new sensor'):
            self.assertIsNotNone(attributes)
            self.assertJsonDictEqual(
                {
                    'group': 'awayinstantmotion',
                    'state': '0',
                    'zone_physical_type': 2,
                    'zone_alarm_type': 3,
                    'zone_type': 2,
                    'tampered': False,
                },
                attributes['payload'],
            )

        state = gw._state

        with self.subTest(msg='Partition 0 has the new sensor'):
            partition0 = state.partition(0)
            self.assertEqual(2, len(partition0.sensors))

        with self.subTest(msg='Sensor 110 is properly configured'):
            sensor110 = partition0.zone(110)
            self.assertEqual(QolsysSensorMotion, sensor110.__class__)
            self.assertEqual('001-0010', sensor110.id)
            self.assertEqual('My Motion', sensor110.name)
            self.assertEqual('awayinstantmotion', sensor110.group)
            self.assertEqual('Closed', sensor110.status)
            self.assertEqual('0', sensor110.state)
            self.assertEqual(110, sensor110.zone_id)
            self.assertEqual(2, sensor110.zone_physical_type)
            self.assertEqual(3, sensor110.zone_alarm_type)
            self.assertEqual(2, sensor110.zone_type)
            self.assertEqual(0, sensor110.partition_id)

        self.assertTrue(panel.is_client_connected)

    async def _test_integration_event_arming(self, from_status, to_status, ha_status=None):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[100],
            partition_status={
                0: from_status,
            },
        )

        event = {
            'event': 'ARMING',
            'arming_type': to_status,
            'partition_id': 0,
            'version': 1,
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        published_state = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/alarm_control_panel/'
                              'qolsys_panel/partition0/state'},
        )

        if from_status != to_status:
            self.assertIsNotNone(published_state)
            self.assertEqual(ha_status, published_state['payload'])
        else:
            self.assertIsNone(published_state)

        partition = gw._state.partition(0)
        self.assertEqual(to_status, partition.status)

        self.assertTrue(panel.is_client_connected)

    async def test_integration_event_arming_disarm_if_disarm(self):
        await self._test_integration_event_arming(
            from_status='DISARM',
            to_status='DISARM',
        )

    async def test_integration_event_arming_disarm_if_arm_stay(self):
        await self._test_integration_event_arming(
            from_status='ARM_STAY',
            to_status='DISARM',
            ha_status='disarmed',
        )

    async def test_integration_event_arming_disarm_if_arm_away(self):
        await self._test_integration_event_arming(
            from_status='ARM_AWAY',
            to_status='DISARM',
            ha_status='disarmed',
        )

    async def test_integration_event_arming_disarm_if_entry_delay(self):
        await self._test_integration_event_arming(
            from_status='ARM_AWAY',
            to_status='DISARM',
            ha_status='disarmed',
        )

    async def test_integration_event_arming_arm_stay_if_arm_stay(self):
        await self._test_integration_event_arming(
            from_status='ARM_STAY',
            to_status='ARM_STAY',
        )

    async def test_integration_event_arming_arm_stay_if_exit_delay(self):
        await self._test_integration_event_arming(
            from_status='EXIT_DELAY',
            to_status='ARM_STAY',
            ha_status='armed_home',
        )

    async def test_integration_event_arming_arm_stay_if_disarm(self):
        await self._test_integration_event_arming(
            from_status='DISARM',
            to_status='ARM_STAY',
            ha_status='armed_home',
        )

    async def test_integration_event_arming_arm_away_if_arm_away(self):
        await self._test_integration_event_arming(
            from_status='ARM_AWAY',
            to_status='ARM_AWAY',
        )

    async def test_integration_event_arming_arm_away_if_exit_delay(self):
        await self._test_integration_event_arming(
            from_status='EXIT_DELAY',
            to_status='ARM_AWAY',
            ha_status='armed_away',
        )

    async def test_integration_event_arming_arm_away_if_disarm(self):
        await self._test_integration_event_arming(
            from_status='DISARM',
            to_status='ARM_AWAY',
            ha_status='armed_away',
        )

    async def test_integration_event_arming_entry_delay_if_entry_delay(self):
        await self._test_integration_event_arming(
            from_status='ENTRY_DELAY',
            to_status='ENTRY_DELAY',
        )

    async def test_integration_event_arming_entry_delay_if_arm_away(self):
        await self._test_integration_event_arming(
            from_status='ARM_AWAY',
            to_status='ENTRY_DELAY',
            ha_status='pending',
        )

    async def test_integration_event_arming_entry_delay_if_arm_stay(self):
        await self._test_integration_event_arming(
            from_status='ARM_STAY',
            to_status='ENTRY_DELAY',
            ha_status='pending',
        )

    async def test_integration_event_arming_exit_delay_if_exit_delay(self):
        await self._test_integration_event_arming(
            from_status='EXIT_DELAY',
            to_status='EXIT_DELAY',
        )

    async def test_integration_event_arming_exit_delay_if_disarm(self):
        await self._test_integration_event_arming(
            from_status='DISARM',
            to_status='EXIT_DELAY',
            ha_status='arming',
        )

    async def test_integration_event_arming_arm_away_exit_delay_if_disarm(self):
        await self._test_integration_event_arming(
            from_status='DISARM',
            to_status='ARM-AWAY-EXIT-DELAY',
            ha_status='arming',
        )

    async def test_integration_event_arming_arm_stay_exit_delay_if_disarm(self):
        await self._test_integration_event_arming(
            from_status='DISARM',
            to_status='ARM-STAY-EXIT-DELAY',
            ha_status='arming',
        )

    async def _test_integration_event_alarm(self, alarm_type=''):
        panel, gw, _, _ = await self._ready_panel_and_gw()

        event = {
            'event': 'ALARM',
            'alarm_type': alarm_type,
            'partition_id': 0,
            'version': 1,
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        published_state = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/alarm_control_panel/'
                              'qolsys_panel/partition0/state'},
        )

        published_attrs = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/alarm_control_panel/'
                              'qolsys_panel/partition0/attributes'},
            continued=True,
        )

        self.assertIsNotNone(published_state)
        self.assertEqual('triggered', published_state['payload'])

        partition = gw._state.partition(0)
        self.assertEqual('ALARM', partition.status)

        if alarm_type:
            self.assertIsNotNone(published_attrs)
            self.assertJsonSubDictEqual(
                {'alarm_type': alarm_type},
                published_attrs['payload'],
            )

            self.assertEqual(alarm_type, partition.alarm_type)
        else:
            self.assertIsNone(published_attrs)
            self.assertIsNone(partition.alarm_type)

        self.assertTrue(panel.is_client_connected)

    async def test_integration_event_alarm_default(self):
        await self._test_integration_event_alarm(
            alarm_type='',
        )

    async def test_integration_event_alarm_police(self):
        await self._test_integration_event_alarm(
            alarm_type='POLICE',
        )

    async def test_integration_event_alarm_fire(self):
        await self._test_integration_event_alarm(
            alarm_type='FIRE',
        )

    async def test_integration_event_alarm_auxiliary(self):
        await self._test_integration_event_alarm(
            alarm_type='AUXILIARY',
        )

    async def _test_integration_event_error(self, error_type, error_desc,
                                            extra_expect=None, init_data=None):
        if init_data:
            panel = init_data.panel
            gw = init_data.gw
        else:
            panel, gw, _, _ = await self._ready_panel_and_gw(
                partition_ids=[0],
                zone_ids=[100],
                partition_status={
                    0: 'ARM_STAY',
                },
            )

        event = {
            'event': 'ERROR',
            'error_type': error_type,
            'partition_id': 0,
            'description': error_desc,
            'nonce': 'qolsys',
            'version': 1,
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        attributes = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/alarm_control_panel/'
                              'qolsys_panel/partition0/attributes'},
        )

        self.assertIsNotNone(attributes)

        expected = {
            'last_error_type': error_type,
            'last_error_desc': error_desc,
            'last_error_at': ISODATE,
        }
        if extra_expect:
            expected.update(extra_expect)
        self.assertJsonSubDictEqual(expected, attributes['payload'])

        return SimpleNamespace(
            panel=panel,
            gw=gw,
        )

    async def test_integration_event_error_usercode(self):
        await self._test_integration_event_error(
            error_type='usercode',
            error_desc='Please Enable Six Digit User Code or '
                       'KeyPad is already Locked',
        )

    async def test_integration_event_error_disarm_failed(self):
        with self.subTest(msg='Disarm failed error is handled properly'):
            init_data = await self._test_integration_event_error(
                error_type='DISARM_FAILED',
                error_desc='Invalid usercode',
                extra_expect={
                    'disarm_failed': 1,
                },
            )

        with self.subTest(msg='Other disarm failed error keeps raising the counter'):
            await self._test_integration_event_error(
                error_type='DISARM_FAILED',
                error_desc='Invalid usercode',
                extra_expect={
                    'disarm_failed': 2,
                },
                init_data=init_data,
            )

        with self.subTest(msg='Disarming the panel resets the counter'):
            panel = init_data.panel
            gw = init_data.gw

            self.assertEqual(2, gw._state.partition(0).disarm_failed)

            event = {
                'event': 'ARMING',
                'arming_type': 'DISARM',
                'partition_id': 0,
                'version': 1,
                'requestID': '<request_id>',
            }
            await panel.writeline(event)

            attributes = await gw.wait_for_next_mqtt_publish(
                timeout=self._TIMEOUT,
                filters={'topic': 'homeassistant/alarm_control_panel/'
                                  'qolsys_panel/partition0/attributes'},
            )

            self.assertIsNotNone(attributes)

            self.assertJsonSubDictEqual({'disarm_failed': 0}, attributes['payload'])
            self.assertEqual(0, gw._state.partition(0).disarm_failed)
