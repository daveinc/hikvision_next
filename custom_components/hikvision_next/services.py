"Integration actions."

from httpx import HTTPStatusError
import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import (
    ACTION_ISAPI_REQUEST,
    ACTION_PTZ_MOVE,
    ACTION_PTZ_STOP,
    ACTION_REBOOT,
    ATTR_CONFIG_ENTRY_ID,
    DOMAIN,
)
from .isapi import ISAPIForbiddenError, ISAPIUnauthorizedError

ACTION_ISAPI_REQUEST_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required("method"): str,
        vol.Required("path"): str,
        vol.Optional("payload"): str,
    }
)


# Direction mappings for PTZ movement
PTZ_DIRECTIONS = {
    "up": {"pan": 0, "tilt": 50, "zoom": 0},
    "down": {"pan": 0, "tilt": -50, "zoom": 0},
    "left": {"pan": -50, "tilt": 0, "zoom": 0},
    "right": {"pan": 50, "tilt": 0, "zoom": 0},
    "up_left": {"pan": -50, "tilt": 50, "zoom": 0},
    "up_right": {"pan": 50, "tilt": 50, "zoom": 0},
    "down_left": {"pan": -50, "tilt": -50, "zoom": 0},
    "down_right": {"pan": 50, "tilt": -50, "zoom": 0},
    "zoom_in": {"pan": 0, "tilt": 0, "zoom": 50},
    "zoom_out": {"pan": 0, "tilt": 0, "zoom": -50},
    "stop": {"pan": 0, "tilt": 0, "zoom": 0},
}


def _get_camera_channel_id(hass: HomeAssistant, entity_id: str) -> tuple[object, int]:
    """Get the camera channel ID from entity_id."""
    # Get entity registry
    registry = er.async_get(hass)
    entity_entry = registry.async_get(entity_id)

    if not entity_entry:
        raise HomeAssistantError(f"Entity {entity_id} not found")

    # Get config entry
    config_entry = hass.config_entries.async_get_entry(entity_entry.config_entry_id)
    if not config_entry:
        raise HomeAssistantError(f"Config entry for {entity_id} not found")

    device = config_entry.runtime_data

    # Extract channel ID from unique_id (format: serialno_streamid)
    # Stream ID format is like "801" for channel 8, stream type 01
    unique_id = entity_entry.unique_id
    if "_" in unique_id:
        stream_id = unique_id.split("_")[-1]
        # First digit(s) before the last two digits is the channel ID
        channel_id = int(stream_id[:-2]) if len(stream_id) > 2 else int(stream_id[0])
    else:
        raise HomeAssistantError(f"Cannot determine channel ID from entity {entity_id}")

    return device, channel_id


