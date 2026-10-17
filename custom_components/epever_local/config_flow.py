"""Local-only configuration; no cloud account or settings writes."""
from pathlib import Path
import ipaddress

import voluptuous as vol
from homeassistant import config_entries

from . import DOMAIN
from .client import EpeverClient, DeviceException


class EpeverConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            client = None
            try:
                ip = ipaddress.ip_address(user_input["host"])
                if not ip.is_private or ip.is_multicast or ip.is_unspecified:
                    raise ValueError("Local address required")
                initialization = await self.hass.async_add_executor_job(
                    Path(__file__).with_name("native_init.bin").read_bytes)
                client = EpeverClient(user_input["host"], initialization,
                                      user_input["port"], user_input["unit"])
                await self.async_set_unique_id(client.serial)
                self._abort_if_unique_id_configured()
                await client.poll()
                return self.async_create_entry(title="EPEVER UP5000-HM8042", data={
                    **user_input, "session": initialization.hex(), "serial": client.serial})
            except (OSError, TimeoutError, ValueError, EOFError, DeviceException):
                errors["base"] = "cannot_connect"
            finally:
                if client:
                    await client.close()
        schema = vol.Schema({
            vol.Required("host", default="192.168.1.100"): str,
            vol.Required("port", default=8899): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Required("unit", default=10): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
            vol.Required("interval", default=5): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
            vol.Required("battery_present", default=False): bool,
            vol.Required("pv_present", default=False): bool,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
