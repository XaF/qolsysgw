import unittest

from unittest import mock

import tests.unit.qolsysgw.mqtt.testenv  # noqa: F401

from mqtt.listener import MqttQolsysControlListener
from mqtt.listener import MqttQolsysEventListener


# test MqttQolsysEventListener
class TestUnitMqttQolsysEventListener(unittest.IsolatedAsyncioTestCase):

    async def test_unit_event_callback_on_success(self):
        # mock event_callback
        event_callback = mock.AsyncMock()
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
            await listener.event_callback(event_name, event_data, {})
        # assert event_callback was called
        event_callback.assert_called_once_with(qolsys_event)

    async def test_unit_event_callback_on_empty_data(self):
        # mock event_callback
        event_callback = mock.AsyncMock()
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
        event_data = {}
        # call event_callback
        await listener.event_callback(event_name, event_data, {})
        # assert event_callback was not called
        event_callback.assert_not_called()

    async def test_unit_event_callback_on_unhandled_failure(self):
        # mock event_callback
        event_callback = mock.AsyncMock()
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
        # mock QolsysEvent.from_json
        QolsysEvent = mock.Mock()
        QolsysEvent.from_json.side_effect = Exception('test_exception')
        # call event_callback
        await listener.event_callback(event_name, event_data, {})
        # assert event_callback was not called
        event_callback.assert_not_called()


# test MqttQolsysControlListener
class TestUnitMqttQolsysControlListener(unittest.IsolatedAsyncioTestCase):

    async def test_unit_event_callback_on_success(self):
        # mock event_callback
        event_callback = mock.AsyncMock()
        # mock Mqtt object
        mqtt = mock.Mock()
        # create MqttQolsysControlListener
        listener = MqttQolsysControlListener(
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
        qolsys_control = object()
        with mock.patch('qolsys.control.QolsysControl.from_json', return_value=qolsys_control):
            await listener.event_callback(event_name, event_data, {})
        # assert event_callback was called
        event_callback.assert_called_once_with(qolsys_control)

    async def test_unit_event_callback_on_empty_data(self):
        # mock event_callback
        event_callback = mock.AsyncMock()
        # mock Mqtt object
        mqtt = mock.Mock()
        # create MqttQolsysControlListener
        listener = MqttQolsysControlListener(
            app=mqtt,
            namespace='test_namespace',
            topic='test_topic',
            callback=event_callback,
        )
        # mock event_name
        event_name = 'MQTT_MESSAGE'
        # mock event_data
        event_data = {}
        # call event_callback
        await listener.event_callback(event_name, event_data, {})
        # assert event_callback was not called
        event_callback.assert_not_called()

    async def test_unit_event_callback_on_unhandled_failure(self):
        # mock event_callback
        event_callback = mock.AsyncMock()
        # mock Mqtt object
        mqtt = mock.Mock()
        # create MqttQolsysControlListener
        listener = MqttQolsysControlListener(
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
        # mock QolsysEvent.from_json
        QolsysEvent = mock.Mock()
        QolsysEvent.from_json.side_effect = Exception('test_exception')
        # call event_callback
        await listener.event_callback(event_name, event_data, {})
        # assert event_callback was not called
        event_callback.assert_not_called()


if __name__ == '__main__':
    unittest.main()
