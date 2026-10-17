"""RJ45 D native session; strictly read-only inverter communication."""
import asyncio
from datetime import datetime, timezone
import struct

BLOCKS = ((0x3500, 5), (0x350F, 3), (0x3513, 2), (0x3521, 3),
          (0x3529, 1), (0x3530, 4), (0x3549, 4), (0x3557, 3),
          (0x3580, 3), (0x3585, 2), (0x3589, 1))


def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


class DeviceException(Exception):
    """A valid Modbus exception (connection still synchronized)."""


class EpeverClient:
    def __init__(self, host, initialization, port=8899, unit=10):
        if len(initialization) != 32 or initialization[:4] != bytes.fromhex("101e0016"):
            raise ValueError("Unrecognized gateway session initialization")
        if not 1 <= unit <= 247 or not 1 <= port <= 65535:
            raise ValueError("Invalid unit or port")
        self.host, self.port, self.unit = host, port, unit
        self._initialization = initialization
        self.serial = initialization[4:26].decode("ascii")
        self._reader = self._writer = None
        self._lock = asyncio.Lock()
        self.version = None

    async def close(self):
        if self._writer:
            self._writer.close()
            try:
                await asyncio.wait_for(self._writer.wait_closed(), 2)
            except (OSError, asyncio.TimeoutError):
                pass
        self._reader = self._writer = None

    async def _connect(self):
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
        self._writer.write(self._initialization)
        await self._writer.drain()
        prefix = await self._reader.readexactly(2)
        if prefix[0] != 0x20 or not 2 <= prefix[1] <= 64:
            raise ValueError("Invalid gateway initialization response")
        data = await self._reader.readexactly(prefix[1])
        if int.from_bytes(data[:2], "big") != len(data) - 2:
            raise ValueError("Invalid gateway response length")
        self.version = data[2:].decode("ascii")

    async def _read(self, address, count, function=4):
        # Only the observed/read-only ranges, never a generic write API.
        if not ((function == 4 and (address, count) in BLOCKS) or
                (function == 2 and address == 0x2100 and count == 1)):
            raise ValueError("Read outside permitted ranges")
        body = struct.pack(">BBHH", self.unit, function, address, count)
        self._writer.write(body + struct.pack("<H", crc16(body)))
        await self._writer.drain()
        header = await self._reader.readexactly(3)
        if header[0] != self.unit or header[1] not in (function, function | 0x80):
            raise ValueError("Unexpected response header")
        remaining = 2 if header[1] & 0x80 else header[2] + 2
        if remaining > 34:
            raise ValueError("Oversized response")
        frame = header + await self._reader.readexactly(remaining)
        if crc16(frame[:-2]) != int.from_bytes(frame[-2:], "little"):
            raise ValueError("Invalid response CRC")
        if header[1] & 0x80:
            raise DeviceException(f"Modbus exception {header[2]}")
        expected = 1 if function == 2 else count * 2
        if header[2] != expected:
            raise ValueError("Unexpected response byte count")
        if function == 2:
            return bool(frame[3] & 1)
        return list(struct.unpack(">" + "H" * count, frame[3:-2]))

    async def poll(self):
        async with self._lock:
            try:
                async with asyncio.timeout(20):
                    if self._writer is None:
                        await self._connect()
                    registers = {}
                    for address, count in BLOCKS:
                        try:
                            async with asyncio.timeout(3):
                                values = await self._read(address, count)
                            registers.update({address + i: value for i, value in enumerate(values)})
                        except DeviceException:
                            if address == 0x3500:
                                raise
                            # Unsupported optional registers remain unavailable, never zero-filled.
                        await asyncio.sleep(.05)
                    try:
                        async with asyncio.timeout(3):
                            bypass = await self._read(0x2100, 1, 2)
                    except DeviceException:
                        bypass = None
                    return {"registers": registers, "bypass": bypass,
                            "last_update": datetime.now(timezone.utc), "gateway_version": self.version}
            except BaseException:
                await self.close()
                raise


def decode(data):
    registers = data["registers"]
    def u16(address, scale=100):
        value = registers.get(address)
        return value / scale if value is not None else None
    def u32(address, signed=False):
        if address not in registers or address + 1 not in registers:
            return None
        value = registers[address] | registers[address + 1] << 16
        if signed and value & (1 << 31):
            value -= 1 << 32
        return value / 100
    def temperature(address):
        value = registers.get(address)
        if value is None or value in (0x7FFF, 0xFFFF):
            return None
        return (value - 65536 if value >= 32768 else value) / 100
    values = {
        "grid_voltage": u16(0x3500), "grid_charge_current": u16(0x3501),
        "grid_charge_power": u32(0x3502), "grid_frequency": u16(0x3504),
        "grid_charge_energy": u32(0x350F), "grid_status": u16(0x3511, 1),
        "charger_temperature": temperature(0x3513), "power_temperature": temperature(0x3514),
        "ac_voltage": u16(0x3521), "ac_current": u16(0x3522), "ac_status": u16(0x3523, 1),
        "ac_frequency": u16(0x3529), "ac_energy": u32(0x3530),
        "heatsink_1_temperature": temperature(0x3532), "heatsink_2_temperature": temperature(0x3533),
        "pv_voltage": u16(0x3549), "pv_current": u16(0x354A), "pv_power": u32(0x354B),
        "pv_energy": u32(0x3557), "pv_status": u16(0x3559, 1),
        "battery_voltage": u16(0x3580), "battery_current": u32(0x3581, signed=True),
        "battery_soc": u16(0x3586, 1), "battery_status": u16(0x3589, 1),
        "last_update": data["last_update"],
        "operating_mode": None if data["bypass"] is None else ("Bypass réseau" if data["bypass"] else "Sans bypass"),
    }
    if values["battery_soc"] is not None and not 0 <= values["battery_soc"] <= 100:
        values["battery_soc"] = None
    return values
