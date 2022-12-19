import asyncio
import ssl
import os.path
import logging
import json
import time

from testenv import FIXTURES_DIR


LOGGER = logging.getLogger(__name__)


class PanelServer(object):

    MESSAGES = []

    def __init__(self):
        self.stop()

    async def start(self):
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.check_hostname = False
        ssl_ctx.load_cert_chain(
            os.path.join(FIXTURES_DIR, 'mock-panel-server.crt'),
            os.path.join(FIXTURES_DIR, 'mock-panel-server.key'),
        )

        self._keep_listening = True

        server = await asyncio.start_server(
            self._serve_client,
            'localhost',
            0,
            ssl=ssl_ctx,
        )

        address, port = server.sockets[0].getsockname()[:2]
        self._port = port

    @property
    def port(self):
        return self._port

    async def writeline(self, line):
        if not isinstance(line, str):
            line = json.dumps(line)

        self._writer.write(f'{line}\n'.encode())
        await self._writer.drain()

    def stop(self):
        self._keep_listening = False
        self._port = None
        self._writer = None
        self._client_connected = False

    @property
    def is_client_connected(self):
        return self._client_connected

    async def _serve_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        LOGGER.info(f'Connection established with {addr}')

        # We do not want more than one client per instance
        if self._writer:
            LOGGER.warning('Instance already has a client, '
                           f'closing connection with {addr}')
            return

        # Make the writer accessible to the instance
        self._writer = writer
        self._client_connected = True

        try:
            while self._keep_listening:
                # We can't use readline() as there's no guarantee
                # we're getting a \n at the end of the message
                line = await reader.read(4096)

                # Acknowledge that the message was received, as the panel does
                writer.write('ACK\n'.encode())
                await writer.drain()

                # Then handle the message
                line = line.decode().rstrip('\n')
                LOGGER.info(f"Data received (len: {len(line)}): {line}")

                # Convert to JSON
                line_as_json = json.loads(line)
                self.MESSAGES.append(line_as_json)
        finally:
            # If we reach here, clear out the writer
            # self._writer = None
            self._client_connected = False

    async def wait_for_next_message(self, timeout=30, filters=None,
                                    raise_on_timeout=False):
        start = time.time()
        messageslen = len(self.MESSAGES)
        message = None
        _SENTINEL = object()

        if not filters:
            filters = {}

        while message is None:
            while len(self.MESSAGES) == messageslen and time.time() - start < timeout:
                await asyncio.sleep(.1)

            if len(self.MESSAGES) > messageslen:
                while message is None and messageslen < len(self.MESSAGES):
                    message = self.MESSAGES[messageslen]

                    for k, v in filters.items():
                        if message.get(k, _SENTINEL) != v:
                            message = None
                            break

                    messageslen += 1
            else:
                break

        if message is None and raise_on_timeout:
            raise AttributeError('No message found before timeout')

        return message
