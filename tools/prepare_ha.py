"""Prepare private gateway initialization from your own Solar Guardian capture."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from epever_bridge.protocol_capture import initialization_from_capture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pcap", type=Path, help="Your own local Solar Guardian PCAP")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] /
                        "custom_components/epever_local/native_init.bin")
    args = parser.parse_args()
    try:
        frame = initialization_from_capture(args.pcap)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as target:
            target.write(frame)
    except FileExistsError:
        parser.exit(1, "Output already exists; keep your backup and choose another --output path.\n")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Preparation failed ({type(exc).__name__}); verify the capture and dependencies.\n")
    print(f"Private initialization saved to {args.output}. Do not publish this file or the source capture.")


if __name__ == "__main__":
    main()
