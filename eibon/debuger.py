from pathlib import Path
from typing import NamedTuple, ClassVar

from .protocol import ProcessConnection
from .sanitizer_config import SanitizerEnvironment


class DebuggerResponse(NamedTuple):
    debugger: str
    stdout: bytes
    stderr: bytes


class GDBObject:

    _name: ClassVar[str] = 'gdb'

    def __init__(self):
        self._env = SanitizerEnvironment('')

    @staticmethod
    def _cmd(bin_path, additional_args=None):
        commands = Path(__file__).parent.resolve() / 'gdb_commands.py'

        return [
            'gdb',
            '-nx',
            '-x', str(commands),
            '-ex', 'init_command',
            '-ex', 'run',
            '-ex', 'quit_command',
            '-return-child-result',
            '-batch',
            '--args',
        ] + [str(bin_path), *additional_args]

    async def launch(self, bin_path, additional_args) -> DebuggerResponse:
        connection = ProcessConnection(
            env=self._env,
            cmd=self._cmd(bin_path, additional_args=additional_args),
        )

        async with connection as current_connection:
            stdout, stderr = await current_connection.communicate()

        return DebuggerResponse(
            stdout=stdout,
            stderr=stderr,
            debugger=self._name,
        )
