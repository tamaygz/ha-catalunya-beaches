## Plan: Catalan Beaches Integration for Home Assistant

Build a production-ready Home Assistant integration that enables users to monitor Catalan beaches as individual devices, with configurable entities tracking water quality, weather conditions, jellyfish presence, and other real-time beach data from the Catalan Water Agency API.

### Steps

1. **Rewrite API client** in [`api.py`](custom_components/ha-catalunya-beaches/api.py) to fetch beach list from `/api/front/en` and individual beach details from `/api/playadetalle/{beach_id}/en`, replacing JSONPlaceholder authentication with proper error handling for the government API

2. **Create data models** in [`data.py`](custom_components/ha-catalunya-beaches/data.py) with dataclasses for `BeachInfo`, `WaterQuality`, `WeatherConditions`, `JellyfishStatus`, and `BeachConfig` to properly parse the nested JSON responses

3. **Implement config flow** in [`config_flow.py`](custom_components/ha-catalunya-beaches/config_flow.py) allowing users to select beaches from fetched list, set global update interval (default 1 hour), and configure which entities to create (checkboxes for water temp, air temp, quality, jellyfish, UV, waves, etc.)

4. **Build options flow** in [`config_flow.py`](custom_components/ha-catalunya-beaches/config_flow.py) enabling per-beach update interval overrides, entity selection modification (with auto-cleanup of disabled entities), force refresh action, and delete historical data action

5. **Redesign coordinator** in [`coordinator.py`](custom_components/ha-catalunya-beaches/coordinator.py) to fetch individual beach details on schedule, handle per-beach update intervals, and manage partial failures gracefully

6. **Create sensor platform** in [`sensor.py`](custom_components/ha-catalunya-beaches/sensor.py) with dynamic entity generation based on user config: water temperature, air temperature, water quality status, UV index, wave height, wind speed, sky condition, jellyfish status, last test date (timestamp), beach description (diagnostic)

7. **Create binary sensor platform** in [`binary_sensor.py`](custom_components/ha-catalunya-beaches/binary_sensor.py) with lifeguard present, out of season, water quality good, jellyfish alert, and rain risk entities based on user configuration

8. **Remove switch platform** (`switch.py`) entirely as beach data is read-only with no controllable actions

9. **Update translations** in [`translations/en.json`](custom_components/ha-catalunya-beaches/translations/en.json) and add Catalan (`ca.json`) with entity names, state mappings for coded values (`_FORA_DE_TEMPORADA_`, sand types, sky conditions), config flow labels, and option flow text

10. **Update constants** in [`const.py`](custom_components/ha-catalunya-beaches/const.py) with API base URL, endpoint templates, default intervals (3600s), icon mappings for conditions, and translation dictionaries for API codes

11. **Update manifest and docs** in [`manifest.json`](custom_components/ha-catalunya-beaches/manifest.json) and [`README.md`](README.md) with correct domain, author info, IoT class (`cloud_polling`), requirements, and comprehensive usage documentation

### Further Considerations

1. **Entity registry cleanup** - Implement proper `async_remove_config_entry_device` and entity deregistration when beaches are removed or entities unchecked? Option A: Manual cleanup / Option B: Automatic with orphan detection / **Option C: Both with user confirmation**

2. **API rate limiting strategy** - No documented limits found, but implement exponential backoff? Option A: Aggressive (5min retry) / **Option B: Conservative (30min retry)** / Option C: User-configurable

3. **Image handling** - Beach images available via `imagen_url` field. Option A: Download and cache locally / **Option B: Provide URLs as attributes only** / Option C: Optional thumbnail download

4. **Historical data storage** - "Delete historical data" feature scope? Option A: Clear entity states only / **Option B: Remove from recorder/history DB** / Option C: Full entity recreation

5. **Multi-language support** - API supports `/en` and presumably `/ca` endpoints. **Implement language selection in config?** Or follow HA's locale setting?
