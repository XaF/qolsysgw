import asyncio
import json
import requests
import time

from urllib.parse import urljoin


class HomeAssistantRestAPI(requests.Session):

    def __init__(self, port, token, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._base_url = f'http://localhost:{port}/api/'

        self.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        })

    def request(self, method, url, *args, **kwargs):
        joined_url = urljoin(self._base_url, url)
        return super().request(method, joined_url, *args, **kwargs)

    def states(self):
        return self.get('states')

    def entity_state(self, entity):
        return self.get(f'states/{entity}')

    async def wait_for_entity(self, entity, filters=None, timeout=None,
                              raise_if_timeout=False):
        start = time.time()

        resp = None
        while not resp and (not timeout or time.time() - start < timeout):
            resp = self.entity_state(entity)

            if not resp.ok:
                resp = None
            elif filters:
                data = resp.json()
                sentinel = object()
                for k, v in filters.items():
                    if data.get(k, sentinel) != v:
                        resp = None
                        break

            if resp is None:
                await asyncio.sleep(.5)

        if not resp and raise_if_timeout:
            reason = 'unknown reason'
            resp = self.states()
            if not resp.ok:
                reason = 'could not get states from home assistant API'
            else:
                entities = resp.json()
                entity_obj = [e for e in entities if e['entity_id'] == entity]
                if not entity_obj:
                    reason = 'entity not found in home assistant (entities: {})'.format(
                        ', '.join([e['entity_id'] for e in entities]))
                else:
                    entity_obj = entity[0]
                    sentinel = object()
                    diff_filters = [
                        "{}={} (expected: {})".format(
                            k, entity_obj.get(k, sentinel), v)
                        for k, v in filters.items()
                        if entity_obj.get(k, sentinel) != v
                    ]
                    reason = 'entity found but did not match filters: {}'.format(', '.join(diff_filters))

            raise RuntimeError('Timeout before entity {} ready: {}'.format(entity, reason))

        return resp

    def call_service(self, domain, service, service_data=None):
        return self.post(f'services/{domain}/{service}', json=service_data)

    def alarm(self, service, entity_id, code=None):
        service_data = {
            'entity_id': entity_id,
        }

        if code is not None:
            service_data['code'] = code

        return self.call_service(
            domain='alarm_control_panel',
            service=service,
            service_data=service_data,
        )

    def alarm_arm_away(self, *args, **kwargs):
        return self.alarm('alarm_arm_away', *args, **kwargs)

    def alarm_arm_vacation(self, *args, **kwargs):
        return self.alarm('alarm_arm_vacation', *args, **kwargs)

    def alarm_arm_home(self, *args, **kwargs):
        return self.alarm('alarm_arm_home', *args, **kwargs)

    def alarm_arm_night(self, *args, **kwargs):
        return self.alarm('alarm_arm_night', *args, **kwargs)

    def alarm_disarm(self, *args, **kwargs):
        return self.alarm('alarm_disarm', *args, **kwargs)

    def alarm_trigger(self, *args, **kwargs):
        return self.alarm('alarm_trigger', *args, **kwargs)
