import asyncio
import struct
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from epever_bridge.protocol_capture import reassemble, frames, summarize
from epever_bridge.transport.modbus import crc16, read_request
from epever_bridge.transport.native_wifi import snapshot


def response(unit, values):
    body = bytes([unit, 4, len(values) * 2]) + struct.pack(">" + "H" * len(values), *values)
    return body + struct.pack("<H", crc16(body))


class CaptureTests(unittest.TestCase):
    def test_reassembly_overlaps_reordering_and_gaps(self):
        self.assertEqual(reassemble([(103, b"def"), (100, b"abcd"), (100, b"abcd")]), b"abcdef")
        with self.assertRaisesRegex(ValueError, "Gap"):
            reassemble([(100, b"ab"), (103, b"d")])

    def test_multiple_frames_and_crc(self):
        data = response(10, [24438, 5000]) + response(10, [116])
        self.assertEqual(len(frames(data, False)), 2)
        with self.assertRaisesRegex(ValueError, "CRC"):
            frames(data[:-1] + bytes([data[-1] ^ 1]), False)

    def test_initialization_omitted_and_retries_counted(self):
        request = read_request(10, 0x3500, 1)
        session = {"request": [("initialization", b"private"),
                               ("modbus", request), ("modbus", request)],
                   "response": [("modbus", response(10, [24438]))]}
        with patch("epever_bridge.protocol_capture.sessions", return_value=(10, [session])):
            report = summarize("unused")
        self.assertEqual(report["read_pairs_crc_valid"], 1)
        self.assertEqual(report["adjacent_repeated_requests"], 1)
        self.assertNotIn("private", str(report))


class NativeTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialization_and_only_read_requests(self):
        initialization = bytes.fromhex("101e0016") + b"0" * 22 + b"x" * 6
        observed = []
        async def client(reader, writer):
            observed.append(await reader.readexactly(32))
            writer.write(bytes.fromhex("20090007") + b"V1.0.17")
            await writer.drain()
            for values in [[24438, 0, 0, 0, 5000], [24438, 116, 0], [5000], [0, 0], [0, 0]]:
                observed.append(await reader.readexactly(8))
                data = response(10, values)
                writer.write(data[:2])
                await writer.drain()
                await asyncio.sleep(.01)
                writer.write(data[2:])
                await writer.drain()
            writer.close()
            await writer.wait_closed()
        server = await asyncio.start_server(client, "127.0.0.1", 0)
        async with server:
            result = await snapshot("127.0.0.1", initialization, port=server.sockets[0].getsockname()[1])
        self.assertEqual(result["gateway_protocol_version"], "V1.0.17")
        self.assertEqual(result["reads"][0]["registers"][0], 24438)
        self.assertEqual(observed[0], initialization)
        self.assertTrue(all(frame[1] == 4 for frame in observed[1:]))
        self.assertNotIn(initialization.hex(), str(result))
