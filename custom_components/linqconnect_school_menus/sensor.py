"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import LinQConnectClient
from .const import (
    CONF_BUILDING_ID,
    CONF_DAYS_TO_SHOW,
    CONF_MENU_URL,
    DOMAIN,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    session = async_get_clientsession(hass)
    client = LinQConnectClient(session, hass)  # Pass hass instance for media storage

    coordinator = LinQConnectDataUpdateCoordinator(
        hass,
        client,
        config_entry.data[CONF_MENU_URL],
        config_entry.data[CONF_BUILDING_ID],
        config_entry.data[CONF_DAYS_TO_SHOW],
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([LinQConnectSensor(coordinator, config_entry)])


class LinQConnectDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: LinQConnectClient,
        menu_url: str,
        building_id: str,
        days_to_show: int,
    ) -> None:
        """Initialize."""
        self.client = client
        self.menu_url = menu_url
        self.building_id = building_id
        self.days_to_show = days_to_show

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            return await self.client.get_menu_data(
                self.menu_url, self.building_id, self.days_to_show
            )
        except Exception as exception:
            raise UpdateFailed(exception) from exception


class LinQConnectSensor(CoordinatorEntity, SensorEntity):
    """Representation of a LinQ Connect school menu sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LinQConnectDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}"
        self._attr_name = "School Menu"
        self._attr_icon = "mdi:food"
        self._picture_data = {}

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("menus"):
            return "No menu data"

        menus = self.coordinator.data["menus"]
        if not menus:
            return "No menus"

        # Count total items across all days
        total_items = sum(len(menu.get("items", [])) for menu in menus)
        if total_items == 0:
            return "No items"

        # Return count and date range
        if len(menus) == 1:
            return f"{len(menus[0].get('items', []))} items for {menus[0].get('date', 'today')}"
        else:
            return f"{total_items} items for {len(menus)} days"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        attributes = {
            "last_updated": self.coordinator.data.get("last_updated"),
            "days_requested": self.coordinator.data.get("days_requested", 1),
            "menu_url": self._config_entry.data[CONF_MENU_URL],
        }

        # Add each day's menu as separate attributes
        menus = self.coordinator.data.get("menus", [])
        for i, menu in enumerate(menus):
            day_key = f"day_{i+1}"

            # Create structured day data object for template access
            categories = menu.get("categories", {})
            menu_items = []
            for category_name, items in categories.items():
                for item in items:
                    if isinstance(item, dict):
                        menu_items.append({
                            "category_name": category_name,
                            "item_name": item["name"]
                        })
                    else:
                        menu_items.append({
                            "category_name": category_name,
                            "item_name": item
                        })

            # Store complete day data as structured object
            day_data = {
                "date": menu.get("date", f"Day {i+1}"),
                "date_display": menu.get("date", f"Day {i+1}"),
                "session": menu.get("session", "Unknown"),
                "menu_items": menu_items,
                "item_count": menu.get("item_count", 0),
                "category_count": menu.get("category_count", 0)
            }
            attributes[day_key] = day_data

            # Also keep individual attributes for backward compatibility
            attributes[f"{day_key}_date"] = menu.get("date", f"Day {i+1}")
            attributes[f"{day_key}_items"] = menu.get("items", [])

            # Convert categories to simple format for backward compatibility
            simple_categories = {}
            for category_name, items in categories.items():
                if items:
                    simple_categories[category_name] = [
                        item["name"] if isinstance(item, dict) else item
                        for item in items
                    ]
            attributes[f"{day_key}_categories"] = simple_categories
            attributes[f"{day_key}_item_count"] = menu.get("item_count", 0)
            attributes[f"{day_key}_category_count"] = menu.get("category_count", 0)

            # Add picture URLs for all items with pictures (not just main entree)
            all_pictures = menu.get("all_pictures", [])
            if all_pictures:
                # Store picture info with URLs and categories
                for j, picture_item in enumerate(all_pictures):
                    if picture_item.get("picture_url"):
                        attributes[f"{day_key}_picture_{j+1}_name"] = picture_item["name"]
                        attributes[f"{day_key}_picture_{j+1}_url"] = picture_item["picture_url"]
                        attributes[f"{day_key}_picture_{j+1}_category"] = picture_item.get("category", "Unknown")

                # Also store the count of pictures available
                attributes[f"{day_key}_picture_count"] = len(all_pictures)

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
