"""Binary sensor platform for Catalunya Beaches."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import (
    CONF_ENABLED_ENTITIES,
    ENTITY_JELLYFISH_ALERT,
    ENTITY_LIFEGUARD,
    ENTITY_OUT_OF_SEASON,
    ENTITY_RAIN_RISK,
    ENTITY_WATER_QUALITY_GOOD,
    LIFEGUARD_STATUS,
    LOGGER,
    RISK_LEVELS,
)
from .entity import CatalunyaBeachEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import CatalunyaBeachesConfigEntry


BINARY_SENSOR_TYPES: dict[str, BinarySensorEntityDescription] = {
    ENTITY_LIFEGUARD: BinarySensorEntityDescription(
        key=ENTITY_LIFEGUARD,
        name="Lifeguard Present",
        device_class=BinarySensorDeviceClass.SAFETY,
        icon="mdi:lifeguard",
    ),
    ENTITY_OUT_OF_SEASON: BinarySensorEntityDescription(
        key=ENTITY_OUT_OF_SEASON,
        name="Out of Season",
        icon="mdi:calendar-remove",
    ),
    ENTITY_WATER_QUALITY_GOOD: BinarySensorEntityDescription(
        key=ENTITY_WATER_QUALITY_GOOD,
        name="Water Quality Good",
        device_class=BinarySensorDeviceClass.SAFETY,
        icon="mdi:water-check",
    ),
    ENTITY_JELLYFISH_ALERT: BinarySensorEntityDescription(
        key=ENTITY_JELLYFISH_ALERT,
        name="Jellyfish Alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:jellyfish",
    ),
    ENTITY_RAIN_RISK: BinarySensorEntityDescription(
        key=ENTITY_RAIN_RISK,
        name="High Rain Risk",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:weather-rainy",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CatalunyaBeachesConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Catalunya Beaches binary sensor platform."""
    enabled_entities = entry.options.get(CONF_ENABLED_ENTITIES, [])
    
    binary_sensors = []
    for entity_type, description in BINARY_SENSOR_TYPES.items():
        if entity_type in enabled_entities:
            binary_sensors.append(
                CatalunyaBeachBinarySensor(
                    coordinator=entry.runtime_data.coordinator,
                    entity_description=description,
                    beach_id=entry.data["beach_id"],
                    beach_name=entry.data["beach_name"],
                )
            )
    
    LOGGER.debug("Setting up %d binary sensors for beach %s", len(binary_sensors), entry.data["beach_name"])
    async_add_entities(binary_sensors)


class CatalunyaBeachBinarySensor(CatalunyaBeachEntity, BinarySensorEntity):
    """Binary sensor for Catalunya Beach data."""

    def __init__(
        self,
        coordinator,
        entity_description: BinarySensorEntityDescription,
        beach_id: int,
        beach_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, beach_id, beach_name)
        self.entity_description = entity_description
        self._attr_unique_id = f"{beach_id}_{entity_description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None

        beach_info = self.coordinator.data
        key = self.entity_description.key

        try:
            if key == ENTITY_LIFEGUARD:
                if beach_info.caracteristicas_fisicas:
                    socorrismo = beach_info.caracteristicas_fisicas.socorrismo
                    return LIFEGUARD_STATUS.get(socorrismo, False)
                return None

            elif key == ENTITY_OUT_OF_SEASON:
                return beach_info.fora_temporada

            elif key == ENTITY_WATER_QUALITY_GOOD:
                if beach_info.calidad_playa:
                    estado = beach_info.calidad_playa.estado
                    # Consider "Excellent" and "Good" as good quality
                    return estado in ["Excellent", "Good"]
                return None

            elif key == ENTITY_JELLYFISH_ALERT:
                if beach_info.medusas:
                    peligrosidad = beach_info.medusas.peligrosidad_etiqueta
                    # Alert if not "Out of season" and has any danger indication
                    if peligrosidad and peligrosidad != "_FORA_DE_TEMPORADA_":
                        # Alert if there are any jellyfish species detected
                        return len(beach_info.medusas.especies) > 0
                return False

            elif key == ENTITY_RAIN_RISK:
                if beach_info.caracteristicas_ambientales:
                    riesgo = beach_info.caracteristicas_ambientales.riesgo_lluvia
                    return RISK_LEVELS.get(riesgo, "low") == "high"
                return None

        except (AttributeError, KeyError) as err:
            LOGGER.debug("Error getting binary sensor value for %s: %s", key, err)
            return None

        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        beach_info = self.coordinator.data
        key = self.entity_description.key
        attributes = {}

        try:
            if key == ENTITY_JELLYFISH_ALERT and beach_info.medusas:
                if beach_info.medusas.especies:
                    attributes["species_count"] = len(beach_info.medusas.especies)
                    attributes["species"] = beach_info.medusas.especies
                attributes["danger_level"] = beach_info.medusas.peligrosidad

            elif key == ENTITY_WATER_QUALITY_GOOD and beach_info.calidad_playa:
                attributes["status"] = beach_info.calidad_playa.estado
                attributes["status_info"] = beach_info.calidad_playa.estado_info

            elif key == ENTITY_RAIN_RISK and beach_info.caracteristicas_ambientales:
                attributes["risk_level"] = beach_info.caracteristicas_ambientales.riesgo_lluvia
                attributes["phytoplankton_risk"] = beach_info.caracteristicas_ambientales.riesgo_fitoplancton

        except (AttributeError, KeyError) as err:
            LOGGER.debug("Error getting attributes for %s: %s", key, err)

        return attributes
