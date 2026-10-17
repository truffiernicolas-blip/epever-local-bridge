"""Read-only sensors. No switches, buttons or parameter changes."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass as DC, SensorStateClass as SC
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

# key, French name, unit, device class, state class
MEASUREMENTS = [
    ("grid_voltage", "Tension réseau", "V", DC.VOLTAGE, SC.MEASUREMENT),
    ("grid_frequency", "Fréquence réseau", "Hz", DC.FREQUENCY, SC.MEASUREMENT),
    ("grid_charge_current", "Courant de charge réseau", "A", DC.CURRENT, SC.MEASUREMENT),
    ("grid_charge_power", "Puissance de charge réseau", "W", DC.POWER, SC.MEASUREMENT),
    ("grid_charge_energy", "Énergie de charge réseau", "kWh", DC.ENERGY, SC.TOTAL_INCREASING),
    ("ac_voltage", "Tension sortie AC", "V", DC.VOLTAGE, SC.MEASUREMENT),
    ("ac_current", "Courant sortie AC", "A", DC.CURRENT, SC.MEASUREMENT),
    ("ac_frequency", "Fréquence sortie AC", "Hz", DC.FREQUENCY, SC.MEASUREMENT),
    ("ac_energy", "Énergie consommée sortie AC", "kWh", DC.ENERGY, SC.TOTAL_INCREASING),
    ("pv_voltage", "Tension PV", "V", DC.VOLTAGE, SC.MEASUREMENT),
    ("pv_current", "Courant PV", "A", DC.CURRENT, SC.MEASUREMENT),
    ("pv_power", "Puissance PV", "W", DC.POWER, SC.MEASUREMENT),
    ("pv_energy", "Énergie produite PV", "kWh", DC.ENERGY, SC.TOTAL_INCREASING),
    ("battery_voltage", "Tension batterie", "V", DC.VOLTAGE, SC.MEASUREMENT),
    ("battery_current", "Courant batterie", "A", DC.CURRENT, SC.MEASUREMENT),
    ("battery_soc", "SOC batterie", "%", DC.BATTERY, SC.MEASUREMENT),
    ("charger_temperature", "Température chargeur", "°C", DC.TEMPERATURE, SC.MEASUREMENT),
    ("power_temperature", "Température puissance", "°C", DC.TEMPERATURE, SC.MEASUREMENT),
    ("heatsink_1_temperature", "Température dissipateur 1", "°C", DC.TEMPERATURE, SC.MEASUREMENT),
    ("heatsink_2_temperature", "Température dissipateur 2", "°C", DC.TEMPERATURE, SC.MEASUREMENT),
    ("grid_status", "Code état charge réseau", None, None, None),
    ("ac_status", "Code état sortie AC", None, None, None),
    ("pv_status", "Code état PV", None, None, None),
    ("battery_status", "Code état batterie", None, None, None),
    ("operating_mode", "Mode de fonctionnement", None, None, None),
    ("last_update", "Dernière lecture", None, DC.TIMESTAMP, None),
]


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([EpeverSensor(entry.runtime_data, item) for item in MEASUREMENTS])


class EpeverSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator, item):
        super().__init__(coordinator)
        key, name, unit, device_class, state_class = item
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.client.serial}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.client.serial)},
            name="EPEVER UP5000-HM8042", manufacturer="EPEVER", model="UP5000-HM8042")
        if key.endswith("status") or key == "last_update":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self.coordinator.data.get(self.key)

    @property
    def available(self):
        # Failed polls mark everything unavailable; no retained stale numeric values.
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self):
        attrs = {"last_successful_read": self.coordinator.data["last_update"].isoformat()}
        if self.key.startswith("battery_"):
            attrs["battery_installed"] = self.coordinator.entry.data.get("battery_present", False)
            attrs["interpretation"] = "Valeur du registre ; zéro sans batterie ne signifie pas batterie déchargée"
        if self.key.startswith("pv_"):
            attrs["panels_installed"] = self.coordinator.entry.data.get("pv_present", False)
        return attrs
