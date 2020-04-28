import asyncio
from functools import partial
from types import TracebackType
from typing import (
    Any,
    ClassVar,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Type,
    cast,
)

from .sanitizer_config import SanitizerEnvironment


class ProcessProtocol(asyncio.SubprocessProtocol):

    _stdout: ClassVar[int] = 1
    _stderr: ClassVar[int] = 2

    def __init__(self, loop: asyncio.AbstractEventLoop):
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

    async def read_std(self, max_size: int = -1) -> Tuple[bytes, bytes]:
        stdout, stderr = self._std.values()

        return await stdout.read(max_size), await stderr.read(max_size)

    async def wait_closed(self) -> None:
        await asyncio.shield(self.process_end_waiter)

    async def communicate(self) -> Tuple[bytes, bytes]:
        await self.wait_closed()
        return await self.read_std()


class ProcessConnection:
    def __init__(
            self,
            env: SanitizerEnvironment,
            cmd: List[str],
            *,
            loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self._loop = loop or asyncio.get_running_loop()

        self._transport: asyncio.BaseTransport
        self._protocol: asyncio.BaseProtocol

        self._protocol_factory = partial(ProcessProtocol, loop=self._loop)

        self._subprocess = partial(
            self._loop.subprocess_shell,
            protocol_factory=self._protocol_factory,
            cmd=' '.join(cmd),
            bufsize=0,
            creationflags=0,
            env=env.environment,
        )

    def __await__(self) -> Generator[Any, None, ProcessProtocol]:
        return self.__await_impl__().__await__()

    async def __aenter__(self) -> ProcessProtocol:
        return await self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
    ) -> None:
        self._transport.close()

    async def __await_impl__(self) -> ProcessProtocol:
        self._transport, self._protocol = await self._subprocess()
        return cast(ProcessProtocol, self._protocol)
