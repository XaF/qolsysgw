import json

import testenv  # noqa: F401
from testbase import TestQolsysGatewayBase


class TestIntegrationAlarmControlPanelConfig(TestQolsysGatewayBase):

    async def _test_config(self, payload_expect, **kwargs):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[10000],
            **kwargs,
        )

        config = await gw.find_last_mqtt_publish(
            filters={'topic': 'homeassistant/alarm_control_panel/'
                              'qolsys_panel/partition0/config'},
            raise_if_not_found=True,
        )

        payload = json.loads(config['payload'])

        self.assertEqual(payload_expect['code_disarm_required'],
                         payload['code_disarm_required'])
        self.assertEqual(payload_expect['code_arm_required'],
                         payload['code_arm_required'])
        self.assertEqual(payload_expect['code_trigger_required'],
                         payload['code_trigger_required'])

        if payload_expect['code'] is None:
            _SENTINEL = object()
            self.assertEqual(_SENTINEL, payload.get('code', _SENTINEL))
        else:
            self.assertEqual(payload_expect['code'], payload['code'])

        expected_command_template = {
            'partition_id': '0',
            'action': '{{ action }}',
            'session_token': gw._session_token,
        }
        if payload_expect['command_template_code']:
            expected_command_template['code'] = '{{ code }}'

        self.assertJsonDictEqual(expected_command_template, payload['command_template'])

    async def test_integration_config_default(self):
        await self._test_config(
            payload_expect={
                'code': 'REMOTE_CODE',
                'code_disarm_required': True,
                'code_arm_required': False,
                'code_trigger_required': False,
                'command_template_code': True,
            },
        )

    async def test_integration_config_with_panel_code(self):
        await self._test_config(
            payload_expect={
                'code': None,
                'code_disarm_required': False,
                'code_arm_required': False,
                'code_trigger_required': False,
                'command_template_code': False,
            },

            panel_user_code=1337,
        )

    async def test_integration_config_code_required_remote_check_num(self):
        await self._test_config(
            payload_expect={
                'code': 'REMOTE_CODE',
                'code_disarm_required': True,
                'code_arm_required': True,
                'code_trigger_required': True,
                'command_template_code': True,
            },

            panel_user_code=1337,
            code_disarm_required=True,
            code_arm_required=True,
            code_trigger_required=True,
            ha_check_user_code=False,
        )

    async def test_integration_config_code_required_remote_check_alnum(self):
        await self._test_config(
            payload_expect={
                'code': 'REMOTE_CODE_TEXT',
                'code_disarm_required': True,
                'code_arm_required': True,
                'code_trigger_required': True,
                'command_template_code': True,
            },

            panel_user_code='hello1337',
            code_disarm_required=True,
            code_arm_required=True,
            code_trigger_required=True,
            ha_check_user_code=False,
        )

    async def test_integration_config_code_required_ha_check_user_code(self):
        await self._test_config(
            payload_expect={
                'code': '1337',
                'code_disarm_required': True,
                'code_arm_required': True,
                'code_trigger_required': True,
                'command_template_code': False,
            },

            panel_user_code=1337,
            code_disarm_required=True,
            code_arm_required=True,
            code_trigger_required=True,
            ha_check_user_code=True,
        )

    async def test_integration_config_code_required_ha_user_code_with_ha_check(self):
        await self._test_config(
            payload_expect={
                'code': 'topsecret',
                'code_disarm_required': True,
                'code_arm_required': True,
                'code_trigger_required': True,
                'command_template_code': False,
            },

            panel_user_code=1337,
            code_disarm_required=True,
            code_arm_required=True,
            code_trigger_required=True,
            ha_check_user_code=True,
            ha_user_code='topsecret',
        )

    async def test_integration_config_code_required_ha_user_code_with_remote_check(self):
        await self._test_config(
            payload_expect={
                'code': 'REMOTE_CODE_TEXT',
                'code_disarm_required': True,
                'code_arm_required': True,
                'code_trigger_required': True,
                'command_template_code': True,
            },

            panel_user_code=1337,
            code_disarm_required=True,
            code_arm_required=True,
            code_trigger_required=True,
            ha_check_user_code=False,
            ha_user_code='topsecret',
        )
