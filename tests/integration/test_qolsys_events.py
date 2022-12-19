import json
import pytest

from unittest import mock

import testenv  # noqa: F401
from testbase import TestQolsysGatewayBase

from qolsys.sensors import QolsysSensorBluetooth
from qolsys.sensors import QolsysSensorCODetector
from qolsys.sensors import QolsysSensorDoorWindow
from qolsys.sensors import QolsysSensorGlassBreak
from qolsys.sensors import QolsysSensorMotion
from qolsys.sensors import QolsysSensorPanelGlassBreak
from qolsys.sensors import QolsysSensorPanelMotion
from qolsys.sensors import QolsysSensorSmokeDetector
from qolsys.sensors import QolsysSensorWater


class TestQolsysEvents(TestQolsysGatewayBase):

    async def test_event_info_summary_initializes_all_entities(self):
        panel, gw, entity_ids, topics = await self._ready_panel_and_gw()

        mqtt_publish_calls = []

        for topic in topics:
            mqtt_publish_calls.append(mock.call(
                (f'homeassistant/alarm_control_panel/'
                 f'qolsys_panel/partition1/{topic}'),
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
        self.assertEqual(2, len(state.partitions))

        # Check the partitions information
        partition0 = state.partition(0)
        self.assertEqual(10, len(partition0.sensors))
        self.assertEqual(0, partition0.id)
        self.assertEqual('partition1', partition0.name)
        self.assertEqual('DISARM', partition0.status)
        self.assertEqual(False, partition0.secure_arm)
        self.assertIsNone(partition0.alarm_type)

        partition1 = state.partition(1)
        self.assertEqual(1, len(partition1.sensors))
        self.assertEqual(1, partition1.id)
        self.assertEqual('partition2', partition1.name)
        self.assertEqual('DISARM', partition1.status)
        self.assertEqual(False, partition1.secure_arm)
        self.assertIsNone(partition1.alarm_type)

        # Check the sensors information
        sensor100 = partition0.zone(100)
        self.assertEqual(QolsysSensorDoorWindow, sensor100.__class__)
        self.assertEqual('001-0000', sensor100.id)
        self.assertEqual('My Door', sensor100.name)
        self.assertEqual('entryexitdelay', sensor100.group)
        self.assertEqual('Closed', sensor100.status)
        self.assertEqual('0', sensor100.state)
        self.assertEqual(100, sensor100.zone_id)
        self.assertEqual(1, sensor100.zone_type)
        self.assertEqual(1, sensor100.zone_physical_type)
        self.assertEqual(3, sensor100.zone_alarm_type)
        self.assertEqual(0, sensor100.partition_id)

        sensor101 = partition0.zone(101)
        self.assertEqual(QolsysSensorDoorWindow, sensor101.__class__)
        self.assertEqual('001-0001', sensor101.id)
        self.assertEqual('My Window', sensor101.name)
        self.assertEqual('entryexitdelay', sensor101.group)
        self.assertEqual('Open', sensor101.status)
        self.assertEqual('0', sensor101.state)
        self.assertEqual(101, sensor101.zone_id)
        self.assertEqual(1, sensor101.zone_type)
        self.assertEqual(1, sensor101.zone_physical_type)
        self.assertEqual(3, sensor101.zone_alarm_type)
        self.assertEqual(0, sensor101.partition_id)

        sensor110 = partition0.zone(110)
        self.assertEqual(QolsysSensorMotion, sensor110.__class__)
        self.assertEqual('001-0010', sensor110.id)
        self.assertEqual('My Motion', sensor110.name)
        self.assertEqual('awayinstantmotion', sensor110.group)
        self.assertEqual('Closed', sensor110.status)
        self.assertEqual('0', sensor110.state)
        self.assertEqual(110, sensor110.zone_id)
        self.assertEqual(1, sensor110.zone_type)
        self.assertEqual(1, sensor110.zone_physical_type)
        self.assertEqual(3, sensor110.zone_alarm_type)
        self.assertEqual(0, sensor110.partition_id)

        sensor111 = partition0.zone(111)
        self.assertEqual(QolsysSensorPanelMotion, sensor111.__class__)
        self.assertEqual('001-0011', sensor111.id)
        self.assertEqual('Panel Motion', sensor111.name)
        self.assertEqual('awayinstantmotion', sensor111.group)
        self.assertEqual('Closed', sensor111.status)
        self.assertEqual('0', sensor111.state)
        self.assertEqual(111, sensor111.zone_id)
        self.assertEqual(1, sensor111.zone_type)
        self.assertEqual(1, sensor111.zone_physical_type)
        self.assertEqual(3, sensor111.zone_alarm_type)
        self.assertEqual(0, sensor111.partition_id)

        sensor120 = partition0.zone(120)
        self.assertEqual(QolsysSensorGlassBreak, sensor120.__class__)
        self.assertEqual('001-0020', sensor120.id)
        self.assertEqual('My Glass Break', sensor120.name)
        self.assertEqual('entryexitdelay', sensor120.group)
        self.assertEqual('Closed', sensor120.status)
        self.assertEqual('0', sensor120.state)
        self.assertEqual(120, sensor120.zone_id)
        self.assertEqual(1, sensor120.zone_type)
        self.assertEqual(1, sensor120.zone_physical_type)
        self.assertEqual(3, sensor120.zone_alarm_type)
        self.assertEqual(0, sensor120.partition_id)

        sensor121 = partition0.zone(121)
        self.assertEqual(QolsysSensorPanelGlassBreak, sensor121.__class__)
        self.assertEqual('001-0021', sensor121.id)
        self.assertEqual('Panel Glass Break', sensor121.name)
        self.assertEqual('entryexitdelay', sensor121.group)
        self.assertEqual('Closed', sensor121.status)
        self.assertEqual('0', sensor121.state)
        self.assertEqual(121, sensor121.zone_id)
        self.assertEqual(1, sensor121.zone_type)
        self.assertEqual(1, sensor121.zone_physical_type)
        self.assertEqual(3, sensor121.zone_alarm_type)
        self.assertEqual(0, sensor121.partition_id)

        sensor130 = partition0.zone(130)
        self.assertEqual(QolsysSensorBluetooth, sensor130.__class__)
        self.assertEqual('001-0030', sensor130.id)
        self.assertEqual('My Phone', sensor130.name)
        self.assertEqual('entryexitdelay', sensor130.group)
        self.assertEqual('Closed', sensor130.status)
        self.assertEqual('0', sensor130.state)
        self.assertEqual(130, sensor130.zone_id)
        self.assertEqual(1, sensor130.zone_type)
        self.assertEqual(1, sensor130.zone_physical_type)
        self.assertEqual(3, sensor130.zone_alarm_type)
        self.assertEqual(0, sensor130.partition_id)

        sensor140 = partition0.zone(140)
        self.assertEqual(QolsysSensorSmokeDetector, sensor140.__class__)
        self.assertEqual('001-0040', sensor140.id)
        self.assertEqual('My Smoke Detector', sensor140.name)
        self.assertEqual('entryexitdelay', sensor140.group)
        self.assertEqual('Closed', sensor140.status)
        self.assertEqual('0', sensor140.state)
        self.assertEqual(140, sensor140.zone_id)
        self.assertEqual(1, sensor140.zone_type)
        self.assertEqual(1, sensor140.zone_physical_type)
        self.assertEqual(3, sensor140.zone_alarm_type)
        self.assertEqual(0, sensor140.partition_id)

        sensor141 = partition0.zone(141)
        self.assertEqual(QolsysSensorCODetector, sensor141.__class__)
        self.assertEqual('001-0041', sensor141.id)
        self.assertEqual('My CO Detector', sensor141.name)
        self.assertEqual('entryexitdelay', sensor141.group)
        self.assertEqual('Closed', sensor141.status)
        self.assertEqual('0', sensor141.state)
        self.assertEqual(141, sensor141.zone_id)
        self.assertEqual(1, sensor141.zone_type)
        self.assertEqual(1, sensor141.zone_physical_type)
        self.assertEqual(3, sensor141.zone_alarm_type)
        self.assertEqual(0, sensor141.partition_id)

        sensor150 = partition0.zone(150)
        self.assertEqual(QolsysSensorWater, sensor150.__class__)
        self.assertEqual('001-0050', sensor150.id)
        self.assertEqual('My Water Detector', sensor150.name)
        self.assertEqual('entryexitdelay', sensor150.group)
        self.assertEqual('Closed', sensor150.status)
        self.assertEqual('0', sensor150.state)
        self.assertEqual(150, sensor150.zone_id)
        self.assertEqual(1, sensor150.zone_type)
        self.assertEqual(1, sensor150.zone_physical_type)
        self.assertEqual(3, sensor150.zone_alarm_type)
        self.assertEqual(0, sensor150.partition_id)

        sensor200 = partition1.zone(200)
        self.assertEqual(QolsysSensorDoorWindow, sensor200.__class__)
        self.assertEqual('002-0000', sensor200.id)
        self.assertEqual('My 2nd Door', sensor200.name)
        self.assertEqual('entryexitdelay', sensor200.group)
        self.assertEqual('Closed', sensor200.status)
        self.assertEqual('0', sensor200.state)
        self.assertEqual(200, sensor200.zone_id)
        self.assertEqual(1, sensor200.zone_type)
        self.assertEqual(1, sensor200.zone_physical_type)
        self.assertEqual(3, sensor200.zone_alarm_type)
        self.assertEqual(0, sensor200.partition_id)

    async def _test_event_info_secure_arm(self, from_secure_arm,
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
                              'qolsys_panel/partition1/attributes'},
        )

        if from_secure_arm != to_secure_arm:
            self.assertIsNotNone(attributes)

            self.assertDictEqual(
                {'secure_arm': to_secure_arm, 'alarm_type': None},
                json.loads(attributes['payload']),
            )
        else:
            self.assertIsNone(attributes)

        self.assertEqual(to_secure_arm, gw._state.partition(0).secure_arm)

        self.assertTrue(panel.is_client_connected)

    async def test_event_info_secure_arm_true_if_false(self):
        await self._test_event_info_secure_arm(
            from_secure_arm=False,
            to_secure_arm=True,
        )

    async def test_event_info_secure_arm_true_if_true(self):
        await self._test_event_info_secure_arm(
            from_secure_arm=True,
            to_secure_arm=True,
        )

    async def test_event_info_secure_arm_false_if_true(self):
        await self._test_event_info_secure_arm(
            from_secure_arm=True,
            to_secure_arm=False,
        )

    async def test_event_info_secure_arm_false_if_false(self):
        await self._test_event_info_secure_arm(
            from_secure_arm=False,
            to_secure_arm=False,
        )

    async def _test_event_zone_event_zone_active(self, from_status, to_status):
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

    async def test_event_zone_event_zone_active_open_if_closed(self):
        await self._test_event_zone_event_zone_active(
            from_status='Closed',
            to_status='Open',
        )

    async def test_event_zone_event_zone_active_open_if_open(self):
        await self._test_event_zone_event_zone_active(
            from_status='Open',
            to_status='Open',
        )

    async def test_event_zone_event_zone_active_closed_if_open(self):
        await self._test_event_zone_event_zone_active(
            from_status='Open',
            to_status='Closed',
        )

    async def test_event_zone_event_zone_active_closed_if_closed(self):
        await self._test_event_zone_event_zone_active(
            from_status='Closed',
            to_status='Closed',
        )

    async def test_event_zone_event_zone_active_unknown_zone(self):
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

    async def test_event_zone_event_zone_update_existing_zone(self):
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

        state, pos = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_door/state'},
            returnpos=True,
        )

        attributes = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_door/attributes'},
            startpos=pos,
        )

        self.assertIsNotNone(state)
        self.assertIsNotNone(attributes)

        self.assertEqual('Open', state['payload'])
        self.assertDictEqual(
            {
                'group': 'entryexitdelay',
                'state': '1',
                'zone_physical_type': 60,
                'zone_alarm_type': 61,
                'zone_type': 62,
            },
            json.loads(attributes['payload']),
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

    async def test_event_zone_event_zone_update_unknown_zone(self):
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

    @pytest.mark.skip(reason='ZONE_EVENT ZONE_ADD not yet supported')
    async def test_event_zone_event_zone_add(self):
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
                'zone_physical_type': 1,
                'zone_alarm_type': 3,
                'zone_type': 1,
                'partition_id': 0,
            },
            'version': 1,
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        state, pos = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_motion/state'},
            returnpos=True,
        )

        attributes = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/binary_sensor/'
                              'my_motion/attributes'},
            startpos=pos,
        )

        self.assertIsNotNone(state)
        self.assertIsNotNone(attributes)

        self.assertEqual('Closed', state['payload'])
        self.assertDictEqual(
            {
                'group': 'awayinstantmotion',
                'state': '0',
                'zone_physical_type': 1,
                'zone_alarm_type': 3,
                'zone_type': 1,
            },
            json.loads(attributes['payload']),
        )

        state = gw._state

        partition0 = state.partition(0)
        self.assertEqual(2, len(partition0.sensors))

        sensor110 = partition0.zone(110)
        self.assertEqual(QolsysSensorMotion, sensor110.__class__)
        self.assertEqual('001-0010', sensor110.id)
        self.assertEqual('My Motion', sensor110.name)
        self.assertEqual('awayinstantmotion', sensor110.group)
        self.assertEqual('Closed', sensor110.status)
        self.assertEqual('0', sensor110.state)
        self.assertEqual(110, sensor110.zone_id)
        self.assertEqual(1, sensor110.zone_type)
        self.assertEqual(1, sensor110.zone_physical_type)
        self.assertEqual(3, sensor110.zone_alarm_type)
        self.assertEqual(0, sensor110.partition_id)

        self.assertTrue(panel.is_client_connected)

    async def _test_event_arming(self, from_status, to_status, ha_status=None):
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
                              'qolsys_panel/partition1/state'},
        )

        if from_status != to_status:
            self.assertIsNotNone(published_state)
            self.assertEqual(ha_status, published_state['payload'])
        else:
            self.assertIsNone(published_state)

        partition = gw._state.partition(0)
        self.assertEqual(to_status, partition.status)

        self.assertTrue(panel.is_client_connected)

    async def test_event_arming_disarm_if_disarm(self):
        await self._test_event_arming(
            from_status='DISARM',
            to_status='DISARM',
        )

    async def test_event_arming_disarm_if_arm_stay(self):
        await self._test_event_arming(
            from_status='ARM_STAY',
            to_status='DISARM',
            ha_status='disarmed',
        )

    async def test_event_arming_disarm_if_arm_away(self):
        await self._test_event_arming(
            from_status='ARM_AWAY',
            to_status='DISARM',
            ha_status='disarmed',
        )

    async def test_event_arming_disarm_if_entry_delay(self):
        await self._test_event_arming(
            from_status='ARM_AWAY',
            to_status='DISARM',
            ha_status='disarmed',
        )

    async def test_event_arming_arm_stay_if_arm_stay(self):
        await self._test_event_arming(
            from_status='ARM_STAY',
            to_status='ARM_STAY',
        )

    async def test_event_arming_arm_stay_if_exit_delay(self):
        await self._test_event_arming(
            from_status='EXIT_DELAY',
            to_status='ARM_STAY',
            ha_status='armed_home',
        )

    async def test_event_arming_arm_stay_if_disarm(self):
        await self._test_event_arming(
            from_status='DISARM',
            to_status='ARM_STAY',
            ha_status='armed_home',
        )

    async def test_event_arming_arm_away_if_arm_away(self):
        await self._test_event_arming(
            from_status='ARM_AWAY',
            to_status='ARM_AWAY',
        )

    async def test_event_arming_arm_away_if_exit_delay(self):
        await self._test_event_arming(
            from_status='EXIT_DELAY',
            to_status='ARM_AWAY',
            ha_status='armed_away',
        )

    async def test_event_arming_arm_away_if_disarm(self):
        await self._test_event_arming(
            from_status='DISARM',
            to_status='ARM_AWAY',
            ha_status='armed_away',
        )

    async def test_event_arming_entry_delay_if_entry_delay(self):
        await self._test_event_arming(
            from_status='ENTRY_DELAY',
            to_status='ENTRY_DELAY',
        )

    async def test_event_arming_entry_delay_if_arm_away(self):
        await self._test_event_arming(
            from_status='ARM_AWAY',
            to_status='ENTRY_DELAY',
            ha_status='pending',
        )

    async def test_event_arming_entry_delay_if_arm_stay(self):
        await self._test_event_arming(
            from_status='ARM_STAY',
            to_status='ENTRY_DELAY',
            ha_status='pending',
        )

    async def test_event_arming_exit_delay_if_exit_delay(self):
        await self._test_event_arming(
            from_status='EXIT_DELAY',
            to_status='EXIT_DELAY',
        )

    async def test_event_arming_exit_delay_if_disarm(self):
        await self._test_event_arming(
            from_status='DISARM',
            to_status='EXIT_DELAY',
            ha_status='arming',
        )

    async def test_event_arming_arm_away_exit_delay_if_disarm(self):
        await self._test_event_arming(
            from_status='DISARM',
            to_status='ARM-AWAY-EXIT-DELAY',
            ha_status='arming',
        )

    async def _test_event_alarm(self, alarm_type=''):
        panel, gw, _, _ = await self._ready_panel_and_gw()

        event = {
            'event': 'ALARM',
            'alarm_type': alarm_type,
            'partition_id': 0,
            'version': 1,
            'requestID': '<request_id>',
        }
        await panel.writeline(event)

        published_state, pos = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/alarm_control_panel/'
                              'qolsys_panel/partition1/state'},
            returnpos=True,
        )

        published_attrs = await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': 'homeassistant/alarm_control_panel/'
                              'qolsys_panel/partition1/attributes'},
            startpos=pos,
        )

        self.assertIsNotNone(published_state)
        self.assertEqual('triggered', published_state['payload'])

        partition = gw._state.partition(0)
        self.assertEqual('ALARM', partition.status)

        if alarm_type:
            self.assertIsNotNone(published_attrs)
            self.assertEqual(
                alarm_type,
                json.loads(published_attrs['payload'])['alarm_type'],
            )

            self.assertEqual(alarm_type, partition.alarm_type)
        else:
            self.assertIsNone(published_attrs)
            self.assertIsNone(partition.alarm_type)

        self.assertTrue(panel.is_client_connected)

    async def test_event_alarm_default(self):
        await self._test_event_alarm(
            alarm_type='',
        )

    async def test_event_alarm_police(self):
        await self._test_event_alarm(
            alarm_type='POLICE',
        )

    async def test_event_alarm_fire(self):
        await self._test_event_alarm(
            alarm_type='FIRE',
        )

    async def test_event_alarm_auxiliary(self):
        await self._test_event_alarm(
            alarm_type='AUXILIARY',
        )
