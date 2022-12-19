import asyncio
import logging
import time
import re

from unittest import mock
from copy import deepcopy

from appdaemon.utils import sync_wrapper


LOGGER = logging.getLogger(__name__)


class ADBase(object):
    def get_ad_api(self):
        raise RuntimeError('Not defined yet')

    async def get_plugin_api(self, plugin_name):
        raise RuntimeError('Not defined yet')

    def register_constraint(self, name):
        raise RuntimeError('Not defined yet')

    def deregister_constraint(self, name):
        raise RuntimeError('Not defined yet')

    def list_constraints(self):
        raise RuntimeError('Not defined yet')


class ADAPI(object):

    CAPTURED_LOGS = []
    PLUGIN_CONFIG = {}

    def log(self, msg, *args, **kwargs):
        log = dict(kwargs.items())

        log['message'] = msg

        for i, v in enumerate(args):
            log[f'arg{i}'] = v

        self.CAPTURED_LOGS.append(log)

    def error(self, msg, *args, **kwargs):
        self.log(msg, *args, level='ERROR', **kwargs)

    @sync_wrapper
    async def create_task(self, coro, callback=None, **kwargs):
        if callback is not None:
            raise RuntimeError('Not defined yet')

        return asyncio.create_task(coro)

    async def get_plugin_config(self, **kwargs):
        return deepcopy(self.PLUGIN_CONFIG)

    async def wait_for_next_log(self, timeout=30, filters=None, match=None,
                                raise_on_timeout=False, startpos=None,
                                returnpos=False):
        start = time.time()
        logslen = startpos or len(self.CAPTURED_LOGS)
        log = None
        _SENTINEL = object()

        if not filters:
            filters = {}

        while log is None:
            while len(self.CAPTURED_LOGS) == logslen and \
                    time.time() - start < timeout:
                await asyncio.sleep(.1)

            if len(self.CAPTURED_LOGS) > logslen:
                while log is None and logslen < len(self.CAPTURED_LOGS):
                    log = self.CAPTURED_LOGS[logslen]

                    for k, v in filters.items():
                        if log.get(k, _SENTINEL) != v:
                            log = None
                            break

                    if log and match and not re.search(match, log['message']):
                        log = None

                    logslen += 1
            else:
                break

        if log is None and raise_on_timeout:
            raise AttributeError('No log found before timeout')

        if returnpos:
            return log, logslen
        else:
            return log


class Mqtt(ADBase, ADAPI):

    SUBSCRIBED_TO = []
    PUBLISHED = []
    LISTEN_EVENT = []

    mqtt_publish_func = mock.Mock(name='mqtt_publish')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @sync_wrapper
    async def listen_event(self, callback, event=None, **kwargs):
        listen_event = deepcopy(kwargs)
        listen_event['callback'] = callback
        listen_event['event'] = event

        self.LISTEN_EVENT.append(listen_event)

        LOGGER.debug(f'listen_event: event={event} callback={callback} kwargs={kwargs}')

    @sync_wrapper
    async def mqtt_publish(self, topic, payload=None, **kwargs):
        published = deepcopy(kwargs)
        published['topic'] = topic
        published['payload'] = payload

        # Store the messages in case we might need them
        self.PUBLISHED.append(published)

        # Let's use a mock function that we forward the call to, so we can
        # then use it for assertions in the tests
        self.mqtt_publish_func(topic, payload, **kwargs)

        # In case we want to follow the logs of what happens in our mock
        LOGGER.debug(f'publishing: topic={topic} payload={payload} kwargs={kwargs}')

        # Let's go through the LISTEN_EVENT data and check if we have
        # any LISTEN_EVENT with MQTT_MESSAGE as event, for the same topic,
        # and in which case we can call the callback
        for listener in self.LISTEN_EVENT:
            if listener['event'] != 'MQTT_MESSAGE' or listener['topic'] != topic:
                continue

            # This is not at all complete, as we only put the payload in the
            # data and give nothing for the kwargs, but that's sufficient for
            # out mock here
            await listener['callback']('MQTT_MESSAGE', {'payload': payload}, {})

    def mqtt_subscribe(self, topic, **kwargs):
        subscribe = deepcopy(kwargs)
        subscribe['topic'] = topic

        self.SUBSCRIBED_TO.append(subscribe)

        LOGGER.debug(f'subscribed: topic={topic} kwargs={kwargs}')

    def mqtt_unsubscribe(self, topic, **kwargs):
        subscribe = deepcopy(kwargs)
        subscribe['topic'] = topic

        self.SUBSCRIBED_TO.remove(subscribe)

    async def is_client_connected(self, **kwargs):
        raise RuntimeError('Not defined yet')

    async def find_last_mqtt_publish(self, filters=None,
                                     raise_if_not_found=False):
        _SENTINEL = object()

        for publish in reversed(self.PUBLISHED):
            found = True

            for k, v in filters.items():
                if publish.get(k, _SENTINEL) != v:
                    found = False
                    break

            if found:
                return publish

        if raise_if_not_found:
            raise AttributeError('No publish found')

        return None

    async def wait_for_next_mqtt_publish(self, timeout=30, filters=None,
                                         raise_on_timeout=False, startpos=None,
                                         returnpos=False):
        start = time.time()
        publishedlen = startpos or len(self.PUBLISHED)
        publish = None
        _SENTINEL = object()

        if not filters:
            filters = {}

        while publish is None:
            while len(self.PUBLISHED) == publishedlen and \
                    time.time() - start < timeout:
                await asyncio.sleep(.1)

            if len(self.PUBLISHED) > publishedlen:
                while publish is None and publishedlen < len(self.PUBLISHED):
                    publish = self.PUBLISHED[publishedlen]

                    for k, v in filters.items():
                        if publish.get(k, _SENTINEL) != v:
                            publish = None
                            break

                    publishedlen += 1
            else:
                break

        if publish is None and raise_on_timeout:
            raise AttributeError('No publish found before timeout')

        if returnpos:
            return publish, publishedlen
        else:
            return publish
