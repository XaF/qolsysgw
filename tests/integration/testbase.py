import unittest

import testenv  # noqa: F401
from mock_panel import PanelServer

from gateway import QolsysGateway
from qolsys.config import QolsysGatewayConfig


class TestQolsysGatewayBase(unittest.IsolatedAsyncioTestCase):

    _TIMEOUT = .1

    async def _init_panel_and_gw(self, **kwargs):
        # Start a panel panel
        panel = PanelServer()
        await panel.start()

        # Initialize a gateway instance to connect to that panel
        gw = QolsysGateway()
        gw.args = {
            'panel_host': 'localhost',
            'panel_port': panel.port,
        }

        for k, v in kwargs.items():
            if k in QolsysGatewayConfig._DEFAULT_CONFIG:
                if k not in gw.args:
                    gw.args[k] = v
                else:
                    raise AttributeError(f"Cannot redefine '{k}'")
            else:
                raise AttributeError(f"Unknown attribute '{k}'")

        if 'panel_token' not in gw.args:
            gw.args['panel_token'] = '<panel_token>'

        await gw.initialize()

        return panel, gw

    async def _init_panel_and_gw_and_wait(self, return_info=False, **kwargs):
        panel, gw = await self._init_panel_and_gw(**kwargs)

        if return_info:
            # Wait until the INFO message is received
            info = await panel.wait_for_next_message(
                timeout=self._TIMEOUT,
                filters={'action': 'INFO'},
            )

            return panel, gw, info

        # If we didn't want to return the info message, just
        # wait for the next message and raise on timeout
        await panel.wait_for_next_message(
            timeout=self._TIMEOUT,
            raise_on_timeout=True,
        )

        return panel, gw

    async def _ready_panel_and_gw(self, secure_arm=False, partition_ids=None,
                                  zone_ids=None, partition_status=None,
                                  **kwargs):
        panel, gw = await self._init_panel_and_gw_and_wait(**kwargs)

        if partition_status is None:
            partition_status = {}

        event = {
            'event': 'INFO',
            'info_type': 'SUMMARY',
            'partition_list': [
                {
                    'partition_id': 0,
                    'name': 'partition1',
                    'status': partition_status.get(0, 'DISARM'),
                    'secure_arm': secure_arm,
                    'zone_list': [
                        {
                            'id': '001-0000',
                            'type': 'Door_Window',
                            'name': 'My Door',
                            'group': 'entryexitdelay',
                            'status': 'Closed',
                            'state': '0',
                            'zone_id': 100,
                            'zone_physical_type': 1,
                            'zone_alarm_type': 3,
                            'zone_type': 1,
                            'partition_id': 0,
                        },
                        {
                            'id': '001-0001',
                            'type': 'Door_Window',
                            'name': 'My Window',
                            'group': 'entryexitlongdelay',
                            'status': 'Open',
                            'state': '0',
                            'zone_id': 101,
                            'zone_physical_type': 1,
                            'zone_alarm_type': 3,
                            'zone_type': 1,
                            'partition_id': 0,
                        },
                        {
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
                        {
                            'id': '001-0011',
                            'type': 'Panel Motion',
                            'name': 'Panel Motion',
                            'group': 'safetymotion',
                            'status': 'Closed',
                            'state': '0',
                            'zone_id': 111,
                            'zone_physical_type': 1,
                            'zone_alarm_type': 3,
                            'zone_type': 119,
                            'partition_id': 0,
                        },
                        {
                            'id': '001-0020',
                            'type': 'GlassBreak',
                            'name': 'My Glass Break',
                            'group': 'glassbreakawayonly',
                            'status': 'Closed',
                            'state': '0',
                            'zone_id': 120,
                            'zone_physical_type': 1,
                            'zone_alarm_type': 0,
                            'zone_type': 116,
                            'partition_id': 0,
                        },
                        {
                            'id': '001-0021',
                            'type': 'Panel Glass Break',
                            'name': 'Panel Glass Break',
                            'group': 'glassbreakawayonly',
                            'status': 'Closed',
                            'state': '0',
                            'zone_id': 121,
                            'zone_physical_type': 1,
                            'zone_alarm_type': 0,
                            'zone_type': 116,
                            'partition_id': 0,
                        },
                        {
                            'id': '001-0030',
                            'type': 'Bluetooth',
                            'name': 'My Phone',
                            'group': 'mobileintrusion',
                            'status': 'Closed',
                            'state': '0',
                            'zone_id': 130,
                            'zone_physical_type': 1,
                            'zone_alarm_type': 1,
                            'zone_type': 115,
                            'partition_id': 0,
                        },
                        {
                            'id': '001-0040',
                            'type': 'SmokeDetector',
                            'name': 'My Smoke Detector',
                            'group': 'smoke_heat',
                            'status': 'Closed',
                            'state': '0',
                            'zone_id': 140,
                            'zone_physical_type': 9,
                            'zone_alarm_type': 9,
                            'zone_type': 5,
                            'partition_id': 0,
                        },
                        {
                            'id': '001-0041',
                            'type': 'CODetector',
                            'name': 'My CO Detector',
                            'group': 'entryexitdelay',
                            'status': 'Closed',
                            'state': '0',
                            'zone_id': 141,
                            'zone_physical_type': 1,
                            'zone_alarm_type': 3,
                            'zone_type': 1,
                            'partition_id': 0,
                        },
                        {
                            'id': '001-0050',
                            'type': 'Water',
                            'name': 'My Water Detector',
                            'group': 'WaterSensor',
                            'status': 'Closed',
                            'state': '0',
                            'zone_id': 150,
                            'zone_physical_type': 8,
                            'zone_alarm_type': 0,
                            'zone_type': 15,
                            'partition_id': 0,
                        },
                    ],
                },
                {
                    'partition_id': 1,
                    'name': 'partition2',
                    'status': partition_status.get(1, 'DISARM'),
                    'secure_arm': secure_arm,
                    'zone_list': [
                        {
                            'id': '002-0000',
                            'type': 'Door_Window',
                            'name': 'My 2nd Door',
                            'group': 'instantperimeter',
                            'status': 'Closed',
                            'state': '0',
                            'zone_id': 200,
                            'zone_physical_type': 1,
                            'zone_alarm_type': 3,
                            'zone_type': 1,
                            'partition_id': 0,
                        },
                    ],
                },
            ],
            'nonce': 'qolsys',
            'requestID': '<request_id>',
        }

        if partition_ids is not None:
            event['partition_list'] = [
                p for p in event['partition_list']
                if p['partition_id'] in partition_ids
            ]

        if zone_ids is not None:
            for i, partition in enumerate(event['partition_list']):
                partition['zone_list'] = [
                    z for z in partition['zone_list']
                    if z['zone_id'] in zone_ids
                ]

        await panel.writeline(event)

        entity_ids = [
            z['name'].lower().replace(' ', '_')
            for p in event['partition_list']
            for z in p['zone_list']
        ]

        topics = [
            'config',
            'availability',
            'state',
            'attributes',
        ]

        # We need to wait for the whole side effects to finish happening,
        # before we can check the final result; we check that by waiting
        # for the last entity's last topic to be published
        last_topic = (f'homeassistant/binary_sensor/'
                      f'{entity_ids[-1]}/{topics[-1]}')
        await gw.wait_for_next_mqtt_publish(
            timeout=self._TIMEOUT,
            filters={'topic': last_topic},
        )

        return panel, gw, entity_ids, topics
