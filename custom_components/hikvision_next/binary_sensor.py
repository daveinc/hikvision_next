"""Platform for binary sensor integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import ENTITY_ID_FORMAT, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HikvisionConfigEntry
from .const import EVENTS
from .hikvision_device import HikvisionDevice
from .isapi import EventInfo
from .isapi.const import DETECTION_TARGETS, EVENT_IO, MAX_EVENT_REGIONS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HikvisionConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add binary sensors for hikvision events states."""

    device = entry.runtime_data

    entities = []

    # Video Events
    for camera in device.cameras:
        for event in camera.events_info:
            entities.append(EventBinarySensor(device, camera.id, event))
            # Separate sensor per line / region of smart events
            if EVENTS[event.id].get("has_regions"):
                for region_id in range(1, MAX_EVENT_REGIONS + 1):
                    entities.append(RegionEventBinarySensor(device, camera.id, event, region_id))
                    for target in DETECTION_TARGETS:
                        entities.append(RegionEventBinarySensor(device, camera.id, event, region_id, target))

    # General Events
    for event in device.events_info:
        entities.append(EventBinarySensor(device, 0, event))

    async_add_entities(entities)


class EventBinarySensor(BinarySensorEntity):
    """Event detection sensor."""

    _attr_has_entity_name = True
    _attr_is_on = False

    def __init__(self, device: HikvisionDevice, device_id: int, event: EventInfo) -> None:
        """Initialize."""
        self.entity_id = ENTITY_ID_FORMAT.format(event.unique_id)
        self._attr_unique_id = self.entity_id
        self._attr_translation_key = event.id
        if event.id == EVENT_IO:
            self._attr_translation_placeholders = {"io_port_id": event.io_port_id}
        self._attr_device_class = EVENTS[event.id]["device_class"]
        self._attr_device_info = device.hass_device_info(device_id)
        self._attr_entity_registry_enabled_default = not event.disabled


class RegionEventBinarySensor(EventBinarySensor):
    """Event detection sensor for a single line / region of a smart event, optionally for one detection target."""

    def __init__(
        self, device: HikvisionDevice, device_id: int, event: EventInfo, region_id: int, target: str | None = None
    ) -> None:
        """Initialize."""
        super().__init__(device, device_id, event)
        target_param = f"_{target}" if target else ""
        self.entity_id = ENTITY_ID_FORMAT.format(f"{event.unique_id}_region_{region_id}{target_param}")
        self._attr_unique_id = self.entity_id
        self._attr_translation_key = f"{event.id}_region{target_param}"
        self._attr_translation_placeholders = {"region_id": region_id}
        self._attr_extra_state_attributes = {"region_id": region_id}
        if target:
            self._attr_extra_state_attributes["detection_target"] = target
        # Disabled by default, enable only sensors for lines / regions configured on the device
        self._attr_entity_registry_enabled_default = False
