import re
import subprocess
import threading

from ast import literal_eval

from .utils import MessageStorage


class AppDaemonDockerLogReader(object):

    PARSER_REG = re.compile(
        r'^(?P<datetime>[0-9]{4}-[0-9]{2}-[0-9]{2} '
        r'[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]*) '
        r'(?P<level>[A-Z]*) '
        r'(?P<source>[^ ]*): '
        r'(?P<message>'
        r'(?P<action>[^ :]*): (?P<action_target>[^ ,]*), (?P<action_data>.*)|'
        r'.*)\n$'
    )

    def __init__(self, container_name, backlog=1000):
        self.LOGS = MessageStorage(name='docker log')
        self._container_name = container_name
        self._backlog = backlog

    def start(self):
        t = threading.Thread(target=self.read_logs, daemon=True)
        t.start()
        return t

    def parse_line(self, logline):
        m = self.PARSER_REG.search(logline)
        if m:
            result = m.groupdict()

            # If the action data exists, it's going to be a set of parameters
            # that we can then flatten into the resulting object
            if 'action_data' in result and result['action_data']:
                result.update({
                    f'action_data/{k}': v
                    for k, v in literal_eval(result['action_data']).items()
                })

            return result

        return None

    def read_logs(self):
        cmd = ['docker', 'logs']
        if self._backlog > 0:
            cmd += ['-n', str(self._backlog)]
        cmd += ['-f', self._container_name]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        for line in iter(process.stdout.readline, b''):
            pline = self.parse_line(line.decode())
            if pline:
                self.LOGS.append(pline)

        process.wait()
        return process.returncode

    async def wait_for_next_log(self, *args, **kwargs):
        return await self.LOGS.wait_for_next(*args, **kwargs)

    async def find_last_log(self, *args, **kwargs):
        return await self.LOGS.find_last(*args, **kwargs)
