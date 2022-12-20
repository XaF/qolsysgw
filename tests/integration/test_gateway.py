import asyncio

import testenv  # noqa: F401
from testbase import TestQolsysGatewayBase

from gateway import QolsysGateway
from mqtt.exceptions import MqttPluginUnavailableException


class TestQolsysGateway(TestQolsysGatewayBase):

    async def test_gateway_raise_proper_error_if_mqtt_plugin_unavailable(self):
        # Initialize a gateway instance to connect to that panel
        gw = QolsysGateway()
        gw.args = {
            'panel_host': 'localhost',
            'panel_token': '<panel_token>',
        }

        # Override what will be returned as plugins
        gw.PLUGIN_CONFIG = None

        with self.assertRaises(MqttPluginUnavailableException):
            await gw.initialize()

    async def test_gateway_sends_info_message_on_connection(self):
        panel, gw, info = await self._init_panel_and_gw_and_wait(
            return_info=True,
        )

        # Make sure that we got the message, and not a timeout
        self.assertIsNotNone(info)

        self.assertTrue(panel.is_client_connected)

    async def test_gateway_stays_connected_on_non_json_data(self):
        panel, gw = await self._init_panel_and_gw_and_wait()

        await panel.writeline('blah')
        await asyncio.sleep(self._TIMEOUT)

        self.assertTrue(panel.is_client_connected)

    async def test_gateway_stays_connected_on_unknown_json_data(self):
        panel, gw = await self._init_panel_and_gw_and_wait()

        await panel.writeline({'not': 'expected'})
        await asyncio.sleep(self._TIMEOUT)

        self.assertTrue(panel.is_client_connected)

    async def test_gateway_stays_connected_on_unknown_event_type(self):
        panel, gw = await self._init_panel_and_gw_and_wait()

        await panel.writeline({'event': 'unknown'})
        await asyncio.sleep(self._TIMEOUT)

        self.assertTrue(panel.is_client_connected)
