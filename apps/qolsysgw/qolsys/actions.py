import json
import logging


LOGGER = logging.getLogger(__name__)


class QolsysAction(object):

    _PARAMS_TO_REDACT = []

    _DEFAULT_DATA = {
        'nonce': 'qolsys',
        'source': 'C4',
        'version': 0,
    }

    @property
    def data(self) -> dict:
        return {**self._DEFAULT_DATA, **self._data}

    @property
    def redacted(self) -> str:
        return json.dumps({
            **{k: '<redacted>' if k in self._PARAMS_TO_REDACT else v
               for k, v in self.data.items()},
            'token': '<redacted>'
        })

    def with_token(self, token) -> str:
        return json.dumps({**self.data, 'token': token})

    def __str__(self) -> str:
        return json.dumps(self.data)


class QolsysActionInfo(QolsysAction):
    def __init__(self) -> None:
        self._data = {
            'action': 'INFO',
            'info_type': 'SUMMARY',
        }


class QolsysActionArm(QolsysAction):

    ARMING_TYPE_DISARM = 'DISARM'
    ARMING_TYPE_ARM_AWAY = 'ARM_AWAY'
    ARMING_TYPE_ARM_STAY = 'ARM_STAY'

    _PARAMS_TO_REDACT = ['usercode']

    def __init__(self, arm_type: str, partition_id: int,
                 panel_code: str=None) -> None:
        self._data = {
            'action': 'ARMING',
            'arming_type': arm_type,
            'partition_id': partition_id,
        }

        if panel_code:
            self._data['usercode'] = str(panel_code)


class QolsysActionDisarm(QolsysActionArm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(arm_type=QolsysActionArm.ARMING_TYPE_DISARM,
                         *args, **kwargs)


class QolsysActionArmAway(QolsysActionArm):
    def __init__(self, delay: int=None, *args, **kwargs) -> None:
        super().__init__(arm_type=QolsysActionArm.ARMING_TYPE_ARM_AWAY,
                         *args, **kwargs)

        if delay is not None and delay >= 0:
            self._data['delay'] = delay


class QolsysActionArmStay(QolsysActionArm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(arm_type=QolsysActionArm.ARMING_TYPE_ARM_STAY,
                         *args, **kwargs)


class QolsysActionTrigger(QolsysAction):
    ALARM_TYPE_POLICE = 'POLICE'
    ALARM_TYPE_FIRE = 'FIRE'
    ALARM_TYPE_AUXILIARY = 'AUXILIARY'

    def __init__(self, partition_id: int, alarm_type: str=None) -> None:
        self._data = {
            'action': 'ALARM',
            'alarm_type': alarm_type or self.ALARM_TYPE_POLICE,
            'partition_id': partition_id,
        }
