import asyncio
import json
import logging
import os
import socket

GUI_SOCK = "/tmp/friday-gui.sock"
DAEMON_SOCK = "/tmp/friday-daemon.sock"

logger = logging.getLogger("friday.ipc")


class UnixServer:
    def __init__(self, path: str):
        self.path = path
        self._server = None

    async def start(self, handler):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass
        self._server = await asyncio.start_unix_server(handler, path=self.path)
        os.chmod(self.path, 0o666)
        logger.info("IPC server listening on %s", self.path)

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass


async def send_command(path: str, command: dict, timeout: float = 3.0) -> dict | None:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_unix_connection(path), timeout=timeout
        )
        writer.write(json.dumps(command).encode() + b"\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.readline(), timeout=timeout)
        writer.close()
        return json.loads(data.decode())
    except Exception as e:
        logger.debug("IPC send_command to %s failed: %s", path, e)
        return None


def send_command_sync(path: str, command: dict, timeout: float = 3.0) -> dict | None:
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(path)
        sock.sendall(json.dumps(command).encode() + b"\n")
        data = sock.recv(65536)
        sock.close()
        return json.loads(data.decode())
    except Exception as e:
        logger.debug("IPC sync send_command to %s failed: %s", path, e)
        return None


def is_running(path: str) -> bool:
    if not os.path.exists(path):
        return False
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(path)
        sock.close()
        return True
    except Exception:
        return False
