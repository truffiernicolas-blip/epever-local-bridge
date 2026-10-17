"""CLI de phase A : aucun envoi de trame série ou Modbus."""
import argparse
import asyncio
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path

from .discovery import neighbors
from .transport.tcp import inspect_port


def port_list(value):
    try:
        ports = list(dict.fromkeys(int(x.strip()) for x in value.split(",")))
        if not ports or len(ports) > 128 or any(not 1 <= p <= 65535 for p in ports):
            raise ValueError()
        return ports
    except ValueError as exc:
        raise argparse.ArgumentTypeError("1 à 128 ports entre 1 et 65535, séparés par des virgules") from exc


async def probe(args):
    report = {"schema_version": 1, "started_at": datetime.now(timezone.utc).isoformat(),
              "host": args.host, "hardware_identity": "unverified", "services": [],
              "network_mode": "undetermined", "udp": {"state": "not_actively_probed"},
              "modbus": {"state": "not_probed", "reason": "hardware_and_register_map_unverified"},
              "configuration_modified": False,
              "limitations": ["An open TCP port does not identify its protocol",
                              "A failed connection does not establish cloud-only operation",
                              "No automatic identification of EPEVER hardware"]}
    if args.discover:
        report["neighbors"] = neighbors()
    if args.host and not args.offline:
        for port in args.ports:
            report["services"].append(await inspect_port(args.host, port, args.timeout,
                                                        http=port in args.http_ports))
            await asyncio.sleep(0.25)
    if args.pcap:
        from .capture import analyze
        report["capture"] = analyze(args.pcap, args.host)
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    return report


def main():
    parser = argparse.ArgumentParser(description="Diagnostic EPEVER sans écriture de paramètres (Python 3.10+)")
    parser.add_argument("--host", help="Adresse IP locale littérale de la clé (pas de résolution DNS)")
    parser.add_argument("--ports", type=port_list, default=port_list("80,443,502,8088,8899,9999"))
    parser.add_argument("--http-ports", type=port_list, default=[],
                        help="HEAD / explicite sur ces ports déjà inclus dans --ports ; aucune authentification")
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--discover", action="store_true", help="Lire le cache ARP, sans balayage réseau")
    parser.add_argument("--pcap", type=Path, help="Capture PCAP/PCAPNG hors ligne, filtrée sur --host")
    parser.add_argument("--offline", action="store_true", help="Ne pas ouvrir de connexion vers la clé")
    parser.add_argument("--output", type=Path, default=Path("reports/probe.json"))
    args = parser.parse_args()
    if not args.host and not args.discover:
        parser.error("--host ou --discover requis")
    if args.pcap and not args.host:
        parser.error("--pcap nécessite --host pour limiter l'analyse à la clé")
    if not 0.1 <= args.timeout <= 30:
        parser.error("--timeout doit être compris entre 0.1 et 30 secondes")
    if not set(args.http_ports) <= set(args.ports):
        parser.error("--http-ports doit être inclus dans --ports")
    if args.host:
        try:
            ip = ipaddress.ip_address(args.host)
            if not ip.is_private or ip.is_multicast or ip.is_unspecified or ip.is_reserved:
                raise ValueError()
        except ValueError:
            parser.error("--host doit être une adresse locale unicast littérale")
    try:
        report = asyncio.run(probe(args))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Diagnostic impossible ({type(exc).__name__}). Vérifier le chemin et les dépendances.\n")
    print(f"Rapport : {args.output.resolve()}")


if __name__ == "__main__":
    main()
