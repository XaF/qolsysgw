import asyncio
import os
import subprocess
import sys
import unittest

from unittest import mock

from testenv import FIXTURES_DIR
import asyncmock

from mqtt.listener import MqttQolsysEventListener
from qolsys.events import QolsysEvent


# test MqttQolsysEventListener
class TestMqttQolsysEventListener(unittest.TestCase):

    def test_event_callback_on_success(self):
        # mock event_callback
        event_callback = asyncmock.AsyncMock()
        # mock Mqtt object
        mqtt = mock.Mock()
        # create MqttQolsysEventListener
        listener = MqttQolsysEventListener(
            app=mqtt,
            namespace='test_namespace',
            topic='test_topic',
            callback=event_callback,
        )
        # mock event_name
        event_name = 'MQTT_MESSAGE'
        # mock event_data
        event_data = {
            'topic': 'test_topic',
            'payload': 'test_payload',
        }
        # call event_callback
        qolsys_event = object()
        with mock.patch('qolsys.events.QolsysEvent.from_json', return_value=qolsys_event):
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                listener.event_callback(event_name, event_data, {})
            )
        # assert event_callback was called
        event_callback.assert_called_once_with(qolsys_event)

    #  def test_event_callback_on_unhandled_failure(self):
        #  # mock event_callback
        #  event_callback = mock.Mock()
        #  # mock Mqtt object
        #  mqtt = mock.Mock()
        #  # create MqttQolsysEventListener
        #  listener = MqttQolsysEventListener(
            #  app=mqtt,
            #  namespace='test_namespace',
            #  topic='test_topic',
            #  callback=event_callback,
        #  )
        #  # mock event_name
        #  event_name = 'MQTT_MESSAGE'
        #  # mock event_data
        #  event_data = {
            #  'topic': 'test_topic',
            #  'payload': 'test_payload',
        #  }
        #  # mock QolsysEvent.from_json
        #  QolsysEvent = mock.Mock()
        #  QolsysEvent.from_json.side_effect = Exception('test_exception')
        #  # call event_callback
        #  loop = asyncio.get_event_loop()
        #  result = loop.run_until_complete(
            #  listener.event_callback(event_name, event_data, {})
        #  )
        #  # assert event_callback was not called
        #  event_callback.assert_not_called()


if __name__ == '__main__':
    unittest.main()
