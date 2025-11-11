Goal: Creating a homeassistant integration that lets a user setup "beach" devices for (catalan) beaches of interest. A beach device contains many configurable entities (information sensors based on the data available).

API:
To receive a list of all trackable beaches, query: https://aplicacions.aca.gencat.cat/platgescat2/agencia-catalana-del-agua-backend/web/app.php/api/front/en

To receive real time data of a beach, query with corresponding beach_id:
https://aplicacions.aca.gencat.cat/platgescat2/agencia-catalana-del-agua-backend/web/app.php/api/playadetalle/{beach_id}/en

Requirements:
- User should be able to use homeassistant config flow to setup monitored beaches (1 beach = 1 device)
- User can add, edit, remove beaches
- User can configure global polling interval
- User can configure (override global) polling interval per beach (if not set, global applies)
- User can configure which datapoints to load as entities per beach (checkboxes per data item)
- Each beach device self updates using above api spec and keeps its entities in updated & in order to config
- If data items have been unselected from monitoring via config flow, old monitoring entities should be removed from the system (autoclean)
- When a beach device is removed, the addon correctly deletes all related entities
- Offer a force refresh via configflow of a beach device
- Offer a delete all historic data via configflow of a beach device


Reference documentation of hacs and homeassistant:
Creating a Integration : https://developers.home-assistant.io/docs/creating_component_index
Config Flow : https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
Options Flow : https://developers.home-assistant.io/docs/config_entries_options_flow_handler
Fetching Data : https://developers.home-assistant.io/docs/integration_fetching_data
Hacs Documentation : https://hacs.xyz/docs/publish/integration/#ok-example
