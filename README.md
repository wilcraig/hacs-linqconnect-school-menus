# LinQ Connect School Menus - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/ryancraig/hacs-linqconnect-school-menus)](https://github.com/ryancraig/hacs-linqconnect-school-menus/releases)
[![GitHub](https://img.shields.io/github/license/ryancraig/hacs-linqconnect-school-menus)](LICENSE)

A Home Assistant custom integration that scrapes school lunch menus from LinQ Connect websites and displays them as sensors with configurable display periods.

## Quick Install

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ryancraig&repository=hacs-linqconnect-school-menus&category=integration)

## Features

- 🍎 **Menu Scraping**: Automatically fetches school lunch menus from LinQ Connect websites
- 📅 **Configurable Display**: Show anywhere from 1 to 7 days of upcoming menus
- 🔄 **Automatic Updates**: Updates menu data every hour
- 🏠 **Home Assistant Integration**: Full integration with config flow UI
- 📱 **HACS Compatible**: Install easily through HACS (Home Assistant Community Store)

## Installation

### HACS (Recommended)

**Option 1: Using the Quick Install Button**
1. Click the "Open your Home Assistant instance" button above
2. This will automatically add the repository to HACS
3. Install the integration
4. Restart Home Assistant

**Option 2: Manual HACS Installation**
1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL: `https://github.com/ryancraig/hacs-linqconnect-school-menus`
5. Select "Integration" as the category
6. Click "Add"
7. Find "LinQ Connect School Menus" in the integration list and install it
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/ryancraig/hacs-linqconnect-school-menus/releases)
2. Extract the files to your `custom_components` directory:
   ```
   custom_components/
   └── linqconnect_school_menus/
       ├── __init__.py
       ├── api.py
       ├── config_flow.py
       ├── const.py
       ├── manifest.json
       ├── sensor.py
       ├── strings.json
       └── translations/
           └── en.json
   ```
3. Restart Home Assistant

## Configuration

### Finding Your Menu URL

1. Go to your school's LinQ Connect menu page (usually provided by the school)
2. The URL should look like: `https://linqconnect.com/public/menu/MENUCODE?buildingId=BUILDING-ID`
3. Copy the complete URL including all parameters

### Setting Up the Integration

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **"+ Add Integration"**
3. Search for **"LinQ Connect School Menus"**
4. Enter your configuration:
   - **Menu URL**: The complete LinQ Connect menu URL from your school
   - **Days to Show**: Number of days of menus to display (1-7)

## Usage

### Sensor Entity

The integration creates a sensor entity with the following properties:

- **Entity ID**: `sensor.school_menu`
- **State**: Today's menu items (comma-separated)
- **Icon**: 🍎 (`mdi:food`)

### Attributes

The sensor provides detailed menu information in its attributes:

```yaml
last_updated: "2025-10-21T10:30:00"
days_requested: 3
menu_url: "https://linqconnect.com/public/menu/..."
day_1_date: "Monday, October 21"
day_1_items: ["Pizza", "Caesar Salad", "Fruit Cup", "Milk"]
day_2_date: "Tuesday, October 22"
day_2_items: ["Chicken Nuggets", "Green Beans", "Mashed Potatoes", "Milk"]
day_3_date: "Wednesday, October 23"
day_3_items: ["Spaghetti", "Garlic Bread", "Side Salad", "Milk"]
```

### Example Automations

#### Daily Menu Notification

```yaml
automation:
  - alias: "Daily School Menu"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.school_day  # Optional: only on school days
        state: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Today's School Menu"
          message: "{{ states('sensor.school_menu') }}"
```

#### Menu Display Card

```yaml
type: entities
title: School Lunch Menu
entities:
  - entity: sensor.school_menu
    name: Today's Menu
show_header_toggle: false
```

### Lovelace Cards

#### Example Card (Included)

An example Lovelace card is included in the repository (`school_menu_card.yaml`) that creates a rich display of the school menu with icons, categories, and pictures. You can copy this into your dashboard:

