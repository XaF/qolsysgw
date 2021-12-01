import logging

from qolsys.exceptions import QolsysGwConfigIncomplete
from qolsys.exceptions import QolsysGwConfigError


LOGGER = logging.getLogger(__name__)


class QolsysGatewayConfig(object):

    _SENTINEL = object()
    _DEFAULT_CONFIG = {
        'panel_host': _SENTINEL,
        'panel_port': None,
        'panel_token': _SENTINEL,
        'panel_disarm_code': None,
        'panel_unique_id': 'qolsys_panel',
        'panel_device_name': 'Qolsys Panel',

        'mqtt_namespace': 'mqtt',
        'mqtt_retain': True,
        'discovery_topic': 'homeassistant',

        'state_topic': 'mqtt-state',
        'availability_topic': 'mqtt-availability',
        'control_topic': 'qolsys/control',
        'event_topic': 'qolsys/event',

        'ha_check_disarm_code': True,
        'ha_disarm_code': None,
        'code_arm_required': False,
        'code_disarm_required': False,
        'code_trigger_required': False,

        'arm_away_exit_delay': None,

        'default_sensor_device_class': 'safety',
    }

    def __init__(self, args=None, check=True):
        self._override_config = {}

        if args:
            self.load(args)

        if check:
            self.check()

    def load(self, args):
        for k, v in args.items():
            if k in self._DEFAULT_CONFIG:
                self._override_config[k] = v

    def check(self):
        errors = 0
        for k in self._DEFAULT_CONFIG.keys():
            if self.get(k) is self._SENTINEL:
                LOGGER.error(f"Missing mandatory configuration key '{k}'")
                errors += 1
        if errors > 0:
            raise QolsysGwConfigIncomplete

        if self.get('panel_disarm_code') is None:
            if self.get('ha_disarm_code'):
                raise QolsysGwConfigError(
                        "Cannot use 'ha_disarm_code' if "\
                        "'panel_disarm_code' is not set")

            for k in ['code_arm_required', 'code_trigger_required']:
                if self.get(k):
                    raise QolsysGwConfigError(
                        f"Cannot use '{k}' if no disarm code is set, as the "\
                        "Qolsys Panel does not offer a built-in way to check "\
                        "for the code on ARM or TRIGGER actions.")

            # Without a configured disarm code, we cannot have home assistant
            # checking it for us
            self._override_config['ha_check_disarm_code'] = False

            # Without a configured disarm code, we will use the one provided
            # in home assistant to try and disarm the alarm
            self._override_config['code_disarm_required'] = True

    def get(self, name):
        value = self._override_config.get(name, self._SENTINEL)
        if value is self._SENTINEL:
            value = self._DEFAULT_CONFIG.get(name, self._SENTINEL)
        return value

    def __getattr__(self, name):
        value = self.get(name)
        if value is self._SENTINEL:
            raise AttributeError
        return value

