"""Config flow for Provision ISR integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_AUTO_DETECT_IP,
    CONF_MAC_ADDRESS,
    DEFAULT_PORT,
    DOMAIN,
)
from .discovery import discover_devices
from .provision_api import ProvisionClient
from .provision_api.exceptions import AuthenticationError, ConnectionError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


class ProvisionISRConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Provision ISR."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: list[dict[str, Any]] = []
        self._manual_entry = False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - discovery."""
        if user_input is not None:
            # User selected a device or manual entry
            if user_input.get("device") == "manual":
                self._manual_entry = True
                return await self.async_step_manual()
            
            # User selected discovered device
            selected = user_input["device"]
            for device in self._discovered_devices:
                if device["name"] == selected:
                    return await self.async_step_credentials(device)
        
        # Discover devices on network
        _LOGGER.info("Starting device discovery...")
        self._discovered_devices = await discover_devices(self.hass)
        
        # Build options list
        device_options = {}
        for device in self._discovered_devices:
            device_options[device["name"]] = device["name"]
        
        # Always add manual entry option
        device_options["manual"] = "Manual Entry"
        
        if len(self._discovered_devices) > 0:
            _LOGGER.info("Found %d device(s)", len(self._discovered_devices))
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("device"): vol.In(device_options),
                }
            ),
            description_placeholders={
                "discovered_count": str(len(self._discovered_devices))
            },
        )

    async def async_step_credentials(
        self, device_info: dict[str, Any], user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle credentials entry for discovered device."""
        errors = {}
        
        if user_input is not None:
            # Validate connection
            user_input[CONF_HOST] = device_info[CONF_HOST]
            user_input[CONF_PORT] = device_info[CONF_PORT]
            
            result = await self._test_connection(user_input)
            if result["success"]:
                # Store MAC address for IP change detection
                user_input[CONF_MAC_ADDRESS] = result["mac"]
                
                # Check if already configured
                await self.async_set_unique_id(result["mac"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=result["model"],
                    data=user_input,
                )
            
            errors["base"] = result["error"]
        
        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default="admin"): cv.string,
                    vol.Required(CONF_PASSWORD): cv.string,
                }
            ),
            errors=errors,
            description_placeholders={
                "host": device_info[CONF_HOST],
                "port": str(device_info[CONF_PORT]),
                "model": device_info.get("model", "Unknown"),
            },
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual device entry."""
        errors = {}
        
        if user_input is not None:
            # Validate connection
            result = await self._test_connection(user_input)
            if result["success"]:
                # Store MAC address
                user_input[CONF_MAC_ADDRESS] = result["mac"]
                
                # Check if already configured
                await self.async_set_unique_id(result["mac"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=result["model"],
                    data=user_input,
                )
            
            errors["base"] = result["error"]
        
        return self.async_show_form(
            step_id="manual",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        """Test connection to device.
        
        Returns:
            Dictionary with success status, error message, MAC, and model
        """
        try:
            client = ProvisionClient(
                host=config[CONF_HOST],
                port=config[CONF_PORT],
                username=config[CONF_USERNAME],
                password=config[CONF_PASSWORD],
            )
            
            # Test connection and get device info
            await client.connect()
            device_info = await client.get_device_info()
            await client.close()
            
            return {
                "success": True,
                "mac": device_info.mac,
                "model": f"{device_info.brand} {device_info.model}",
                "error": None,
            }
            
        except AuthenticationError:
            return {
                "success": False,
                "mac": None,
                "model": None,
                "error": "invalid_auth",
            }
        except ConnectionError:
            return {
                "success": False,
                "mac": None,
                "model": None,
                "error": "cannot_connect",
            }
        except Exception as err:
            _LOGGER.exception("Unexpected error during connection test")
            return {
                "success": False,
                "mac": None,
                "model": None,
                "error": "unknown",
            }

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry,
    ) -> ProvisionISROptionsFlow:
        """Get the options flow for this handler."""
        return ProvisionISROptionsFlow(config_entry)


class ProvisionISROptionsFlow(OptionsFlow):
    """Handle options flow for Provision ISR."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_AUTO_DETECT_IP,
                        default=self.config_entry.options.get(
                            CONF_AUTO_DETECT_IP, False
                        ),
                    ): cv.boolean,
                }
            ),
        )
