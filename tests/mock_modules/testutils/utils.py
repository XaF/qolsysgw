import asyncio
import re
import socket
import time

from contextlib import closing


def get_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class MessageStorage(object):

    def __init__(self, name='message', match_check_key=None):
        self.MESSAGES = []
        self.SAVED_MESSAGES_POS = 0
        self._name = name
        self._match_check_key = match_check_key

    def _check_if_message_fits(self, msg, filters, match):
        fits = True

        sentinel = object()
        for k, v in filters.items():
            if msg.get(k, sentinel) != v:
                fits = False
                break

        if fits and self._match_check_key and match and \
                not re.search(match, msg[self._match_check_key]):
            fits = False

        return fits

    def append(self, value):
        self.MESSAGES.append(value)

    async def find_last(self, filters=None, match=None,
                        raise_if_not_found=False):
        for msg in reversed(self.MESSAGES):
            if self._check_if_message_fits(msg, filters, match):
                return msg

        if raise_if_not_found:
            raise AttributeError(f'No {self._name} found')

        return None

    async def wait_for_next(self, timeout=30, filters=None, match=None,
                            raise_on_timeout=False, startpos=None,
                            returnpos=False, continued=False):
        start = time.time()
        msg = None

        pos = startpos
        if pos is None and continued:
            pos = self._SAVED_MESSAGES_POS
        if pos is None:
            pos = len(self.MESSAGES)

        if not filters:
            filters = {}

        while msg is None:
            while len(self.MESSAGES) == pos and \
                    time.time() - start < timeout:
                await asyncio.sleep(.1)

            if len(self.MESSAGES) > pos:
                while msg is None and pos < len(self.MESSAGES):
                    msg = self.MESSAGES[pos]

                    if not self._check_if_message_fits(msg, filters, match):
                        msg = None

                    pos += 1
            else:
                break

        self._SAVED_MESSAGES_POS = pos

        if msg is None and raise_on_timeout:
            raise AttributeError(f'No {self._name} found before timeout')

        if returnpos:
            return msg, pos
        else:
            return msg
