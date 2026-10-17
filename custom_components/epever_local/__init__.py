"""Home Assistant direct local EPEVER integration."""
from datetime import timedelta
import logging
import time

from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import EpeverClient, decode

DOMAIN = "epever_local"
PLATFORMS = [Platform.SENSOR]
LOGGER = logging.getLogger(__name__)


class EpeverCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, LOGGER, name="EPEVER Local", config_entry=entry,
                         update_interval=timedelta(seconds=entry.data.get("interval", 5)))
        self.client = EpeverClient(entry.data["host"], bytes.fromhex(entry.data["session"]),
                                   entry.data.get("port", 8899), entry.data.get("unit", 10))
        self.entry = entry
        self.failures = 0
        self.retry_at = 0

    async def _async_update_data(self):
        if time.monotonic() < self.retry_at:
            raise UpdateFailed("Reconnexion en attente")
        try:
            result = decode(await self.client.poll())
        except Exception as exc:
            self.failures += 1
            self.retry_at = time.monotonic() + min(60, 5 * 2 ** min(self.failures - 1, 4))
            # Do not log initialization, credentials, raw frames or detailed device data.
            raise UpdateFailed(f"Lecture locale indisponible ({type(exc).__name__})") from None
        self.failures = 0
        self.retry_at = 0
        return result


async def async_setup_entry(hass, entry):
    coordinator = EpeverCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async def stop(event):
        await coordinator.client.close()
    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop))
    return True


async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.client.close()
    return unloaded
