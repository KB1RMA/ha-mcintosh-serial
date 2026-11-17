"""Connection management: owns the library client, reconnects when the link drops."""

import asyncio
from collections.abc import Awaitable, Callable
import logging

from mcintosh_serial import (
    DeviceState,
    Timing,
    Transport,
    ZonedClient,
    ZoneState,
    open_serial,
)

_LOGGER = logging.getLogger(__name__)

TIMING = Timing()
RECONNECT_DELAY = 10.0

OpenFn = Callable[[str, int], Awaitable[Transport]]


class Hub:
    """One receiver: its client, availability and change listeners."""

    def __init__(
        self, port: str, baudrate: int, zone: int, open_fn: OpenFn | None = None
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.zone = zone
        self._open_fn = open_fn
        self._client: ZonedClient | None = None
        self._listeners: list[Callable[[], None]] = []
        self._reconnect_task: asyncio.Task[None] | None = None
        self._closing = False

    # ----------------------------------------------------------------- state
    @property
    def available(self) -> bool:
        """Report whether the receiver is connected."""
        return self._client is not None and self._client.connected

    @property
    def zone_state(self) -> ZoneState:
        """Return the managed zone's last known state."""
        return self.state.zone(self.zone)

    @property
    def state(self) -> DeviceState:
        """Return everything the receiver has reported."""
        return self._client.state if self._client else DeviceState()

    @property
    def client(self) -> ZonedClient:
        """Return the connected client or raise ConnectionError."""
        if self._client is None or not self._client.connected:
            message = "McIntosh receiver is not connected"
            raise ConnectionError(message)
        return self._client

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Call ``listener`` on every state or availability change."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _notify(self) -> None:
        for listener in tuple(self._listeners):
            listener()

    # ------------------------------------------------------------ connection
    async def async_connect(self) -> None:
        """Open the port and load state. Raises on failure and leaves nothing open."""
        transport = await (self._open_fn or open_serial)(self.port, self.baudrate)
        client = ZonedClient(transport, TIMING)
        client.add_listener(lambda _state: self._notify())
        client.add_connection_listener(self._on_connection)
        try:
            await client.start()
        except Exception:
            await client.stop()
            raise
        self._client = client
        self._notify()

    def _on_connection(self, connected: bool) -> None:  # noqa: FBT001 - library callback
        self._notify()
        if not connected and not self._closing and self._reconnect_task is None:
            self._reconnect_task = asyncio.get_running_loop().create_task(
                self._reconnect()
            )

    async def _reconnect(self) -> None:
        await self._drop_client()
        self._notify()
        try:
            while True:
                await asyncio.sleep(RECONNECT_DELAY)
                try:
                    await self.async_connect()
                except Exception as err:  # noqa: BLE001 - keep retrying
                    _LOGGER.debug("Reconnect to %s failed: %s", self.port, err)
                else:
                    _LOGGER.info("Reconnected to McIntosh receiver on %s", self.port)
                    return
        finally:
            self._reconnect_task = None

    async def async_close(self) -> None:
        """Stop reconnecting and close the port."""
        self._closing = True
        task, self._reconnect_task = self._reconnect_task, None
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await self._drop_client()

    async def _drop_client(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            await client.stop()
