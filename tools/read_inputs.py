"""Lecture ponctuelle explicite, aucune modification de configuration."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from epever_bridge.transport.modbus import read_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--unit", type=int, default=10)
    parser.add_argument("--address", type=lambda s: int(s, 0), required=True)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("reports/read-inputs.json"))
    args = parser.parse_args()
    try:
        report = asyncio.run(read_inputs(args.host, args.port, args.unit, args.address, args.count))
    except (OSError, ValueError, asyncio.TimeoutError, asyncio.IncompleteReadError) as exc:
        parser.exit(1, f"Lecture échouée : {type(exc).__name__}: {exc}\n")
    report["observed_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
