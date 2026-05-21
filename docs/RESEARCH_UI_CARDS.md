# UI Research & Recommendations (Lovelace + Bubble Card)

## Scope
Research Home Assistant UI visualization options (built-in + Bubble Card), audit all available entities/attributes, and provide recommendations for dashboard design and integration improvements.

## Bubble Card notes (Clooos/Bubble-Card)
Bubble Card is a minimalist card collection that includes **pop-ups**, **sub-buttons**, **horizontal buttons stack**, and multiple card types including button, media player, cover, select, climate, calendar, separator, and layout helpers. Pop-ups are a core capability and can be triggered via navigation/actions or entity states.  
Source: https://github.com/Clooos/Bubble-Card (README).

## Integration UI data inventory
### Sensors (always or selectable)
- **Water Temperature**: state in °C; attributes: `test_estado`, `test_date` (latest water test).
- **Air Temperature**: state in °C.
- **Water Quality**: state string; attributes: `estado_info`, optional `destacar`, `last_update`.
- **UV Index**: numeric; attributes: `uv_min`.
- **Wave Height**: meters.
- **Wind Speed**: km/h; attributes: `direction` (degrees).
- **Sky Condition**: translated text.
- **Jellyfish Status**: text; attributes: `danger_level`, `species[]`, `last_update`.
- **Last Water Test Date**: timestamp.
- **Description**: truncated state; attributes: `full_description`, `length`.
- **Beach Info**: short status/alert text.
- **Beach Name** (always present): state with rich attributes:
  - `beach_id`, `municipality`, `coast`
  - `images[]`, `image_count`, `primary_image`
  - `icon_water_*`, `icon_jellyfish_*` (cached URL values)
  - `entity_picture` is set to the primary beach image
  - image/icon URLs are exposed as token-free `/local/ha-catalunya-beaches/<beach_id>/<filename>`

- **Water Quality** and **Jellyfish Status** sensors also expose `latitude` / `longitude` attributes, making them directly usable in the HA Map card with `label_mode: state` to display quality level at each beach pin.

### Binary sensors
- **Lifeguard Present**
- **Out of Season**
- **Water Quality Good**
- **Jellyfish Alert**
- **Rain Risk High**

### Button
- **Refresh** button; attributes: `last_fetched`

### Services
- `refresh_all`, `refresh_beach` (action-oriented UI can expose these)

## UI recommendations (built-in Lovelace cards)
### 1) At-a-glance summary
**Tile / Entities / Glance** card with:
- Water temp, air temp, UV, wave height, wind speed
- Water quality + jellyfish alert + lifeguard present

### 2) Hero visual
**Picture-Entity** using `sensor.<beach>_beach_name` (uses `entity_picture`):
- Display primary beach image with the beach name
- Combine with **Markdown** or **Entity** card for description/alerts

### 3) Trends
**History Graph**:
- Water temp, air temp, wind speed, UV index
**Statistics Graph** (if long-term trends are important)

### 4) Risk & safety status
- **Conditional** card or **Binary Sensor** tiles:
  - Water quality good / jellyfish alert / rain risk / out of season
- **Gauge** for UV Index with warning thresholds

### 5) Details and explanation
- **Markdown** card with:
  - `description`, `beach_info`, water quality `estado_info`
  - Helpful during out-of-season or rain disturbance events

### 6) Map card (built-in)
- The Home Assistant **Map** card only shows entities with `latitude`/`longitude` attributes (our `sensor.<beach>_beach_name` includes them).
- Best practice: enable `auto_fit` so the viewport fits all beaches, and use `label_mode: state` to show the beach name.
- Optional: set `show_all: true` if you want every beach name sensor with coordinates to appear automatically.

## Bubble Card dashboard concepts
### A) Beach overview bubble
- **Bubble Card: Button**
  - Main icon = beach
  - Sub-buttons for quick metrics: water temp, air temp, UV, water quality
  - Conditional sub-buttons for alerts: jellyfish, rain risk, out of season

### B) Pop-up details
- **Bubble Card: Pop-up**
  - Triggered from the overview bubble
  - Contents: picture-entity (beach image), detailed entities list, history graph, markdown description, jellyfish species list

