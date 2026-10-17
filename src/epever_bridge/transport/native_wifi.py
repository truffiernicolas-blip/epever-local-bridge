"""Session locale RJ45 D observée, initialisation opaque puis FC04 uniquement."""
import asyncio
from .modbus import read_request, decode_response


async def snapshot(host, initialization, port=8899, unit=10, timeout=4):
    if len(initialization) != 32 or initialization[:4] != bytes.fromhex("101e0016"):
        raise ValueError("Invalid native initialization")
    reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    result = {"host": host, "port": port, "unit": unit, "reads": []}
    try:
        writer.write(initialization)
        await asyncio.wait_for(writer.drain(), timeout)
        header = await asyncio.wait_for(reader.readexactly(2), timeout)
        if header[0] != 0x20 or not 2 <= header[1] <= 64:
            raise ValueError("Unrecognized initialization reply")
        reply = await asyncio.wait_for(reader.readexactly(header[1]), timeout)
        if len(reply) < 2 or int.from_bytes(reply[:2], "big") != len(reply) - 2:
            raise ValueError("Invalid initialization reply length")
        result["gateway_protocol_version"] = reply[2:].decode("ascii", "strict")
        for address, count in [(0x3500, 5), (0x3521, 3), (0x3529, 1), (0x3580, 2), (0x3585, 2)]:
            writer.write(read_request(unit, address, count))
            await asyncio.wait_for(writer.drain(), timeout)
            async def receive():
                prefix = await reader.readexactly(3)
                if prefix[0] != unit or prefix[1] not in (4, 0x84):
                    raise ValueError("Unexpected read response")
                remaining = 2 if prefix[1] == 0x84 else prefix[2] + 2
                if remaining > 34:
                    raise ValueError("Oversized read response")
                return prefix + await reader.readexactly(remaining)
            frame = await asyncio.wait_for(receive(), timeout)
            result["reads"].append({"address": f"0x{address:04X}",
                                    "registers": decode_response(frame, unit, count), "crc_valid": True})
            await asyncio.sleep(.5)
        return result
    finally:
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), timeout)
        except (OSError, asyncio.TimeoutError):
            pass
