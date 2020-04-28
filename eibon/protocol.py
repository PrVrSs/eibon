import asyncio
from functools import partial
from typing import ClassVar, Dict


class ProcessProtocol(asyncio.SubprocessProtocol):

    _stdout: ClassVar[int] = 1
    _stderr: ClassVar[int] = 2

    def __init__(self, loop):
        self._std: Dict[int, asyncio.StreamReader] = {
            self._stdout: asyncio.StreamReader(loop=loop),
            self._stderr: asyncio.StreamReader(loop=loop),
        }

        self.process_end_waiter: asyncio.Future[None] = loop.create_future()

    def pipe_data_received(self, fd: int, data: bytes) -> None:
        self._std[fd].feed_data(data)

    def process_exited(self) -> None:
        self.process_end_waiter.set_result(None)

        for pipe in self._std.values():
            pipe.feed_eof()

    async def read_std(self, max_size: int = -1):
        stdout, stderr = self._std.values()

        return await stdout.read(max_size), await stderr.read(max_size)

    async def wait_closed(self) -> None:
        await asyncio.shield(self.process_end_waiter)

    async def communicate(self):
        await self.wait_closed()
        return await self.read_std()


class ProcessConnection:
    def __init__(
            self,
            env,
            cmd,
            *,
            loop=None
    ):
        self._loop = loop or asyncio.get_running_loop()

        self._transport = None
        self._protocol = None

        self._protocol_factory = partial(ProcessProtocol, loop=self._loop)

        self._subprocess = partial(
            self._loop.subprocess_shell,
            protocol_factory=self._protocol_factory,
            cmd=' '.join(cmd),
            bufsize=0,
            creationflags=0,
            env=env.environment,
        )

    def __await__(self):
        return self.__await_impl__().__await__()

    async def __aenter__(self):
        return await self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._transport.close()

    async def __await_impl__(self):
        self._transport, self._protocol = await self._subprocess()
        return self._protocol
