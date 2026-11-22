"""One early-release event entity per explicitly selected native button."""
from matter_server.common.models import EventType

from homeassistant.components.event import EventEntity, EventDeviceClass
from homeassistant.core import callback
from . import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ShortReleaseEntity(entry, source) for source in entry.data["sources"]])


class ShortReleaseEntity(EventEntity):
    _attr_event_types = ["short_release"]
    _attr_device_class = EventDeviceClass.BUTTON
    _attr_should_poll = False

    def __init__(self, entry, source):
        self.entry = entry
        self.source = source
        self._client = None
        self._unsubscribe = None
        self._attr_unique_id = source["unique_id"] + "-short-release"
        self.entity_id = source["entity_id"] + "_short_release"
        self._attr_name = source["entity_id"].split(".", 1)[1] + " Short release"

    @property
    def available(self):
        matter = self.hass.config_entries.async_get_entry(self.source["matter_entry_id"])
        client = getattr(getattr(getattr(matter, "runtime_data", None), "adapter", None), "matter_client", None)
        return client is not None and self._client is client

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        from homeassistant.helpers.event import async_track_time_interval
        from datetime import timedelta

        self._client = None
        self._unsubscribe = None
        source_state = self.hass.states.get(self.source["entity_id"])
        if source_state:
            self._attr_name = source_state.name + " Short release"
        self._attach()
        # Reattach after a core Matter entry reload. This monitors ownership,
        # never waits to classify input or polls devices.
        self.async_on_remove(async_track_time_interval(self.hass, self._check_client, timedelta(seconds=5)))
        self.async_on_remove(self._detach)

    @callback
    def _check_client(self, _now):
        self._attach()
        self.async_write_ha_state()

    @callback
    def _detach(self):
        if self._unsubscribe:
            self._unsubscribe()
        self._unsubscribe = None
        self._client = None

    @callback
    def _attach(self):
        matter = self.hass.config_entries.async_get_entry(self.source["matter_entry_id"])
        client = getattr(getattr(getattr(matter, "runtime_data", None), "adapter", None), "matter_client", None)
        if client is self._client:
            return
        self._detach()
        if client is not None:
            self._client = client
            self._unsubscribe = client.subscribe_events(
                callback=self._receive, event_filter=EventType.NODE_EVENT,
                node_filter=self.source["node_id"])

    @callback
    def _receive(self, _event_type, data):
        gate = self.entry.runtime_data["gate"]
        if not gate.accept(data, self.source["node_id"], self.source["endpoint_id"]):
            return
        self.entry.runtime_data["store"].async_delay_save(gate.snapshot, 1)
        self._trigger_event("short_release", {"event_number": data.event_number,
                            "matter_timestamp": data.timestamp,
                            "previousPosition": 1,
                            "source_entity_id": self.source["entity_id"]})
        self.async_write_ha_state()
