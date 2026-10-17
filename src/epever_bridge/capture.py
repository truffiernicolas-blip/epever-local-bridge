"""Analyse hors ligne de métadonnées uniquement. Pas de déchiffrement TLS."""
from collections import Counter


def analyze(path, host):
    try:
        from scapy.all import PcapReader, IP, IPv6, TCP, UDP, DNS, DNSQR
    except ImportError as exc:
        raise ValueError("Analyse PCAP : installer requirements-capture.txt") from exc
    flows, domains = Counter(), Counter()
    packets = 0
    with PcapReader(str(path)) as capture:
        for packet in capture:
            ip = packet.getlayer(IP) or packet.getlayer(IPv6)
            if ip is None or host not in (ip.src, ip.dst):
                continue
            packets += 1
            transport = packet.getlayer(TCP) or packet.getlayer(UDP)
            if transport is not None:
                kind = "tcp" if packet.haslayer(TCP) else "udp"
                flows[(ip.src, ip.dst, kind, int(transport.sport), int(transport.dport))] += 1
            if packet.haslayer(DNS) and packet.haslayer(DNSQR):
                # Noms DNS seulement, pas de charge utile ou de secrets applicatifs.
                name = bytes(packet[DNSQR].qname).decode("ascii", "replace").rstrip(".")
                domains[name] += 1
    return {"packets_matching_host": packets,
            "flows": [{"src": k[0], "dst": k[1], "transport": k[2],
                       "sport": k[3], "dport": k[4], "packets": n} for k, n in sorted(flows.items())],
            "dns_names": dict(domains), "cloud_attribution": "unverified",
            "limitations": ["No TCP reassembly or binary telemetry decoder yet",
                            "Observed UDP traffic does not prove an accessible UDP server",
                            "DNS may be absent, cached or performed by another device"]}
