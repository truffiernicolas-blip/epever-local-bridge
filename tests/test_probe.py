import asyncio
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from epever_bridge.transport.tcp import inspect_port


class NetworkTests(unittest.IsolatedAsyncioTestCase):
    async def test_default_sends_no_application_data(self):
        received = []
        async def client(reader, writer):
            received.append(await reader.read(1024))
            writer.close()
            await writer.wait_closed()
        server = await asyncio.start_server(client, "127.0.0.1", 0)
        async with server:
            result = await inspect_port("127.0.0.1", server.sockets[0].getsockname()[1], .1)
            await asyncio.sleep(.05)
        self.assertEqual(result["state"], "open")
        self.assertEqual(received, [b""])

    async def test_http_opt_in_no_secret_in_report(self):
        requests = []
        async def client(reader, writer):
            requests.append(await reader.readuntil(b"\r\n\r\n"))
            writer.write(b"HTTP/1.0 401 Unauthorized\r\nSet-Cookie: secret\r\n\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        server = await asyncio.start_server(client, "127.0.0.1", 0)
        async with server:
            result = await inspect_port("127.0.0.1", server.sockets[0].getsockname()[1], .5, True)
        self.assertTrue(requests[0].startswith(b"HEAD / "))
        self.assertEqual(result["protocol"], "http")
        self.assertEqual(result["evidence"], [{"http_status": 401}])
        self.assertNotIn("secret", json.dumps(result))

    async def test_refused(self):
        with patch("asyncio.open_connection", new=AsyncMock(side_effect=ConnectionRefusedError())):
            self.assertEqual((await inspect_port("127.0.0.1", 9999, .5))["state"], "closed")


class CliTests(unittest.TestCase):
    def test_offline_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            subprocess.run([sys.executable, str(ROOT / "epever_probe.py"), "--host", "127.0.0.1",
                            "--offline", "--output", str(path)], check=True, capture_output=True)
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report["services"], [])
            self.assertFalse(report["configuration_modified"])
            self.assertEqual(report["modbus"]["state"], "not_probed")

    def test_invalid_target(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/epever_probe.py"),
                                 "--host", "8.8.8.8"], capture_output=True)
        self.assertEqual(result.returncode, 2)
