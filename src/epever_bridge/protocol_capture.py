"""Analyse ciblée Solar Guardian ; aucune exportation de la négociation native."""
from collections import defaultdict
from .transport.modbus import crc16, decode_response


def reassemble(segments):
    """Réassemble un sens TCP, élimine doublons/chevauchements, refuse les trous."""
    output = bytearray()
    end = None
    for seq, data in sorted(segments):
        if end is None:
            end = seq
        if seq > end:
            raise ValueError("Gap in TCP capture")
        skip = max(0, end - seq)
        output.extend(data[skip:])
        end = max(end, seq + len(data))
    return bytes(output)


def frames(data, request):
    """Sépare négociation et lectures Modbus ; refuse fonctions non prévues."""
    result = []
    while data:
        if data[0] == (0x10 if request else 0x20):
            if len(data) < 2:
                raise ValueError("Truncated native header")
            size = data[1] + 2
            kind = "initialization"
        else:
            if len(data) < 3:
                raise ValueError("Truncated Modbus header")
            function = data[1]
            if request:
                if function not in (1, 2, 4):
                    raise ValueError("Unexpected request function; not exported")
                size = 8
            elif function in (1, 2, 4):
                size = data[2] + 5
            elif function in (0x81, 0x82, 0x84):
                size = 5
            else:
                raise ValueError("Unexpected response function")
            kind = "modbus"
        if size > len(data):
            raise ValueError("Truncated frame")
        frame, data = data[:size], data[size:]
        if kind == "modbus" and crc16(frame[:-2]) != int.from_bytes(frame[-2:], "little"):
            raise ValueError("Invalid captured CRC")
        result.append((kind, frame))
    return result


def sessions(path, host="10.10.100.254", port=8899):
    try:
        from scapy.all import PcapReader, IP, TCP
    except ImportError as exc:
        raise ValueError("Install requirements-capture.txt") from exc
    streams = defaultdict(lambda: {"request": [], "response": []})
    packets = 0
    with PcapReader(str(path)) as capture:
        for packet in capture:
            packets += 1
            if not packet.haslayer(IP) or not packet.haslayer(TCP):
                continue
            ip, tcp = packet[IP], packet[TCP]
            data = bytes(tcp.payload)
            if not data:
                continue
            if ip.dst == host and tcp.dport == port:
                streams[(ip.src, int(tcp.sport))]["request"].append((int(tcp.seq), data))
            elif ip.src == host and tcp.sport == port:
                streams[(ip.dst, int(tcp.dport))]["response"].append((int(tcp.seq), data))
    return packets, [{direction: frames(reassemble(segments), direction == "request")
                       for direction, segments in stream.items()} for stream in streams.values()]


def initialization_from_capture(path):
    _, streams = sessions(path)
    candidates = {frame for stream in streams for kind, frame in stream["request"]
                  if kind == "initialization"}
    if len(candidates) != 1:
        raise ValueError("Expected one unique native initialization")
    frame = candidates.pop()
    # Seulement le type d'initialisation observé, pas un envoi arbitraire vers la série.
    if len(frame) != 32 or frame[:4] != bytes.fromhex("101e0016"):
        raise ValueError("Unrecognized native initialization")
    return frame


def summarize(path):
    packets, streams = sessions(path)
    readings = defaultdict(list)
    units, functions = set(), set()
    pairs = 0
    unmatched_requests = 0
    repeated_requests = 0
    for stream in streams:
        requests = [f for k, f in stream["request"] if k == "modbus"]
        unique_requests = []
        for frame in requests:
            if unique_requests and frame == unique_requests[-1]:
                repeated_requests += 1
            else:
                unique_requests.append(frame)
        requests = unique_requests
        responses = [f for k, f in stream["response"] if k == "modbus"]
        if len(responses) > len(requests):
            raise ValueError("Responses without requests")
        unmatched_requests += len(requests) - len(responses)
        for request, response in zip(requests, responses):
            unit, function = request[:2]
            units.add(unit)
            functions.add(function)
            if response[0] != unit or response[1] != function:
                raise ValueError("Request/response mismatch")
            address = int.from_bytes(request[2:4], "big")
            count = int.from_bytes(request[4:6], "big")
            if function == 4:
                values = decode_response(response, unit, count)
                for offset, value in enumerate(values):
                    readings[f"0x{address + offset:04X}"].append(value)
            pairs += 1
    return {"packet_count": packets, "tcp_sessions": len(streams),
            "gateway": "10.10.100.254", "port": 8899, "transport": "tcp",
            "protocol": "native_initialization_then_modbus_rtu", "units": sorted(units),
            "functions": sorted(functions), "read_pairs_crc_valid": pairs,
            "unmatched_requests": unmatched_requests,
            "adjacent_repeated_requests": repeated_requests,
            "registers": {key: {"samples": len(values), "first": values[0],
                                "last": values[-1], "min": min(values), "max": max(values)}
                          for key, values in sorted(readings.items())},
            "initialization": "Present; contents intentionally omitted"}
