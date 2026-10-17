# Contributing

Report the inverter model, Wi-Fi adapter reference, adapter firmware, Home
Assistant version and whether the Solar Guardian local mode works. Compatibility
with one EPEVER family does not imply compatibility with another register map.

Do not attach raw captures, gateway initialization, serial numbers, credentials,
Home Assistant backups or personal network details to public issues. Prefer
sanitized register addresses, numeric read results and error types.

Run `python -m unittest discover -s tests -v` before proposing changes. The tests
do not require real hardware or Home Assistant; client code is loaded separately.
They do not replace integration tests on a running Home Assistant instance.

Keep inverter communication read-only. Do not add write functions, firmware
flashing or automatic adapter reconfiguration to the polling path.
