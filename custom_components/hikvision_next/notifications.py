"""Events listener."""

from __future__ import annotations

from http import HTTPStatus
import ipaddress
import logging
import socket
from urllib.parse import urlparse

from aiohttp import web
from requests_toolbelt.multipart import MultipartDecoder

from homeassistant.components.http import HomeAssistantView
from homeassistant.const import CONTENT_TYPE_TEXT_PLAIN, STATE_OFF, STATE_ON, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get
from homeassistant.util import slugify

from .const import ALARM_SERVER_PATH, DOMAIN, HIKVISION_EVENT
from .hikvision_device import HikvisionDevice
from .isapi import AlertInfo, IPCamera, ISAPIClient
from .isapi.const import (
    DETECTION_TARGETS,
    EVENT_IO,
    EVENTS,
    MAX_EVENT_REGIONS,
    TARGET_HUMAN,
    TARGET_OTHER,
    TARGET_VEHICLE,
)

_LOGGER = logging.getLogger(__name__)

CONTENT_TYPE = "Content-Type"
CONTENT_TYPE_XML = (
    "application/xml",
    'application/xml; charset="UTF-8"',
    "text/xml",
)
CONTENT_TYPE_TEXT_HTML = "text/html"
CONTENT_TYPE_IMAGE = "image/jpeg"


def get_detection_target(detection_target: str | None) -> str | None:
    """Map detection target reported by the camera to human / vehicle / other."""

    if not detection_target:
        return None
    detection_target = detection_target.lower()
    if detection_target in (TARGET_HUMAN, TARGET_VEHICLE):
        return detection_target
    return TARGET_OTHER


