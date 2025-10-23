"""Config flow for LinQ Connect School Menus integration."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import parse_qs, urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_BUILDING_ID,
    CONF_DAYS_TO_SHOW,
    CONF_MENU_URL,
    DEFAULT_DAYS_TO_SHOW,
    DOMAIN,
    MAX_DAYS_TO_SHOW,
    MIN_DAYS_TO_SHOW,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MENU_URL): str,
        vol.Optional(CONF_DAYS_TO_SHOW, default=DEFAULT_DAYS_TO_SHOW): vol.All(
            int, vol.Range(min=MIN_DAYS_TO_SHOW, max=MAX_DAYS_TO_SHOW)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from .api import LinQConnectClient

    # Parse the URL to extract building ID
    parsed_url = urlparse(data[CONF_MENU_URL])

    if "linqconnect.com" not in parsed_url.netloc:
        raise InvalidHost("URL must be from linqconnect.com")

    # Extract building ID from query parameters
    query_params = parse_qs(parsed_url.query)
    building_id = query_params.get("buildingId")

    if not building_id:
        raise InvalidBuildingId("Building ID not found in URL - URL should include ?buildingId=...")

    building_id = building_id[0]

    # Extract menu ID from path - support both /public/menu/ and /unified/menu/ formats
    path_parts = parsed_url.path.split("/")
    menu_id = None

    # Look for menu ID in different URL formats
    if "public" in path_parts and "menu" in path_parts:
        menu_idx = path_parts.index("menu")
        if menu_idx + 1 < len(path_parts):
            menu_id = path_parts[menu_idx + 1].split("?")[0]  # Remove query params if present
    elif "unified" in path_parts and "menu" in path_parts:
        # For unified URLs, menu ID might be at the end
        if len(path_parts) >= 5:  # e.g., /unified/menu/k12/milpitas
            menu_id = path_parts[-1]

    if not menu_id:
        raise InvalidMenuId("Invalid menu URL format - should be like https://linqconnect.com/public/menu/MENUCODE?buildingId=...")

    # Test API connectivity
    session = async_get_clientsession(hass)
    client = LinQConnectClient(session)

    try:
        # Test getting district ID
        district_id = await client._get_district_id(menu_id)
        if not district_id:
            raise CannotConnect(f"Cannot fetch district information for menu ID: {menu_id}")

        # Test menu data fetch
        menu_data = await client.get_menu_data(data[CONF_MENU_URL], building_id, 1)
        if not menu_data or not menu_data.get("menus"):
            raise CannotConnect("Cannot fetch menu data from API")

    except CannotConnect:
        raise
    except Exception as err:
        _LOGGER.error("Failed to test API connection: %s", err)
        raise CannotConnect(f"API connection test failed: {err}")

    # Return info that you want to store in the config entry.
    return {
        "title": f"School Menu ({menu_id})",
        CONF_MENU_URL: data[CONF_MENU_URL],
        CONF_BUILDING_ID: building_id,
        CONF_DAYS_TO_SHOW: data[CONF_DAYS_TO_SHOW],
        "menu_id": menu_id,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LinQ Connect School Menus."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["menu_url"] = "invalid_host"
            except InvalidBuildingId:
                errors["menu_url"] = "invalid_building_id"
            except InvalidMenuId:
                errors["menu_url"] = "invalid_menu_id"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=info)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate there is invalid host."""


class InvalidBuildingId(HomeAssistantError):
    """Error to indicate building ID is invalid."""


class InvalidMenuId(HomeAssistantError):
    """Error to indicate menu ID is invalid."""
