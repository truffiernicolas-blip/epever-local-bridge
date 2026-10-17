import importlib.util
from pathlib import Path
import unittest
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("standalone_ha_client", ROOT / "custom_components/epever_local/client.py")
CLIENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIENT)


class DecodeTests(unittest.TestCase):
    def test_signed_current_and_low_word_first_energy(self):
        value = CLIENT.decode({"registers": {0x3581: 0xFF9C, 0x3582: 0xFFFF,
                                             0x3530: 0x0010, 0x3531: 0x0001},
                               "last_update": datetime.now(timezone.utc), "bypass": True})
        self.assertEqual(value["battery_current"], -1.0)
        self.assertEqual(value["ac_energy"], 655.52)
        self.assertIsNone(value["grid_voltage"])
        self.assertEqual(value["operating_mode"], "Bypass réseau")

    def test_missing_is_distinct_from_zero(self):
        value = CLIENT.decode({"registers": {0x3549: 0, 0x3586: 65535, 0x3513: 65535},
                               "last_update": datetime.now(timezone.utc), "bypass": None})
        self.assertEqual(value["pv_voltage"], 0)
        self.assertIsNone(value["pv_current"])
        self.assertIsNone(value["battery_soc"])
        self.assertIsNone(value["charger_temperature"])
