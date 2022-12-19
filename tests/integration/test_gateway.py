import asyncio

import testenv  # noqa: F401
from testbase import TestQolsysGatewayBase


class TestQolsysGateway(TestQolsysGatewayBase):

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