```yaml
type: markdown
title: 📚 Today's School Menu
content: >
  {% set menu_sensor = states('sensor.school_menu') %} {% set day_1 =
  state_attr('sensor.school_menu', 'day_1') %}

  {% if day_1 and day_1.date %}

  ## 🍽️ {{ day_1.date }} **{{ day_1.session }} Menu**

  ---

  {% set categories = state_attr('sensor.school_menu', 'day_1_categories') %} {%
  if categories %} {% if categories['Main Entree'] %} #### 🍽️ **Main Entrees**
  {% endif %}

  {% if categories['Main Entree'][0] %} _{{ categories['Main Entree'][0] }}_ {%
  endif %} or {% if categories['Main Entree'][1] %} _{{ categories['Main
  Entree'][1] }}_ {% endif %}

  {% set picture_1_url = state_attr('sensor.school_menu', 'day_1_picture_1_url')
  %} {% set picture_1_name = state_attr('sensor.school_menu',
  'day_1_picture_1_name') %} {% set picture_2_url =
  state_attr('sensor.school_menu', 'day_1_picture_2_url') %} {% set
  picture_2_name = state_attr('sensor.school_menu', 'day_1_picture_2_name') %}

  {% if picture_1_url or picture_2_url %}

  {% if picture_1_url %} ![{{ picture_1_name }}]({{ picture_1_url }})

  {% endif %} {% if picture_2_url %} ![{{ picture_2_name }}]({{ picture_2_url
  }})

  {% endif %} {% endif %}

  ---

  {% set icons = {'Side': '🥗', 'Vegetable': '🥕', 'Fruit': '🍎', 'Beverages':
  '🥤', 'Dessert': '🍰'} %}

    {% for category, items in categories.items() if category != 'Main Entree' and category != 'Other' and category != 'Condiments' and category != 'Milk' and category != 'Fruit Juice' and items %}
    #### {{ icons.get(category, '🍽️') }} **{{ category }}**
    {% for item in items %}
    - {{ item if item is string else item.name }}
    {% endfor %}

    {% endfor %}

    {% if categories['Milk'] or categories['Fruit Juice'] %}
    #### 🥤 **Beverages**
    {% if categories['Milk'] %}
    {% for item in categories['Milk'] %}
    - {{ item if item is string else item.name }}
    {% endfor %}
    {% endif %}
    {% if categories['Fruit Juice'] %}
    {% for item in categories['Fruit Juice'] %}
    - {{ item if item is string else item.name }}
    {% endfor %}
    {% endif %}

    {% endif %}
  {% else %}

  📅 No menu items available for today

  {% endif %}

  {% else %}

  ⏳ Loading menu data ({{ menu_sensor }})...

  {% endif %}
```

#### Simple Markdown Card Example

```yaml
type: markdown
content: |
  ## 🍎 School Lunch Menu

  {% set menu = states.sensor.school_menu %}
  {% if menu.state != 'unavailable' %}
    **{{ menu.attributes.day_1_date }}**
    {% for item in menu.attributes.day_1_items %}
    - {{ item }}
    {% endfor %}

    {% if menu.attributes.day_2_items %}
    **{{ menu.attributes.day_2_date }}**
    {% for item in menu.attributes.day_2_items %}
    - {{ item }}
    {% endfor %}
    {% endif %}
  {% else %}
    Menu not available
  {% endif %}
```

## Troubleshooting

### Common Issues

1. **"Building ID not found in URL"**
   - Ensure your URL includes the `buildingId` parameter
   - Example: `?buildingId=102de379-aebe-ed11-82b1-d0dc7addf44a`

2. **"Invalid menu URL format"**
   - URL must be from `linqconnect.com`
   - Must follow pattern: `/public/menu/MENUCODE`

3. **No menu data available**
   - Check if the website is accessible
   - Verify the URL works in a web browser
   - Some schools may have restricted access during certain hours

### Debug Logging

Add this to your `configuration.yaml` to enable debug logging:

```yaml
logger:
  logs:
    custom_components.linqconnect_school_menus: debug
```

## Development

This integration is ready for use. The source code structure follows Home Assistant integration standards:

- `custom_components/linqconnect_school_menus/` - Integration source code
- `school_menu_card.yaml` - Example Lovelace card
- `MENU_CARDS_README.md` - Card examples and documentation

### Dependencies

- `aiohttp>=3.8.0`
- `beautifulsoup4>=4.11.0`
- `lxml>=4.9.0`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [Issues](https://github.com/ryancraig/hacs-linqconnect-school-menus/issues)
- [Discussions](https://github.com/ryancraig/hacs-linqconnect-school-menus/discussions)

## Acknowledgments

- Home Assistant community for the excellent documentation
- LinQ Connect for providing accessible menu data
- HACS for making custom integrations easy to distribute
