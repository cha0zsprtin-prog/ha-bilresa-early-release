"""Expose only ShortRelease from HA's existing Matter client; no device writes."""
from homeassistant.const import Platform
from homeassistant.helpers.storage import Store

from .gate import ReleaseGate

DOMAIN = "bilresa_events"


async def async_setup_entry(hass, entry):
    store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
    saved = await store.async_load()
    entry.runtime_data = {"gate": ReleaseGate(saved), "store": store}
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.EVENT])
    return True


async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, [Platform.EVENT])
    if unloaded:
        await entry.runtime_data["store"].async_save(entry.runtime_data["gate"].snapshot())
    return unloaded
