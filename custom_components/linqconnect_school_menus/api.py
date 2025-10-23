"""LinQ Connect API client."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Any
import re

import aiohttp

_LOGGER = logging.getLogger(__name__)


class LinQConnectClient:
    """Client for LinQ Connect school menu API."""

    def __init__(self, session: aiohttp.ClientSession, hass=None) -> None:
        """Initialize the client."""
        self.session = session
        self.hass = hass

    async def get_menu_data(
        self, menu_url: str, building_id: str, days: int = 1
    ) -> dict[str, Any]:
        """Fetch menu data from LinQ Connect API."""
        try:
            # Extract menu identifier from URL
            menu_identifier = self._extract_menu_identifier(menu_url)
            if not menu_identifier:
                _LOGGER.error("Could not extract menu identifier from URL")
                return {}

            # Get district ID using the identifier
            district_id = await self._get_district_id(menu_identifier)
            if not district_id:
                _LOGGER.error("Could not get district ID for identifier: %s", menu_identifier)
                return {}

            # Calculate date range
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days)

            # Build API URL
            api_url = (
                f"https://api.linqconnect.com/api/FamilyMenu"
                f"?buildingId={building_id}"
                f"&districtId={district_id}"
                f"&startDate={start_date.strftime('%m-%d-%Y')}"
                f"&endDate={end_date.strftime('%m-%d-%Y')}"
            )

            _LOGGER.debug("Fetching menu data from API: %s", api_url)

            async with self.session.get(api_url) as response:
                if response.status != 200:
                    _LOGGER.error("HTTP error %s when fetching menu", response.status)
                    return {}

                json_data = await response.json()
                return await self._parse_menu_json(json_data, days, district_id)

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout when fetching menu data")
            return {}
        except aiohttp.ClientError as err:
            _LOGGER.error("Client error when fetching menu data: %s", err)
            return {}
        except Exception as err:
            _LOGGER.error("Unexpected error when fetching menu data: %s", err)
            return {}

    def _extract_menu_identifier(self, menu_url: str) -> str | None:
        """Extract menu identifier from the LinQ Connect URL."""
        try:
            # Extract from URL pattern: /public/menu/IDENTIFIER
            pattern = r'/public/menu/([A-Z0-9]+)'
            match = re.search(pattern, menu_url)
            if match:
                return match.group(1)

            _LOGGER.error("Could not extract menu identifier from URL: %s", menu_url)
            return None
        except Exception as err:
            _LOGGER.error("Error extracting menu identifier: %s", err)
            return None

    async def _get_district_id(self, identifier: str) -> str | None:
        """Get district ID using the menu identifier."""
        try:
            api_url = f"https://api.linqconnect.com/api/FamilyMenuIdentifier?identifier={identifier}"

            _LOGGER.debug("Getting district ID from: %s", api_url)

            async with self.session.get(api_url) as response:
                if response.status != 200:
                    _LOGGER.error("HTTP error %s when fetching district ID", response.status)
                    return None

                json_data = await response.json()
                district_id = json_data.get("DistrictId")

                if district_id:
                    _LOGGER.debug("Found district ID: %s", district_id)
                    return district_id
                else:
                    _LOGGER.error("District ID not found in response")
                    return None

        except Exception as err:
            _LOGGER.error("Error getting district ID: %s", err)
            return None

    async def _parse_menu_json(self, json_data: dict, days: int, district_id: str) -> dict[str, Any]:
        """Parse the JSON response to extract menu information."""
        menu_data = {
            "menus": [],
            "last_updated": datetime.now().isoformat(),
            "days_requested": days,
        }

        try:
            sessions = json_data.get("FamilyMenuSessions", [])

            if not sessions:
                _LOGGER.warning("No menu sessions found in API response")
                return menu_data

            # Process each serving session (Breakfast, Lunch, etc.)
            for session in sessions:
                session_name = session.get("ServingSession", "Unknown")
                menu_plans = session.get("MenuPlans", [])

                for plan in menu_plans:
                    plan_name = plan.get("MenuPlanName", "Unknown Plan")
                    days_data = plan.get("Days", [])

                    # Limit to requested number of days
                    for day_data in days_data[:days]:
                        day_menu = await self._parse_day_menu(day_data, session_name, plan_name, district_id)
                        if day_menu:
                            menu_data["menus"].append(day_menu)

            # Sort menus by date
            menu_data["menus"].sort(key=lambda x: x.get("date_obj", datetime.min))

        except Exception as err:
            _LOGGER.error("Error parsing menu JSON: %s", err)

        return menu_data

    async def _get_recipe_picture(self, district_id: str, item_id: str) -> str | None:
        """Get base64 picture data for a recipe item."""
        try:
            api_url = (
                f"https://api.linqconnect.com/api/FamilyMenuRecipe"
                f"?districtId={district_id}"
                f"&itemId={item_id}"
            )

            _LOGGER.debug("Fetching recipe picture from: %s", api_url)

            async with self.session.get(api_url) as response:
                if response.status != 200:
                    _LOGGER.debug("HTTP error %s when fetching recipe picture for item %s", response.status, item_id)
                    return None

                json_data = await response.json()
                picture_data = json_data.get("Picture")

                if picture_data and len(picture_data.strip()) > 0:
                    _LOGGER.debug("Found picture data for item %s (length: %d)", item_id, len(picture_data))
                    return picture_data
                else:
                    _LOGGER.debug("No picture data found for item %s", item_id)
                    return None

        except Exception as err:
            _LOGGER.debug("Error fetching recipe picture for item %s: %s", item_id, err)
            return None

    async def _save_picture_to_media(self, item_name: str, item_id: str, picture_data: str) -> str | None:
        """Save picture data to Home Assistant media folder and return URL."""
        if not self.hass or not picture_data:
            return None

        try:
            # Create media directory if it doesn't exist
            media_dir = os.path.join(self.hass.config.config_dir, "www", "school_menus")
            os.makedirs(media_dir, exist_ok=True)

            # Create a safe filename using item ID and name hash
            name_hash = hashlib.md5(item_name.encode()).hexdigest()[:8]
            filename = f"{item_id}_{name_hash}.png"
            file_path = os.path.join(media_dir, filename)

            # Decode base64 and save as PNG file
            try:
                image_data = base64.b64decode(picture_data)
                with open(file_path, "wb") as f:
                    f.write(image_data)

                # Return the URL path for Home Assistant media
                media_url = f"/local/school_menus/{filename}"
                _LOGGER.debug("Saved picture for %s to %s", item_name, media_url)
                return media_url

            except Exception as save_err:
                _LOGGER.warning("Failed to save picture file for %s: %s", item_name, save_err)
                return None

        except Exception as err:
            _LOGGER.warning("Error saving picture to media folder for %s: %s", item_name, err)
            return None

    async def _parse_day_menu(self, day_data: dict, session_name: str, plan_name: str, district_id: str) -> dict[str, Any] | None:
        """Parse a single day's menu from JSON data."""
        try:
            date_str = day_data.get("Date", "")
            if not date_str:
                return None

            # Parse date
            try:
                date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
            except ValueError:
                date_obj = datetime.now()
                formatted_date = date_str

            menu_categories = {}
            total_items = []
            all_items_with_categories = []  # Track all items with their categories for pictures
            main_entree_items = []  # Keep for backward compatibility

            # Process each meal in the day
            for meal in day_data.get("MenuMeals", []):
                meal_name = meal.get("MenuMealName", "")

                # Process each recipe category
                for category in meal.get("RecipeCategories", []):
                    category_name = category.get("CategoryName", "").strip()
                    if not category_name:
                        category_name = "Other"

                    # Initialize category if not exists
                    if category_name not in menu_categories:
                        menu_categories[category_name] = []

                    # Add category items
                    for recipe in category.get("Recipes", []):
                        recipe_name = recipe.get("RecipeName", "").strip()
                        item_id = recipe.get("ItemId", "")

                        if recipe_name:
                            item_info = {
                                "name": recipe_name,
                                "item_id": item_id,
                                "category": category_name,
                                "picture": None
                            }

                            menu_categories[category_name].append(item_info)
                            total_items.append(f"{recipe_name} ({category_name})")

                            # Collect all items for picture fetching
                            all_items_with_categories.append(item_info)

                            # Collect main entree items for backward compatibility
                            if category_name.lower() in ["main entree", "main entrée", "entree", "entrée"]:
                                main_entree_items.append(item_info)

            # Fetch pictures for items with priority for main entree items
            # Sort items to prioritize main entree, then limit to first 4 total
            sorted_items = []
            for item in all_items_with_categories:
                if item["category"].lower() in ["main entree", "main entrée", "entree", "entrée"]:
                    sorted_items.insert(0, item)  # Insert at beginning
                else:
                    sorted_items.append(item)  # Add at end

            picture_fetch_tasks = []
            for item in sorted_items[:4]:  # Limit to first 4 items total
                if item["item_id"]:
                    task = self._get_recipe_picture(district_id, item["item_id"])
                    picture_fetch_tasks.append((item, task))

            # Execute picture fetching tasks and save to media folder
            for item, task in picture_fetch_tasks:
                try:
                    picture_data = await task
                    if picture_data:
                        # Save picture to media folder and get URL
                        media_url = await self._save_picture_to_media(
                            item["name"], item["item_id"], picture_data
                        )
                        if media_url:
                            item["picture_url"] = media_url
                            _LOGGER.debug("Added picture URL for item: %s -> %s", item["name"], media_url)
                        else:
                            _LOGGER.debug("Failed to save picture for item: %s", item["name"])
                except Exception as err:
                    _LOGGER.debug("Failed to fetch picture for %s: %s", item["name"], err)

            # Remove empty categories and sort items within each category
            for category in list(menu_categories.keys()):
                if not menu_categories[category]:
                    del menu_categories[category]
                else:
                    # Sort by name for consistency
                    menu_categories[category] = sorted(menu_categories[category], key=lambda x: x["name"])

            return {
                "date": formatted_date,
                "date_obj": date_obj,
                "session": session_name,
                "plan": plan_name,
                "items": total_items,  # Keep for backward compatibility
                "categories": menu_categories,
                "item_count": len(total_items),
                "category_count": len(menu_categories),
                "raw_date": date_str,
                "main_entree_pictures": [item for item in main_entree_items if item.get("picture_url")],
                "all_pictures": [item for item in sorted_items if item.get("picture_url")],
            }

        except Exception as err:
            _LOGGER.error("Error parsing day menu: %s", err)
            return None