def setup_services(hass: HomeAssistant) -> None:
    """Set up the services for the Hikvision component."""

    async def handle_reboot(call: ServiceCall):
        """Handle the reboot action call."""
        entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        entry = hass.config_entries.async_get_entry(entry_id)
        device = entry.runtime_data
        try:
            await device.reboot()
        except (HTTPStatusError, ISAPIForbiddenError, ISAPIUnauthorizedError) as ex:
            raise HomeAssistantError(ex.response.content) from ex

    async def handle_isapi_request(call: ServiceCall) -> ServiceResponse:
        """Handle the custom ISAPI request action call."""
        entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        entry = hass.config_entries.async_get_entry(entry_id)
        device = entry.runtime_data
        method = call.data.get("method", "POST")
        path = call.data["path"].strip("/")
        payload = call.data.get("payload")
        try:
            response = await device.request(method, path, present="xml", data=payload)
        except (HTTPStatusError, ISAPIForbiddenError, ISAPIUnauthorizedError) as ex:
            if isinstance(ex.response.content, bytes):
                response = ex.response.content.decode("utf-8")
            else:
                response = ex.response.content
        return {"data": response.replace("\r", "")}

    async def handle_ptz_move(call: ServiceCall):
        """Handle the PTZ move action call."""
        entity_ids = call.data.get("entity_id")
        if not entity_ids:
            raise HomeAssistantError("No entity_id provided")

        # Ensure entity_ids is a list
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        # Get movement parameters
        direction = call.data.get("direction")
        pan = call.data.get("pan")
        tilt = call.data.get("tilt")
        zoom = call.data.get("zoom")
        duration = call.data.get("duration", 1000)
        continuous = call.data.get("continuous", False)

        # Determine pan/tilt/zoom values
        if pan is not None or tilt is not None or zoom is not None:
            # Custom values provided
            pan = pan if pan is not None else 0
            tilt = tilt if tilt is not None else 0
            zoom = zoom if zoom is not None else 0
        elif direction:
            # Use predefined direction
            if direction not in PTZ_DIRECTIONS:
                raise HomeAssistantError(f"Invalid direction: {direction}")
            movement = PTZ_DIRECTIONS[direction]
            pan = movement["pan"]
            tilt = movement["tilt"]
            zoom = movement["zoom"]
        else:
            raise HomeAssistantError("Either direction or pan/tilt/zoom parameters must be provided")

        # Execute PTZ command for each entity
        for entity_id in entity_ids:
            try:
                device, channel_id = _get_camera_channel_id(hass, entity_id)
                await device.ptz_control(channel_id, pan, tilt, zoom, duration, continuous)
            except (HTTPStatusError, ISAPIForbiddenError, ISAPIUnauthorizedError) as ex:
                raise HomeAssistantError(f"PTZ control failed for {entity_id}: {ex}") from ex

    async def handle_ptz_stop(call: ServiceCall):
        """Handle the PTZ stop action call."""
        entity_ids = call.data.get("entity_id")
        if not entity_ids:
            raise HomeAssistantError("No entity_id provided")

        # Ensure entity_ids is a list
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        # Execute stop command for each entity
        for entity_id in entity_ids:
            try:
                device, channel_id = _get_camera_channel_id(hass, entity_id)
                await device.ptz_control(channel_id, 0, 0, 0, 0, continuous=True)
            except (HTTPStatusError, ISAPIForbiddenError, ISAPIUnauthorizedError) as ex:
                raise HomeAssistantError(f"PTZ stop failed for {entity_id}: {ex}") from ex

    async def handle_ptz(call: ServiceCall):
        """Handle the PTZ action call (ONVIF-compatible interface)."""
        entity_ids = call.data.get("entity_id")
        if not entity_ids:
            raise HomeAssistantError("No entity_id provided")

        # Ensure entity_ids is a list
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        # Get PTZ parameters
        pan = call.data.get("pan")
        tilt = call.data.get("tilt")
        zoom = call.data.get("zoom")
        move_mode = call.data.get("move_mode", "ContinuousMove")
        continuous_duration = call.data.get("continuous_duration", 2.0)

        # Convert ONVIF-style parameters to Hikvision values
        pan_value = 0
        tilt_value = 0
        zoom_value = 0

        # If Stop mode, send stop command (all zeros)
        if move_mode == "Stop":
            # Stop command: all values zero, no duration
            duration_ms = 0
        else:
            # ContinuousMove mode: convert direction parameters
            if pan == "LEFT":
                pan_value = -70
            elif pan == "RIGHT":
                pan_value = 70

            if tilt == "UP":
                tilt_value = 70
            elif tilt == "DOWN":
                tilt_value = -70

            if zoom == "ZOOM_IN":
                zoom_value = -70
            elif zoom == "ZOOM_OUT":
                zoom_value = 70

            # For hold-to-move: duration=0 means no auto-stop (continuous until Stop command)
            # For timed mode: duration>0 triggers auto-stop after delay
            duration_ms = int(continuous_duration * 1000) if continuous_duration > 0 else 0

        # Execute PTZ command for each entity
        for entity_id in entity_ids:
            try:
                device, channel_id = _get_camera_channel_id(hass, entity_id)
                await device.ptz_control(channel_id, pan_value, tilt_value, zoom_value, duration_ms, continuous=True)
            except (HTTPStatusError, ISAPIForbiddenError, ISAPIUnauthorizedError) as ex:
                raise HomeAssistantError(f"PTZ control failed for {entity_id}: {ex}") from ex

    hass.services.async_register(
        DOMAIN,
        ACTION_REBOOT,
        handle_reboot,
    )
    hass.services.async_register(
        DOMAIN,
        ACTION_ISAPI_REQUEST,
        handle_isapi_request,
        schema=ACTION_ISAPI_REQUEST_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        ACTION_PTZ_MOVE,
        handle_ptz_move,
    )
    hass.services.async_register(
        DOMAIN,
        ACTION_PTZ_STOP,
        handle_ptz_stop,
    )
    hass.services.async_register(
        DOMAIN,
        "ptz",
        handle_ptz,
    )
