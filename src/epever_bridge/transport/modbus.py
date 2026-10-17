"""Transport Modbus RTU sur TCP, lectures FC04 exclusivement."""
import asyncio
import struct


def crc16(data):
    value = 0xFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ 0xA001 if value & 1 else value >> 1
    return value


def read_request(unit, address, count):
    if not 1 <= unit <= 247 or not 0 <= address <= 65535 or not 1 <= count <= 16:
        raise ValueError("Invalid read range")
    if address + count > 65536:
        raise ValueError("Read crosses address boundary")
    body = struct.pack(">BBHH", unit, 4, address, count)
    return body + struct.pack("<H", crc16(body))


def decode_response(frame, unit, count):
    if len(frame) < 5 or crc16(frame[:-2]) != int.from_bytes(frame[-2:], "little"):
        raise ValueError("Invalid frame or CRC")
    if frame[0] != unit:
        raise ValueError("Unexpected unit")
    if frame[1] == 0x84 and len(frame) == 5:
        raise ValueError(f"Modbus exception {frame[2]}")
    if frame[1] != 4 or frame[2] != count * 2 or len(frame) != count * 2 + 5:
        raise ValueError("Unexpected function or length")
    return list(struct.unpack(">" + "H" * count, frame[3:-2]))


async def read_inputs(host, port, unit, address, count=1, timeout=3):
    request = read_request(unit, address, count)
    reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    try:
        writer.write(request)
        await asyncio.wait_for(writer.drain(), timeout)
        async def receive():
            header = await reader.readexactly(3)
            if header[0] != unit or header[1] not in (4, 0x84):
                raise ValueError("Unexpected response header")
            remaining = 2 if header[1] == 0x84 else header[2] + 2
            if remaining > 34:
                raise ValueError("Oversized response")
            return header + await reader.readexactly(remaining)
        frame = await asyncio.wait_for(receive(), timeout)
        return {"unit": unit, "address": f"0x{address:04X}", "function": 4,
                "request_hex": request.hex(), "response_hex": frame.hex(),
                "registers": decode_response(frame, unit, count), "crc_valid": True}
    finally:
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), timeout)
        except (OSError, asyncio.TimeoutError):
            pass