class EventNotificationsView(HomeAssistantView):
    """Event notifications listener."""

    def __init__(self, hass: HomeAssistant):
        """Initialize."""
        self.requires_auth = False
        self.url = ALARM_SERVER_PATH
        self.name = DOMAIN
        self.device: HikvisionDevice
        self.hass = hass

    async def post(self, request: web.Request):
        """Accept the POST request from NVR or IP Camera."""

        try:
            _LOGGER.debug("--- Incoming event notification ---")
            _LOGGER.debug("Source: %s", request.remote)
            xml = await self.parse_event_request(request)
            _LOGGER.debug("alert info: %s", xml)
            alert = ISAPIClient.parse_event_notification(xml)
            self.device = self.get_isapi_device(request.remote, alert)
            self.update_alert_channel(alert)
            self.trigger_sensor(alert)
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.warning("Cannot process incoming event %s", ex)

        response = web.Response(status=HTTPStatus.OK, content_type=CONTENT_TYPE_TEXT_PLAIN)
        return response

    def get_isapi_device(self, device_ip, alert: AlertInfo) -> HikvisionDevice:
        """Get integration instance for device sending alert."""
        integration_entries = self.hass.config_entries.async_entries(DOMAIN)
        instance_identifiers = []
        entry = None
        if len(integration_entries) == 1:
            entry = integration_entries[0]
        else:
            # Search device by mac_address
            for item in integration_entries:
                if item.disabled_by:
                    continue

                item_mac_address = item.runtime_data.device_info.mac_address
                instance_identifiers.append(item_mac_address)

                if item_mac_address == alert.mac:
                    entry = item
                    break

            # Search device by ip_address
            if not entry:
                for item in integration_entries:
                    if item.disabled_by:
                        continue

                    url = item.runtime_data.host
                    instance_identifiers.append(url)

                    if self.get_ip(urlparse(url).hostname) == device_ip:
                        entry = item
                        break

        if not entry:
            raise ValueError(f"Cannot find ISAPI instance for device {device_ip} in {instance_identifiers}")

        return entry.runtime_data

    def get_ip(self, ip_string: str) -> str:
        """Return an IP if either hostname or IP is provided."""

        try:
            ipaddress.ip_address(ip_string)
            return ip_string
        except ValueError:
            resolved_hostname = socket.gethostbyname(ip_string)
            _LOGGER.debug("Resolve host %s resolves to IP %s", ip_string, resolved_hostname)

            return resolved_hostname

    async def parse_event_request(self, request: web.Request) -> str:
        """Extract XML content from multipart request or from simple request."""

        data = await request.read()

        content_type_header = request.headers.get(CONTENT_TYPE).strip()

        _LOGGER.debug("request headers: %s", request.headers)
        xml = None
        if content_type_header in CONTENT_TYPE_XML:
            xml = data.decode("utf-8")
        else:
            # "multipart/form-data; boundary=boundary"
            decoder = MultipartDecoder(data, content_type_header)
            for part in decoder.parts:
                headers = {}
                for key, value in part.headers.items():
                    assert isinstance(key, bytes)
                    headers[key.decode("ascii")] = value.decode("ascii")
                _LOGGER.debug("part headers: %s", headers)
                if headers.get(CONTENT_TYPE) in CONTENT_TYPE_XML:
                    xml = part.text
                if headers.get(CONTENT_TYPE) == CONTENT_TYPE_IMAGE:
                    _LOGGER.debug("image found")
                    # Use camera.snapshot service instead
                    # from datetime import datetime
                    # import aiofiles
                    # now = datetime.now()
                    # filename = f"/media/{DOMAIN}/snapshots/{now.strftime('%Y-%m-%d_%H-%M-%S_%f')}.jpg"
                    # async with aiofiles.open(filename, "wb") as image_file:
                    #     await image_file.write(part.content)
                    #     await image_file.flush()

        if not xml:
            raise ValueError(f"Unexpected event Content-Type {content_type_header}")
        return xml

    def update_alert_channel(self, alert: AlertInfo) -> AlertInfo:
        """Fix channel id for NVR/DVR alert."""

        if alert.channel_id > 32:
            # channel id above 32 is an IP camera
            # On DVRs that support analog cameras 33 may not be
            # camera 1 but camera 5 for example
            try:
                alert.channel_id = [
                    camera.id
                    for camera in self.device.cameras
                    if isinstance(camera, IPCamera) and camera.input_port == alert.channel_id - 32
                ][0]
            except IndexError:
                alert.channel_id = alert.channel_id - 32

    def trigger_sensor(self, alert: AlertInfo) -> None:
        """Determine entity and set binary sensor state."""

        _LOGGER.debug("Alert: %s", alert)

        serial_no = self.device.device_info.serial_no.lower()

        device_id_param = f"_{alert.channel_id}" if alert.channel_id != 0 and alert.event_id != EVENT_IO else ""
        io_port_id_param = f"_{alert.io_port_id}" if alert.io_port_id != 0 else ""
        unique_id = f"binary_sensor.{slugify(serial_no)}{device_id_param}{io_port_id_param}_{alert.event_id}"

        _LOGGER.debug("UNIQUE_ID: %s", unique_id)

        entity_registry = async_get(self.hass)
        entity_id = entity_registry.async_get_entity_id(Platform.BINARY_SENSOR, DOMAIN, unique_id)
        if entity_id:
            # CHANGED: Set state based on eventState from XML
            new_state = STATE_ON if alert.event_state == "active" else STATE_OFF
            entity = self.hass.states.get(entity_id)
            if entity:
                attributes = dict(entity.attributes)
                if alert.region_id:
                    # Keep the last triggered line / region on the aggregate sensor
                    attributes["region_id"] = alert.region_id
                self.hass.states.async_set(entity_id, new_state, attributes)

            self.trigger_region_sensors(unique_id, alert, new_state)

            if entity:
                # Only fire event when motion starts (active), not when it ends
                if alert.event_state == "active":
                    self.fire_hass_event(alert)
            return
        raise ValueError(f"Entity not found {entity_id}")

    def trigger_region_sensors(self, unique_id: str, alert: AlertInfo, new_state: str) -> None:
        """Set state of the binary sensors for the line / region and detection target reported in the alert."""

        if not EVENTS.get(alert.event_id, {}).get("has_regions"):
            return

        sensor_ids = []
        regions = [(region_id, target) for region_id, target in alert.regions if region_id]
        if regions:
            for region_id, detection_target in regions:
                sensor_ids.append(f"{unique_id}_region_{region_id}")
                if target := get_detection_target(detection_target):
                    sensor_ids.append(f"{unique_id}_region_{region_id}_{target}")
                elif new_state == STATE_OFF:
                    # Inactive alert without target info, reset all targets of the line / region
                    sensor_ids.extend(f"{unique_id}_region_{region_id}_{t}" for t in DETECTION_TARGETS)
        elif new_state == STATE_OFF:
            # Inactive alert without region info, reset all lines / regions of the event
            for region_id in range(1, MAX_EVENT_REGIONS + 1):
                sensor_ids.append(f"{unique_id}_region_{region_id}")
                sensor_ids.extend(f"{unique_id}_region_{region_id}_{t}" for t in DETECTION_TARGETS)

        entity_registry = async_get(self.hass)
        for sensor_id in sensor_ids:
            entity_id = entity_registry.async_get_entity_id(Platform.BINARY_SENSOR, DOMAIN, sensor_id)
            if entity_id and (entity := self.hass.states.get(entity_id)):
                self.hass.states.async_set(entity_id, new_state, entity.attributes)

    def fire_hass_event(self, alert: AlertInfo):
        """Fire HASS event."""
        camera_name = ""
        if camera := self.device.get_camera_by_id(alert.channel_id):
            camera_name = camera.name

        message = {
            "channel_id": alert.channel_id,
            "io_port_id": alert.io_port_id,
            "camera_name": camera_name,
            "event_id": alert.event_id,
        }
        if alert.region_id:
            message["region_id"] = alert.region_id
        if alert.detection_target:
            message["detection_target"] = alert.detection_target
            message["region_id"] = alert.region_id

        self.hass.bus.fire(
            HIKVISION_EVENT,
            message,
        )
