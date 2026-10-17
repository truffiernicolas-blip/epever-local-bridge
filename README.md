# EPEVER Local Telemetry Bridge

Read an **EPEVER UP5000-HM8042** locally through an **EPEVER WiFi 2.4G RJ45 D**
and expose telemetry directly in Home Assistant. No EPEVER cloud account,
MQTT broker or always-on PC is required for the Home Assistant integration.

Experimental, read-only, MIT licensed. Independent community project, not an
official EPEVER integration. LAN addresses in the documentation are examples.

## Confirmed setup

- UP5000-HM8042 inverter/charger and WiFi 2.4G RJ45 D adapter.
- Adapter firmware NW9272_LPT270_HuiNeng_V1.0.19, HF-LPT270 module.
- Solar Guardian Android 2.2.7 local mode, UP HI, communication ID 10.
- Home Assistant OS on Raspberry Pi 5, Core 2026.10.1.
- Native TCP **8899**, gateway initialization followed by **Modbus RTU with CRC**.

Other adapter generations and inverter families are unverified. Do not reuse a
Tracer register map for UP HI. Bare Modbus reads do not reproduce the required
native session on the tested adapter. No TCP-server reconfiguration was needed.

## Sensors

26 read-only entities under one device: grid/output voltage and frequency, output
current and cumulative energy, PV voltage/current/power/energy, battery
voltage/current/SOC, temperatures, raw status codes, bypass mode and last read time.
There are no switches, inverter writes or firmware changes.

Default polling interval: 5 seconds; observed refresh cadence about 6–7 seconds
including sequential reads. One persistent connection is shared by all sensors.
Failed polls mark entities unavailable and reconnect with backoff. Missing registers
are not filled with zeros. Energy counters use kWh and total_increasing.

Without battery/panels, the corresponding registers may return zero. Equipment
presence is recorded in sensor attributes; SOC zero without a battery does not
mean a discharged battery. Output active power is not invented from voltage × current.

## Home Assistant installation

The public repository contains **no gateway session data**. This initial release
needs a capture of **your own** Solar Guardian local session. A generic session
initializer independent of captures is not implemented yet.

1. Record a short local Solar Guardian session on Android, for example using
   PCAPdroid filtered to that app. Start before connecting, display live data
   for 30–60 seconds, then stop. Keep TLS decryption disabled and do not change
   settings or press Load Switch while recording. Keep the capture private.
2. With Python 3.10+ and this repository on a PC:

```sh
python -m pip install -r requirements-capture.txt
python tools/prepare_ha.py path/to/your-capture.pcap
```

3. Copy custom_components/epever_local into your HA configuration's
   custom_components directory, **including generated native_init.bin and translations**.
   Do not copy __pycache__.
4. Restart Home Assistant. Open **Settings → Devices & services → Add integration →
   EPEVER Local**. Enter your gateway IP, port **8899**, correct communication ID
   (10 on the tested UP HI), polling interval and equipment presence.
5. Open the EPEVER device. Close Solar Guardian if it competes with HA for the connection.

This is a manual custom integration, not a default HACS repository. Back up HA
before installation. Disable/remove the integration entry to stop polling.
No adapter configuration needs to be restored.

## Diagnostic tools

```sh
python epever_probe.py --host 192.168.1.100
python epever_probe.py --discover
python tools/analyze_solar_guardian.py path/to/your-capture.pcap
python tools/analyze_solar_guardian.py path/to/your-capture.pcap --live-host 192.168.1.100
```

The standard-library probe checks candidate TCP ports sequentially and optionally
reads the local ARP cache. An open port does not identify its protocol. The capture
analyzer requires Scapy; without --live-host it stays offline. With that option it
reuses this gateway's initialization in memory for a bounded read-only snapshot.
Reports go to the ignored reports directory.

UDP scanning, arbitrary proprietary decoding, standalone MQTT publishing and Docker
deployment are not implemented.

## Privacy

Never publish PCAPs, native_init.bin, session frames, serial numbers, credentials or
HA backups. The initialization is also stored in the HA config entry; treat backups
as private. Non-identifier initialization bytes are handled as opaque data, not
documented as a universal password or constant. Only one hardware/firmware setup
has been validated.

## Development and research

```sh
python -m unittest discover -s tests -v
python -m compileall -q src tools custom_components
```

16 tests cover CRC, fragmentation, exceptions, read restrictions, TCP reassembly,
initialization, signed current and energy decoding. They run without HA; the
integration was additionally tested on real Home Assistant OS.

Research notes are in French, with anonymized network examples:

- [Hardware](docs/hardware.md)
- [Comparative investigation and sources](docs/investigation.md)
- [Protocol](docs/protocol.md)
- [Capture analysis and native port](docs/capture-2026-10-17.md)
- [Home Assistant](docs/home_assistant.md)
- [Earlier experiments](docs/trials-2026-10-17.md)

Primary leads: [EPEVER](https://www.epever.com/),
[zuzkins/ha-epever](https://github.com/zuzkins/ha-epever) (Tracer AN + RJ45 D,
not assumed compatible with UP HI), and the
[UP-HI V8.5 register document](https://forum.iobroker.net/assets/uploads/files/1667825519362-up-hi-communication-protocol-v8.5.pdf)
(third-party hosting). Vendor manuals are linked, not redistributed.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [LICENSE](LICENSE).
