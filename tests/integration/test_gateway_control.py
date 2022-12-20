import json

import testenv  # noqa: F401
from testbase import TestQolsysGatewayBase


class TestQolsysGatewayControl(TestQolsysGatewayBase):

    async def test_control_with_wrong_session_token(self):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[100],
        )

        control = {
            'action': 'DISARM',
            'partition_id': 0,
            'session_token': 'this is not the session token',
        }

        gw.mqtt_publish(
            'homeassistant/alarm_control_panel/qolsys_panel/set',
            json.dumps(control),
            namespace='mqtt',
        )

        error = await gw.wait_for_next_log(
            timeout=self._TIMEOUT,
            filters={'level': 'ERROR'},
            match='^invalid session token',
        )

        self.assertIsNotNone(error)

    async def _test_control_arming(self, control_action, partition_status,
                                   arming_type, send_code=False,
                                   expect_error=None, expect_delay=None,
                                   secure_arm=False, panel_user_code=None,
                                   user_control_token=None,
                                   **kwargs):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[100],
            partition_status={
                0: partition_status,
            },
            secure_arm=secure_arm,
            panel_user_code=panel_user_code,
            user_control_token=user_control_token,
            **kwargs,
        )

        session_token = user_control_token or gw._session_token

        control = {
            'action': control_action,
            'partition_id': 0,
            'session_token': session_token,
        }
        if send_code:
            control['code'] = '4242'

        gw.mqtt_publish(
            'homeassistant/alarm_control_panel/qolsys_panel/set',
            json.dumps(control),
            namespace='mqtt',
        )

        if expect_error:
            error = await gw.wait_for_next_log(
                timeout=self._TIMEOUT,
                filters={'level': 'ERROR'},
                match=expect_error,
            )

            self.assertIsNotNone(error)
        else:
            action = await panel.wait_for_next_message(
                timeout=self._TIMEOUT,
                filters={'action': 'ARMING'},
            )

            self.assertIsNotNone(action)
            self.assertEqual(arming_type, action['arming_type'])
            self.assertEqual(0, action['partition_id'])
            self.assertEqual(gw.args['panel_token'], action['token'])

            if expect_delay is not None:
                self.assertEqual(expect_delay, action.get('delay'))
            else:
                _SENTINEL = object()
                self.assertEqual(_SENTINEL, action.get('delay', _SENTINEL))

            if send_code:
                self.assertEqual('4242', action['usercode'])
            elif panel_user_code:
                self.assertEqual(panel_user_code, action['usercode'])

    async def test_control_disarm(self):
        await self._test_control_arming(
            control_action='DISARM',
            partition_status='ARM_AWAY',
            arming_type='DISARM',
            send_code=True,
        )

    async def test_control_disarm_without_code(self):
        await self._test_control_arming(
            control_action='DISARM',
            partition_status='ARM_AWAY',
            arming_type='DISARM',
            expect_error='^Cannot perform action without '
                         'a configured panel code',
        )

    async def test_control_disarm_with_panel_code(self):
        await self._test_control_arming(
            control_action='DISARM',
            partition_status='ARM_AWAY',
            arming_type='DISARM',
            panel_user_code='1337',
        )

    async def test_control_disarm_with_panel_code_and_user_control_token(self):
        await self._test_control_arming(
            control_action='DISARM',
            partition_status='ARM_AWAY',
            arming_type='DISARM',
            panel_user_code='1337',
            user_control_token='My$ecr3tT0k3n!',
        )

    async def test_control_disarm_if_code_disarm_required_and_ha_check_code(self):
        await self._test_control_arming(
            control_action='DISARM',
            partition_status='ARM_AWAY',
            arming_type='DISARM',
            panel_user_code='1337',
            code_disarm_required=True,
            ha_check_user_code=True,
        )

    async def test_control_disarm_with_wrong_code_if_code_disarm_required(self):
        await self._test_control_arming(
            control_action='DISARM',
            partition_status='ARM_AWAY',
            arming_type='DISARM',
            panel_user_code='1337',
            code_disarm_required=True,
            ha_check_user_code=False,
            send_code=True,
            expect_error='^Code received in the control command invalid',
        )

    async def test_control_arm_away(self):
        await self._test_control_arming(
            control_action='ARM_AWAY',
            partition_status='DISARM',
            arming_type='ARM_AWAY',
        )

    async def test_control_arm_away_with_exit_delay(self):
        await self._test_control_arming(
            control_action='ARM_AWAY',
            partition_status='DISARM',
            arming_type='ARM_AWAY',
            arm_away_exit_delay=30,
            expect_delay=30,
        )

    async def test_control_arm_away_secure_arm_with_code(self):
        await self._test_control_arming(
            secure_arm=True,
            control_action='ARM_AWAY',
            partition_status='DISARM',
            arming_type='ARM_AWAY',
            send_code=True,
        )

    async def test_control_arm_away_secure_arm_with_panel_code(self):
        await self._test_control_arming(
            secure_arm=True,
            control_action='ARM_AWAY',
            partition_status='DISARM',
            arming_type='ARM_AWAY',
            panel_user_code='1337',
        )

    async def test_control_arm_away_with_panel_code_if_code_arm_required_and_ha_check_code(self):
        await self._test_control_arming(
            control_action='ARM_AWAY',
            partition_status='DISARM',
            arming_type='ARM_AWAY',
            panel_user_code='1337',
            code_arm_required=True,
            ha_check_user_code=True,
        )

    async def test_control_arm_away_with_panel_code_and_wrong_code_if_code_arm_required(self):
        await self._test_control_arming(
            control_action='ARM_AWAY',
            partition_status='DISARM',
            arming_type='ARM_AWAY',
            panel_user_code='1337',
            code_arm_required=True,
            ha_check_user_code=False,
            send_code=True,
            expect_error='^Code received in the control command invalid',
        )

    async def test_control_arm_away_secure_arm_without_code(self):
        await self._test_control_arming(
            secure_arm=True,
            control_action='ARM_AWAY',
            partition_status='DISARM',
            arming_type='ARM_AWAY',
            expect_error='^Cannot perform action without '
                         'a configured panel code',
        )

    async def test_control_arm_vacation(self):
        await self._test_control_arming(
            control_action='ARM_VACATION',
            partition_status='DISARM',
            arming_type='ARM_AWAY',
        )

    async def test_control_arm_home(self):
        await self._test_control_arming(
            control_action='ARM_HOME',
            partition_status='DISARM',
            arming_type='ARM_STAY',
        )

    async def test_control_arm_home_with_exit_delay(self):
        await self._test_control_arming(
            control_action='ARM_HOME',
            partition_status='DISARM',
            arming_type='ARM_STAY',
            arm_stay_exit_delay=42,
            expect_delay=42,
        )

    async def test_control_arm_home_secure_arm_with_code(self):
        await self._test_control_arming(
            secure_arm=True,
            control_action='ARM_HOME',
            partition_status='DISARM',
            arming_type='ARM_STAY',
            send_code=True,
        )

    async def test_control_arm_home_secure_arm_with_panel_code(self):
        await self._test_control_arming(
            secure_arm=True,
            control_action='ARM_HOME',
            partition_status='DISARM',
            arming_type='ARM_STAY',
            panel_user_code='1337',
        )

    async def test_control_arm_home_secure_arm_without_code(self):
        await self._test_control_arming(
            secure_arm=True,
            control_action='ARM_HOME',
            partition_status='DISARM',
            arming_type='ARM_STAY',
            expect_error='^Cannot perform action without '
                         'a configured panel code',
        )

    async def test_control_arm_night(self):
        await self._test_control_arming(
            control_action='ARM_NIGHT',
            partition_status='DISARM',
            arming_type='ARM_STAY',
        )

    async def _test_control_trigger(self, control_action, alarm_type,
                                    send_code=False, expect_error=None,
                                    **kwargs):
        panel, gw, _, _ = await self._ready_panel_and_gw(
            partition_ids=[0],
            zone_ids=[100],
            **kwargs,
        )

        session_token = gw._session_token

        control = {
            'action': control_action,
            'partition_id': 0,
            'session_token': session_token,
        }
        if send_code:
            control['code'] = '4242'

        gw.mqtt_publish(
            'homeassistant/alarm_control_panel/qolsys_panel/set',
            json.dumps(control),
            namespace='mqtt',
        )

        if expect_error:
            error = await gw.wait_for_next_log(
                timeout=self._TIMEOUT,
                filters={'level': 'ERROR'},
                match=expect_error,
            )

            self.assertIsNotNone(error)
        else:
            action = await panel.wait_for_next_message(
                timeout=self._TIMEOUT,
                filters={'action': 'ALARM'},
            )

            self.assertIsNotNone(action)
            self.assertEqual(alarm_type, action['alarm_type'])
            self.assertEqual(0, action['partition_id'])
            self.assertEqual(gw.args['panel_token'], action['token'])

    async def test_control_trigger_default(self):
        await self._test_control_trigger(
            control_action='TRIGGER',
            alarm_type='POLICE',
        )

    async def test_control_trigger_if_code_trigger_required_and_ha_check_code(self):
        await self._test_control_trigger(
            control_action='TRIGGER',
            alarm_type='POLICE',
            code_trigger_required=True,
            ha_check_user_code=True,
            panel_user_code='1337',
        )

    async def test_control_trigger_with_wrong_code_if_code_trigger_required(self):
        await self._test_control_trigger(
            control_action='TRIGGER',
            alarm_type='POLICE',
            code_trigger_required=True,
            ha_check_user_code=False,
            panel_user_code='1337',
            send_code=True,
            expect_error='^Code received in the control command invalid'
        )

    async def test_control_trigger_police(self):
        await self._test_control_trigger(
            control_action='TRIGGER_POLICE',
            alarm_type='POLICE',
        )

    async def test_control_trigger_fire(self):
        await self._test_control_trigger(
            control_action='TRIGGER_FIRE',
            alarm_type='FIRE',
        )

    async def test_control_trigger_auxiliary(self):
        await self._test_control_trigger(
            control_action='TRIGGER_AUXILIARY',
            alarm_type='AUXILIARY',
        )
