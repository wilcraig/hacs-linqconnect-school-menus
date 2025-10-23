# School Menu Home Assistant Cards

This repository includes three different Home Assistant Lovelace markdown cards for displaying school menu data from the LinQ Connect School Menus integration.

## Card Variations

### 1. **Full Featured Card** (`school_menu_card.yaml`)
- **Best for**: Large dashboard spaces, detailed view
- **Features**:
  - Large food photos (first 2 main dishes)
  - Color-coded categories with icons
  - Detailed item lists
  - Summary statistics
  - Professional gradient styling

### 2. **Compact Card** (`school_menu_card_compact.yaml`)
- **Best for**: Smaller dashboard spaces, quick overview
- **Features**:
  - Smaller horizontal photo layout
  - Condensed category display
  - Minimal spacing
  - Essential information only

### 3. **Photo Focus Card** (`school_menu_card_photo_focus.yaml`)
- **Best for**: Visual emphasis, photo galleries
- **Features**:
  - Large photo gallery grid (up to 4 photos)
  - Organized category groupings
  - Card-style photo presentation
  - Enhanced visual hierarchy

## Installation Instructions

### Step 1: Setup the Integration
1. Install the LinQ Connect School Menus integration via HACS
2. Configure it with your school's menu URL and building ID
3. Verify the sensor `sensor.linqconnect_school_menus_school_menu` is working

### Step 2: Add the Card to Your Dashboard
1. Copy the content from one of the card files (e.g., `school_menu_card.yaml`)
2. In Home Assistant, go to your Lovelace dashboard
3. Click "Edit Dashboard" → "Add Card" → "Manual"
4. Paste the card configuration
5. Replace the sensor entity ID if different:
   ```yaml
   # Change this line if your sensor has a different name
   sensor.linqconnect_school_menus_school_menu
   ```

### Step 3: Customize (Optional)
- Adjust colors, fonts, and styling in the CSS
- Modify which categories are displayed
- Change photo sizes and layouts
- Add or remove icons

## Sensor Data Structure

The cards expect these attributes from your sensor:

### Day Data (`day_1`, `day_2`, etc.)
- `date`: Display date (e.g., "Tuesday, October 22, 2025")
- `session`: Meal session (e.g., "Lunch")
- `item_count`: Total number of menu items
- `category_count`: Number of food categories

### Categories (`day_1_categories`)
- `Main Entree`: Primary dishes
- `Side`: Side dishes
- `Vegetable`: Vegetable options
- `Fruit`: Fruit options
- `Milk`: Milk varieties
- `Dessert`: Dessert items
- `Condiments`: Sauces and condiments
- `Other`: Miscellaneous items

### Photos
- `day_1_picture_1_url`: URL to first food photo
- `day_1_picture_1_name`: Name of first food item
- `day_1_picture_2_url`: URL to second food photo
- `day_1_picture_2_name`: Name of second food item
- `day_1_picture_count`: Total number of photos available

## Troubleshooting

### Card Shows "Loading..." or "No menu data"
1. Check that your sensor is working: Go to Developer Tools → States and search for your sensor
2. Verify the integration is properly configured
3. Check the Home Assistant logs for any integration errors

### Photos Not Displaying
1. Verify photos are being downloaded: Check `config/www/school_menus/` folder
2. Check that photo URLs are accessible from your Home Assistant instance
3. Ensure the `/local/school_menus/` path is accessible

### Entity ID Issues
Update the sensor entity ID in the card if it's different:
```yaml
# Find all instances of this in the card and update:
sensor.linqconnect_school_menus_school_menu
# Replace with your actual sensor name
```

### Categories Not Showing
Some schools may use different category names. Check your sensor attributes and update the category names in the card template accordingly.

## Customization Examples

### Change Colors
```yaml
# Find color definitions in the card and modify:
background: linear-gradient(135deg, #ff6b6b, #ee5a52);  # Main Entree
background: #4CAF50;  # Vegetables
background: #FFA726;  # Fruits
```

### Modify Photo Layout
```yaml
# Change photo grid sizing:
grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
# Adjust photo dimensions:
width: 180px; height: 120px;
```

### Add Custom Icons
```yaml
# Update the icons dictionary:
{% set icons = {'Side': '🥗', 'Vegetable': '🥕', 'Fruit': '🍎', 'Custom Category': '🍕'} %}
```

## Advanced Features

### Multi-Day Display
To show multiple days, duplicate the day sections and change `day_1` to `day_2`, etc.:
```yaml
{% set day_2 = state_attr('sensor.linqconnect_school_menus_school_menu', 'day_2') %}
```

### Conditional Display
Hide sections when no data is available:
```yaml
{% if categories['Main Entree'] %}
  <!-- Show main entree section -->
{% endif %}
```

### Responsive Design
The cards include responsive design elements that adapt to different screen sizes automatically.

## Support

If you encounter issues:
1. Check the Home Assistant community forums
2. Review the LinQ Connect integration documentation
3. Verify your school's menu API is accessible
4. Check Home Assistant logs for error messages

## License

These cards are provided under the same license as the LinQ Connect School Menus integration (MIT License).
