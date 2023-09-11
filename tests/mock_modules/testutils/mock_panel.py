import asyncio
import json
import logging
import os.path
import socket
import ssl
import time

from testutils.utils import MessageStorage


LOGGER = logging.getLogger(__name__)
CERTS_DIR = os.path.join(os.path.dirname(__file__), 'certs')


class PanelServer(object):

    def __init__(self):
        self.MESSAGES = MessageStorage(name='message')
        self.stop()

    async def start(self, port=0):
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.check_hostname = False
        ssl_ctx.load_cert_chain(
            os.path.join(CERTS_DIR, 'mock-panel-server.crt'),
            os.path.join(CERTS_DIR, 'mock-panel-server.key'),
        )

        self._keep_listening = True

        self._address = 'localhost'
        server = await asyncio.start_server(
            self._serve_client,
            self._address,
            port,
            ssl=ssl_ctx,
        )

        address, connected_port = server.sockets[0].getsockname()[:2]
        self._port = connected_port

        return server

    async def test_connection(self):
        s = socket.socket()
        try:
            s.connect((self._address, self._port))
            return True
        except socket.error as e:
            raise RuntimeError("Connection to mock panel ({}, {}) failed: {}".format(self._address, self._port, e))
        finally:
            s.close()

    @property
    def port(self):
        return self._port

    async def writeline(self, line):
        if not isinstance(line, str):
            line = json.dumps(line)

        self._writer.write(f'{line}\n'.encode())
        await self._writer.drain()

    async def wait_for_client(self, timeout=None, raise_if_timeout=False):
        start = time.time()

        while not self._client_connected and (
                not timeout or time.time() - start < timeout):
            await asyncio.sleep(.1)

        if raise_if_timeout and not self._client_connected:
            raise RuntimeError('Timeout before client connection')

        return self._client_connected

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

    async def wait_for_next_message(self, *args, **kwargs):
        return await self.MESSAGES.wait_for_next(*args, **kwargs)
