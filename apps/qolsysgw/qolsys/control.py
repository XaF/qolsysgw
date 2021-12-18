import json
import logging

from qolsys.actions import QolsysActionArmAway
from qolsys.actions import QolsysActionArmStay
from qolsys.actions import QolsysActionDisarm
from qolsys.actions import QolsysActionTrigger
from qolsys.exceptions import UnknownQolsysControlException
from qolsys.exceptions import MissingDisarmCodeException
from qolsys.exceptions import InvalidArmDisarmCodeException
from qolsys.utils import find_subclass


LOGGER = logging.getLogger(__name__)


class QolsysControl(object):

    __SUBCLASSES_CACHE = {}

    def __init__(self, raw: dict, partition_id: int, code: str=None,
                 session_token: str=None):
        self._raw = raw
        self._partition_id = partition_id
        self._code = code
        self._session_token = session_token

        self._requires_config = False

    @property
    def partition_id(self):
        return self._partition_id

    @property
    def session_token(self):
        return self._session_token

    @property
    def raw(self):
        return self._raw

    @property
    def raw_str(self):
        return json.dumps(self.raw)

    @property
    def requires_config(self):
        return self._requires_config

    def configure(self, cfg):
        pass

    def check(self):
        pass

    @property
    def action(self):
        return None

    def __str__(self):
        return f"<{type(self).__name__} partition_id={self.partition_id} "\
                f"code={'<redacted>' if self._code else self._code} "\
                f"session_token={self.session_token}>"

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            data = json.loads(data)

        action_type = data.get('action')
        klass = find_subclass(QolsysControl, action_type,
                              cache=QolsysControl.__SUBCLASSES_CACHE)
        if not klass:
            raise UnknownQolsysControlException(
                "Unable to find a QolsysControl class for "\
                f"action '{action_type}'")

        from_json = getattr(klass, 'from_json', None)
        if callable(from_json) and \
                from_json.__func__ != QolsysControl.from_json.__func__:
            return from_json(data)

        return klass(
            partition_id=data.get('partition_id'),
            code=data.get('code'),
            session_token=data.get('session_token'),
            raw=data,
        )

class _QolsysControlCheckCode(QolsysControl):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._requires_config = True

    def configure(self, cfg):
        self._code_required = getattr(cfg, self._CODE_REQUIRED_ATTR)
        self._check_code = self._code_required and not cfg.ha_check_disarm_code

        if self._check_code:
            self._valid_code = cfg.ha_disarm_code or cfg.panel_disarm_code

    def check(self):
        super().check()

        if self._check_code:
            # The only condition where _valid_code is None and we still
            # require to get a code from home assistant is if we are in
            # the disarm process; in which case, we don't want to raise
            # an exception, as we want to try and use that provided code
            # to disarm the alarm
            if self._valid_code and self._code != self._valid_code:
                raise InvalidArmDisarmCodeException


class QolsysControlDisarm(_QolsysControlCheckCode):
    
    _CODE_REQUIRED_ATTR = 'code_disarm_required'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._requires_config = True
        self._disarm_code = None

    def configure(self, cfg):
        self._disarm_code = cfg.panel_disarm_code

    def check(self):
        super().check()

        if self._disarm_code is None:
            if not self.code:
                LOGGER.info('Using code sent from home assistant since '\
                            'no disarm code configured')
            else:
                raise MissingDisarmCodeException(
                    'Cannot disarm without a configured disarm code')

    @property
    def action(self):
        return QolsysActionDisarm(
            partition_id=self._partition_id,
            disarm_code=self._disarm_code or self._code,
        )


class QolsysControlArm(_QolsysControlCheckCode):
    _CODE_REQUIRED_ATTR = 'code_arm_required'


class QolsysControlArmAway(QolsysControlArm):
    def __init__(self, delay: int=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._delay = delay
        self._requires_config = self._requires_config or delay is None

    def configure(self, cfg):
        if self._delay is None:
            self._delay = cfg.arm_away_exit_delay

    @property
    def action(self):
        return QolsysActionArmAway(
            partition_id=self._partition_id,
            delay=self._delay,
        )


class QolsysControlArmVacation(QolsysControlArmAway):
    pass


class QolsysControlArmHome(QolsysControlArm):
    @property
    def action(self):
        return QolsysActionArmStay(
            partition_id=self._partition_id,
        )


class QolsysControlArmNight(QolsysControlArmHome):
    pass


# I do not think we can support this through the C4 interface with the panel
# class QolsysControlArmCustomBypass(QolsysControlArm):
    # pass


# This depends on https://github.com/home-assistant/core/pull/60525, which
# has been merged and is available starting with Home Assitant 2021.12
class QolsysControlTrigger(_QolsysControlCheckCode):

    _CODE_REQUIRED_ATTR = 'code_trigger_required'

    def __init__(self, alarm_type: str=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._alarm_type = alarm_type

    @property
    def action(self):
        return QolsysActionTrigger(
            partition_id=self._partition_id,
            alarm_type=self._alarm_type,
        )


class QolsysControlTriggerPolice(QolsysControlTrigger):
    def __init__(self, *args, **kwargs):
        super().__init__(alarm_type=QolsysActionTrigger.ALARM_TYPE_POLICE,
                         *args, **kwargs)


class QolsysControlTriggerFire(QolsysControlTrigger):
    def __init__(self, *args, **kwargs):
        super().__init__(alarm_type=QolsysActionTrigger.ALARM_TYPE_FIRE,
                         *args, **kwargs)


class QolsysControlTriggerAuxiliary(QolsysControlTrigger):
    def __init__(self, *args, **kwargs):
        super().__init__(alarm_type=QolsysActionTrigger.ALARM_TYPE_AUXILIARY,
                         *args, **kwargs)

