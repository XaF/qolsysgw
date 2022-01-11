import asyncio
import json
import logging
import socket
import ssl
import threading
import time

from qolsys.actions import QolsysAction
from qolsys.actions import QolsysActionInfo
from qolsys.events import QolsysEvent
from qolsys.exceptions import UnknownQolsysEventException
from qolsys.exceptions import UnknownQolsysSensorException
from qolsys.utils import LoggerCallback


LOGGER = logging.getLogger(__name__)


class QolsysSocket(object):
    def __init__(self, hostname: str, port: int=None, token: str=None,
                 logger=None, callback: callable = None,
                 connected_callback: callable=None,
                 disconnected_callback: callable=None,
                 keep_alive: int=None) -> None:
        self._hostname = hostname
        self._port = port or 12345
        self._token = token or ''

        self._logger = logger or LOGGER
        self._callback = callback or LoggerCallback()
        self._connected_callback = connected_callback or LoggerCallback('Connected callback')
        self._disconnected_callback = disconnected_callback or LoggerCallback('Disconnected callback')
        self._keep_alive = keep_alive or 60 * 4 # 4mn, since the panel generally timeouts at 5mn

        self._writer = None

    def create_tasks(self, event_loop):
        return {
            'listen': event_loop.create_task(self.listen()),
            'keep_alive': event_loop.create_task(self.keep_alive()),
        }

    async def send(self, action: QolsysAction):
        if self._writer is None:
            raise Exception('No writer')

        self._logger.debug(f'Sending: {action.with_token(self._token)}')
        self._writer.write(action.with_token(self._token).encode())
        await self._writer.drain()

    async def keep_alive(self):
        while 'we need to keep the connection alive':
            if self._writer is not None:
                self._logger.debug('Sending keep-alive')
                self._writer.write('\n'.encode())
                await self._writer.drain()
            await asyncio.sleep(self._keep_alive)

    async def listen(self):
        context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_2)
        context.options = ssl.CERT_NONE

        server = (self._hostname, self._port)

        self._listen = True
        delay_reconnect = 0
        while self._listen:
            writer = None
            try:
                self._logger.info(
                        f'Establishing connection to {server[0]}:{server[1]}')
                reader, writer = await asyncio.open_connection(
                        *server, ssl=context, server_hostname='')
                self._writer = writer

                await self.send(QolsysActionInfo())
                await self._connected_callback()

                delay_reconnect = 0
                while 'there is content to read':
                    line = await reader.readline()
                    if not line:
                        self._logger.info('Connection closed by the panel, exiting to reset the connection')
                        break

                    line = line.decode().rstrip('\n')
                    self._logger.debug(f"Data received (len: {len(line)}): {line}")

                    if line == 'ACK':
                        # This is an ACK to a command we sent, we can ignore
                        self._logger.debug('ACK - ignoring.')
                        continue

                    try:
                        # We try to parse the event to one of our event classes
                        event = QolsysEvent.from_json(line)
                    except json.decoder.JSONDecodeError:
                        self._logger.debug(f'Data is not JSON: {line}')
                        continue
                    except UnknownQolsysEventException:
                        self._logger.debug(f'Unknown Qolsys event: {line}')
                        continue
                    except UnknownQolsysSensorException:
                        self._logger.debug(f'Unknown sensor in Qolsys event: {line}')
                        continue
                    
                    try:
                        await self._callback(event)
                    except:
                        self._logger.exception(f'Error calling callback for event: {line}')
            except asyncio.exceptions.CancelledError:
                self._listen = False
                self._logger.info('listening cancelled')
            except:
                delay_reconnect = min(delay_reconnect * 2 or 1, 60)
                self._logger.exception('error while listening')
            finally:
                await self._disconnected_callback()

                self._writer = None

                if writer:
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except:
                        self._logger.exception('unable to wait for writer to '\
                            'be fully closed; this might not be an issue if '\
                            'the connection was closed on the other side')

            if self._listen and delay_reconnect:
                self._logger.info(f'sleeping {delay_reconnect} second(s) before reconnecting')
                await asyncio.sleep(delay_reconnect)

