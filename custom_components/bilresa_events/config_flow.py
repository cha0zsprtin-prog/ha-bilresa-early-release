"""Explicit allowlist of existing Matter button entities; no autodetected controls."""
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers import entity_registry as er, selector

from . import DOMAIN
from .gate import address


class BilresaEventsFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            registry = er.async_get(self.hass)
            sources = []
            try:
                for entity_id in user_input["sources"]:
                    entity = registry.async_get(entity_id)
                    if entity is None or entity.platform != "matter":
                        raise ValueError("Not a Matter entity")
                    node, endpoint = address(entity.unique_id)
                    sources.append({"entity_id": entity_id, "node_id": node,
                                    "endpoint_id": endpoint,
                                    "matter_entry_id": entity.config_entry_id,
                                    "unique_id": entity.unique_id})
                if not sources or len({(s["matter_entry_id"], s["node_id"], s["endpoint_id"]) for s in sources}) != len(sources):
                    raise ValueError("Empty or repeated sources")
            except (KeyError, TypeError, ValueError):
                errors["base"] = "invalid_sources"
            else:
                return self.async_create_entry(title="BILRESA Early Release Events", data={"sources": sources})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("sources"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="event", integration="matter", multiple=True)
            )
        }), errors=errors)