### C) Quick actions
- **Bubble Card: Sub-buttons only** or **Horizontal buttons stack**
  - Refresh button
  - Service calls for `refresh_all` / `refresh_beach`

## NSW Beachwatch-inspired layouts (adapted to our data)
Based on the dashboard examples in https://github.com/PlanetCitizen1829381/ha-nsw-beachwatch, the following patterns map well to this integration (using Bubble Card where possible).

### 1) Short advice card (Bubble Card + card-mod)
**Goal:** A compact status banner that highlights current conditions.  
**Adaptation:** Use `sensor.<beach>_water_quality` or `sensor.<beach>_beach_info` as the main state.  
**Visual cues:** Color the icon background based on `binary_sensor.<beach>_water_quality_good`, `binary_sensor.<beach>_jellyfish_alert`, or `binary_sensor.<beach>_rain_risk_high`.  
**Use available icons:** Show `icon_water_*` and `icon_jellyfish_*` URLs as inline images in a Markdown block beneath the Bubble Card.

### 2) Extended advice card (Bubble Card + Entities)
**Goal:** Large informative card with detailed context.  
**Adaptation:** Vertical stack:
- **Bubble Card button**: status + icon, use `sensor.<beach>_beach_info` or `sensor.<beach>_water_quality`.
- **Entities card**: list `water_temperature`, `air_temperature`, `uv_index`, `wave_height`, `wind_speed`, `sky_condition`.
- **Attributes section**: `test_date`, `test_estado`, `estado_info`, `jellyfish_status` and species list.

### 3) Flat summary card (Entities)
**Goal:** Compact list of essential metrics.  
**Adaptation:** Entities card with:
- `sensor.<beach>_water_temperature`, `sensor.<beach>_air_temperature`
- `sensor.<beach>_uv_index`, `sensor.<beach>_wave_height`, `sensor.<beach>_wind_speed`
- `sensor.<beach>_water_quality`, `binary_sensor.<beach>_jellyfish_alert`
- Attributes: `test_date`, `estado_info`

### 4) Map card (built-in)
**Goal:** Multi-beach overview with state labels.  
**Adaptation:** Map card using the beach name sensors (they carry coordinates), `label_mode: state`.  
**Requires:** latitude/longitude attributes on the selected entities.

Example:
```yaml
type: map
title: Catalunya beaches
auto_fit: true
entities:
  - entity: sensor.platja_de_barcelona_beach_name
    name: Platja de Barcelona
    label_mode: state
  - entity: sensor.platja_de_la_nova_mar_bella_beach_name
    name: Platja de la Nova Mar Bella
    label_mode: state
```

## Visualization ideas using existing data
1. **Image-centric tile**: use `entity_picture` + beach name as a hero header.
2. **Icon strip**: show official water/jellyfish icon URLs (`icon_water_*`, `icon_jellyfish_*`) in markdown or picture-elements.
3. **Risk ribbon**: color-coded badges based on binary sensors (lifeguard, rain risk, out of season).
4. **Trend section**: water temp + wind speed + UV history graph.
5. **Data freshness**: surface `last_fetched` attribute from refresh button or coordinator.

## Implemented integration improvements (UI-related)
1. ✅ Translation step IDs aligned between flow and translations.
2. ✅ Error keys aligned between flow and translations.
3. ✅ Options flow treats `force_refresh`/`delete_history` as action-only.
4. ✅ Device entry type uses `DeviceEntryType.SERVICE`.
5. ✅ Coordinates exposed for map cards.
6. ✅ Water quality/jellyfish states normalized for translation keys.
7. ✅ Wind speed unit aligned to km/h.
8. ✅ Detected image/icon assets cached locally and exposed with token-free `/local/...` URLs.

## Suggested "starter" UI layouts
### Minimal
- Picture-entity (beach image + name)
- Entities card (temps, UV, water quality, lifeguard)

### Safety-focused
- Binary sensor tiles (lifeguard, water quality good, jellyfish alert, rain risk)
- Gauge (UV)
- Entities (water temp, wave height, wind speed)

### Detailed / dashboard
- Picture-entity header
- Entities + history graph
- Markdown (description + beach info)
- Bubble Card pop-up for detailed attributes
