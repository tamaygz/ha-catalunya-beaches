# Catalunya Beaches Integration for Home Assistant

Monitor Catalan beaches with real-time water quality, weather conditions, and safety information from the Catalan Water Agency (Agència Catalana de l'Aigua).

## Features

- **15 Entity Types** across sensors and binary sensors
- **Multi-language Support** (English and Catalan)
- **Configurable Updates** (15 minutes to 24 hours)
- **Dynamic Entity Selection** - enable only the sensors you need
- **Force Refresh** - update data on demand
- **Beach-specific Devices** - organize all entities under each beach

## Sensors

### Regular Sensors (10)
- **Water Temperature** (°C) - Current sea temperature
- **Air Temperature** (°C) - Current air temperature at the beach
- **Water Quality** - Classification from Excellent to Very Poor
- **UV Index** - Sun exposure risk level
- **Wave Height** (m) - Current wave conditions
- **Wind Speed** (km/h) - Wind conditions
- **Sky Condition** - Weather status (Clear, Cloudy, Rain, etc.)
- **Jellyfish Status** - Presence level (None to Very High)
- **Last Water Test Date** - When quality was last checked
- **Beach Description** - General information about the beach

### Binary Sensors (5)
- **Lifeguard Present** - Safety: Is a lifeguard on duty?
- **Out of Season** - Problem: Is the beach closed for the season?
- **Water Quality Good** - Is water quality acceptable or better?
- **Jellyfish Alert** - Problem: Moderate or higher jellyfish presence
- **Rain Risk High** - Problem: Is rain likely?

## Installation

### HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots (⋮) and select "Custom repositories"
4. Add `https://github.com/tamaygz/ha-catalunya-beaches` as an Integration
5. Click "Download"
6. Restart Home Assistant

### Manual Installation
1. Download the latest release from GitHub
2. Copy the `custom_components/ha-catalunya-beaches` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Catalunya Beaches"
4. Follow the configuration flow:

#### Step 1: Language Selection
Choose your preferred language for beach information (English or Catalan)

#### Step 2: Beach Selection
Select a beach from the list fetched from the Catalan Water Agency API

#### Step 3: Entity Configuration
- Select which entities to enable (default: all enabled)
- Set the update interval (default: 1 hour, range: 15 minutes to 24 hours)

### Options

After setup, you can modify configuration:

1. Go to **Settings** → **Devices & Services**
2. Find "Catalunya Beaches"
3. Click **Configure**

Available options:
- **Update Interval** - Change how often data is fetched
- **Enabled Entities** - Add or remove entities
- **Force Refresh** - Immediately update all data
- **Delete Historical Data** - Remove all stored history for this beach

## Usage Examples

### Automations

**Alert when water quality drops:**
```yaml
automation:
  - alias: "Beach Water Quality Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.platja_de_barcelona_water_quality_good
        to: "off"
    action:
      - service: notify.mobile_app
        data:
          message: "Water quality at your beach is not good!"
```

**Check if it's a good beach day:**
```yaml
template:
  - binary_sensor:
      - name: "Good Beach Day"
        state: >
          {{ is_state('binary_sensor.platja_de_barcelona_lifeguard_present', 'on')
             and is_state('binary_sensor.platja_de_barcelona_water_quality_good', 'on')
             and is_state('binary_sensor.platja_de_barcelona_rain_risk_high', 'off')
             and states('sensor.platja_de_barcelona_water_temperature')|float > 20 }}
```

### Dashboard Cards

**Beach overview card:**
```yaml
type: entities
title: Platja de Barcelona
entities:
  - sensor.platja_de_barcelona_water_temperature
  - sensor.platja_de_barcelona_air_temperature
  - sensor.platja_de_barcelona_water_quality
  - binary_sensor.platja_de_barcelona_lifeguard_present
  - binary_sensor.platja_de_barcelona_jellyfish_alert
  - sensor.platja_de_barcelona_uv_index
```

**Beach map card:**
```yaml
type: map
title: Catalunya beaches
auto_fit: true
entities:
  - entity: sensor.platja_de_barcelona_beach_name
    name: Platja de Barcelona
    label_mode: state
```

The **Beach Name** sensor includes attributes for municipality, coast, images, icons, and
latitude/longitude when coordinates are available from the API (detail response or the
stored beach list values captured during setup). These coordinates can be reused in map
cards or templates.

## Data Source

This integration uses the official Catalan Water Agency (Agència Catalana de l'Aigua) API:
- Beach list endpoint: `https://aplicacions.aca.gencat.cat/platges/AppJava/api/front/{language}`
- Beach details endpoint: `https://aplicacions.aca.gencat.cat/platges/AppJava/api/playadetalle/{beach_id}/{language}`

Data is updated according to your configured interval (default: 1 hour). The API provides official government data about beach conditions across Catalonia.

## Troubleshooting

### Integration not loading
- Check your Home Assistant logs for errors
- Verify internet connectivity to the Catalan government API
- Try restarting Home Assistant

### No data showing
- Wait for the first update cycle to complete
- Try using "Force Refresh" in the integration options
- Check if the beach API is accessible from your network

### Entities not appearing
- Verify the entities are enabled in the integration options
- Some beaches may not have all data available
- Check that the entity hasn't been disabled in the entity registry

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Data provided by [Agència Catalana de l'Aigua](https://aca.gencat.cat/)
- Built with the [Home Assistant Integration Blueprint](https://github.com/ludeeus/integration_blueprint)
