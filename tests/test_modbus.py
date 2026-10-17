import struct
import asyncio
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from epever_bridge.transport.modbus import crc16, read_request, decode_response, read_inputs


class ModbusTests(unittest.TestCase):
    def test_known_crc_vector(self):
        self.assertEqual(crc16(b"123456789"), 0x4B37)
        self.assertEqual(read_request(1, 0, 1).hex(), "01040000000131ca")

    def test_decode_and_reject_corruption(self):
        body = bytes.fromhex("0a040214b4")
        frame = body + struct.pack("<H", crc16(body))
        self.assertEqual(decode_response(frame, 10, 1), [5300])
        with self.assertRaises(ValueError):
            decode_response(frame[:-1] + bytes([frame[-1] ^ 1]), 10, 1)
        with self.assertRaises(ValueError):
            decode_response(frame, 1, 1)
        with self.assertRaises(ValueError):
            decode_response(frame, 10, 2)

    def test_no_broadcast_or_oversized_read(self):
        for unit, address, count in [(0, 0, 1), (248, 0, 1), (10, 0, 17), (10, 65535, 2)]:
            with self.assertRaises(ValueError):
                read_request(unit, address, count)


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_fragmented_response(self):
        requests = []
        async def client(reader, writer):
            requests.append(await reader.readexactly(8))
            body = bytes.fromhex("0a040214b4")
            frame = body + struct.pack("<H", crc16(body))
            for part in [frame[:1], frame[1:3], frame[3:]]:
                writer.write(part)
                await writer.drain()
                await asyncio.sleep(.01)
            writer.close()
            await writer.wait_closed()
        server = await asyncio.start_server(client, "127.0.0.1", 0)
        async with server:
            result = await read_inputs("127.0.0.1", server.sockets[0].getsockname()[1], 10, 0x3580)
        self.assertEqual(result["registers"], [5300])
        self.assertEqual(requests, [read_request(10, 0x3580, 1)])

    async def test_modbus_exception(self):
        async def client(reader, writer):
            await reader.readexactly(8)
            body = bytes.fromhex("0a8402")
            writer.write(body + struct.pack("<H", crc16(body)))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        server = await asyncio.start_server(client, "127.0.0.1", 0)
        async with server:
            with self.assertRaisesRegex(ValueError, "Modbus exception 2"):
                await read_inputs("127.0.0.1", server.sockets[0].getsockname()[1], 10, 0x3580)
