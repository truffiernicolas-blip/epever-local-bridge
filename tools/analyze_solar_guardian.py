"""Analyse PCAP ciblée ; essai local optionnel, aucune reconfiguration."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import ipaddress
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from epever_bridge.protocol_capture import summarize, initialization_from_capture
from epever_bridge.transport.native_wifi import snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pcap", type=Path)
    parser.add_argument("--live-host", help="Essai FC04 explicite avec la négociation de cette capture")
    parser.add_argument("--output", type=Path, default=Path("reports/solar-guardian-analysis.json"))
    args = parser.parse_args()
    if args.live_host:
        try:
            ip = ipaddress.ip_address(args.live_host)
            if not ip.is_private or ip.is_multicast or ip.is_unspecified or ip.is_reserved:
                raise ValueError()
        except ValueError:
            parser.error("--live-host doit être une adresse IP locale unicast littérale")
    report = summarize(args.pcap)
    if args.live_host:
        try:
            report["live"] = asyncio.run(snapshot(args.live_host, initialization_from_capture(args.pcap)))
            report["live"]["observed_at"] = datetime.now(timezone.utc).isoformat()
        except (OSError, ValueError, asyncio.TimeoutError, asyncio.IncompleteReadError) as exc:
            report["live"] = {"error": type(exc).__name__}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
