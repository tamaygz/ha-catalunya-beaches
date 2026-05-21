"""Sensor platform for Catalunya Beaches."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfLength, UnitOfSpeed
from homeassistant.helpers.typing import StateType

from .const import (
    CONF_BEACH_LATITUDE,
    CONF_BEACH_LONGITUDE,
    CONF_ENABLED_ENTITIES,
    ENTITY_AIR_TEMP,
    ENTITY_BEACH_INFO,
    ENTITY_BEACH_NAME,
    ENTITY_DESCRIPTION,
    ENTITY_JELLYFISH_STATUS,
    ENTITY_LAST_TEST_DATE,
    ENTITY_SKY_CONDITION,
    ENTITY_UV_INDEX,
    ENTITY_WATER_QUALITY,
    ENTITY_WATER_TEMP,
    ENTITY_WAVE_HEIGHT,
    ENTITY_WIND_SPEED,
    LOGGER,
    SKY_CONDITIONS,
    WATER_QUALITY_STATUS,
)
from .entity import CatalunyaBeachEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import CatalunyaBeachesConfigEntry


SENSOR_TYPES: dict[str, SensorEntityDescription] = {
    ENTITY_WATER_TEMP: SensorEntityDescription(
        key=ENTITY_WATER_TEMP,
        name="Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-thermometer",
    ),
    ENTITY_AIR_TEMP: SensorEntityDescription(
        key=ENTITY_AIR_TEMP,
        name="Air Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    ENTITY_WATER_QUALITY: SensorEntityDescription(
        key=ENTITY_WATER_QUALITY,
        name="Water Quality",
        icon="mdi:water-check",
    ),
    ENTITY_UV_INDEX: SensorEntityDescription(
        key=ENTITY_UV_INDEX,
        name="UV Index",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sun-wireless",
    ),
    ENTITY_WAVE_HEIGHT: SensorEntityDescription(
        key=ENTITY_WAVE_HEIGHT,
        name="Wave Height",
        native_unit_of_measurement=UnitOfLength.METERS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:wave",
    ),
    ENTITY_WIND_SPEED: SensorEntityDescription(
        key=ENTITY_WIND_SPEED,
        name="Wind Speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-windy",
    ),
    ENTITY_SKY_CONDITION: SensorEntityDescription(
        key=ENTITY_SKY_CONDITION,
        name="Sky Condition",
        icon="mdi:weather-partly-cloudy",
    ),
    ENTITY_JELLYFISH_STATUS: SensorEntityDescription(
        key=ENTITY_JELLYFISH_STATUS,
        name="Jellyfish Status",
        icon="mdi:jellyfish",
    ),
    ENTITY_LAST_TEST_DATE: SensorEntityDescription(
        key=ENTITY_LAST_TEST_DATE,
        name="Last Water Test",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:calendar-clock",
    ),
    ENTITY_DESCRIPTION: SensorEntityDescription(
        key=ENTITY_DESCRIPTION,
        name="Description",
        icon="mdi:information",
    ),
    ENTITY_BEACH_INFO: SensorEntityDescription(
        key=ENTITY_BEACH_INFO,
        name="Beach Info",
        icon="mdi:alert-circle-outline",
    ),
    ENTITY_BEACH_NAME: SensorEntityDescription(
        key=ENTITY_BEACH_NAME,
        name="Beach Name",
        icon="mdi:beach",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CatalunyaBeachesConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Catalunya Beaches sensor platform."""
    enabled_entities = entry.options.get(CONF_ENABLED_ENTITIES, [])

    sensors = []

    # Always add beach name sensor (not configurable)
    sensors.append(
        CatalunyaBeachSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=SENSOR_TYPES[ENTITY_BEACH_NAME],
            beach_id=entry.data["beach_id"],
            beach_name=entry.data["beach_name"],
        )
    )

    # Add configurable sensors
    for entity_type, description in SENSOR_TYPES.items():
        if entity_type == ENTITY_BEACH_NAME:
            continue  # Already added above
        if entity_type in enabled_entities:
            sensors.append(
                CatalunyaBeachSensor(
                    coordinator=entry.runtime_data.coordinator,
                    entity_description=description,
                    beach_id=entry.data["beach_id"],
                    beach_name=entry.data["beach_name"],
                )
            )

    LOGGER.debug(
        "Setting up %d sensors for beach %s", len(sensors), entry.data["beach_name"]
    )
    async_add_entities(sensors)


class CatalunyaBeachSensor(CatalunyaBeachEntity, SensorEntity):
    """Sensor for Catalunya Beach data."""

    def __init__(
        self,
        coordinator,
        entity_description: SensorEntityDescription,
        beach_id: int,
        beach_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, beach_id, beach_name)
        self.entity_description = entity_description
        self._attr_unique_id = f"{beach_id}_{entity_description.key}"

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        beach_info = self.coordinator.data
        key = self.entity_description.key

        try:
            if key == ENTITY_WATER_TEMP:
                if beach_info.condiciones and beach_info.condiciones.temperatura_agua:
                    return round(beach_info.condiciones.temperatura_agua, 1)
                # Fallback to latest test result
                if beach_info.ultimos_analisis:
                    latest = beach_info.ultimos_analisis[0]
                    if latest.temperatura_agua:
                        return round(latest.temperatura_agua, 1)
                return None

            elif key == ENTITY_AIR_TEMP:
                if beach_info.condiciones and beach_info.condiciones.temperatura:
                    return round(beach_info.condiciones.temperatura, 1)
                return None

            elif key == ENTITY_WATER_QUALITY:
                if beach_info.calidad_playa:
                    estado = beach_info.calidad_playa.estado
                    return WATER_QUALITY_STATUS.get(estado, estado)
                return None

            elif key == ENTITY_UV_INDEX:
                if (
                    beach_info.condiciones
                    and beach_info.condiciones.uv_maximo is not None
                ):
                    return beach_info.condiciones.uv_maximo
                return None

            elif key == ENTITY_WAVE_HEIGHT:
                if (
                    beach_info.condiciones
                    and beach_info.condiciones.altura_olas is not None
                ):
                    return round(beach_info.condiciones.altura_olas, 2)
                return None

            elif key == ENTITY_WIND_SPEED:
                if (
                    beach_info.condiciones
                    and beach_info.condiciones.velocidad_viento is not None
                ):
                    return round(beach_info.condiciones.velocidad_viento, 1)
                return None

            elif key == ENTITY_SKY_CONDITION:
                if beach_info.condiciones:
                    if beach_info.condiciones.cielo_traduccion:
                        return beach_info.condiciones.cielo_traduccion
                    etiqueta = beach_info.condiciones.cielo_etiqueta
                    return SKY_CONDITIONS.get(etiqueta, etiqueta)
                return None

            elif key == ENTITY_JELLYFISH_STATUS:
                if beach_info.medusas:
                    return beach_info.medusas.peligrosidad or "Unknown"
                return None

            elif key == ENTITY_LAST_TEST_DATE:
                if beach_info.ultimos_analisis:
                    latest = beach_info.ultimos_analisis[0]
                    if latest.fecha:
                        return latest.fecha
                return None

            elif key == ENTITY_DESCRIPTION:
                # Description can be very long, so truncate state to 255 chars
                # and put full text in attributes
                if beach_info.descripcion:
                    desc = beach_info.descripcion.strip()
                    # Return truncated version for state (max 255 chars)
                    if len(desc) > 252:  # Leave room for "..."
                        return desc[:252] + "..."
                    return desc
                return None

            elif key == ENTITY_BEACH_INFO:
                # Beach info from descriptionToast
                if beach_info.descripcion_toast:
                    return beach_info.descripcion_toast.strip()
                return None

            elif key == ENTITY_BEACH_NAME:
                # Beach name - always available
                return beach_info.nombre or None

        except (AttributeError, IndexError, KeyError) as err:
            LOGGER.debug("Error getting sensor value for %s: %s", key, err)
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
            if key == ENTITY_WATER_QUALITY:
                if beach_info.calidad_playa:
                    attributes["estado_info"] = beach_info.calidad_playa.estado_info
                    if beach_info.calidad_playa.a_destacar:
                        attributes["destacar"] = beach_info.calidad_playa.a_destacar
                    if beach_info.calidad_playa.timestamp:
                        attributes["last_update"] = (
                            beach_info.calidad_playa.timestamp.isoformat()
                        )

            elif key == ENTITY_JELLYFISH_STATUS:
                if beach_info.medusas:
                    attributes["danger_level"] = (
                        beach_info.medusas.peligrosidad_etiqueta
                    )
                    if beach_info.medusas.especies:
                        attributes["species"] = beach_info.medusas.especies
                    if beach_info.medusas.fecha_modificacion:
                        attributes["last_update"] = (
                            beach_info.medusas.fecha_modificacion.isoformat()
                        )

            elif key == ENTITY_WATER_TEMP and beach_info.ultimos_analisis:
                latest = beach_info.ultimos_analisis[0]
                attributes["test_estado"] = latest.estado
                if latest.fecha:
                    attributes["test_date"] = latest.fecha.isoformat()

            elif key == ENTITY_UV_INDEX and beach_info.condiciones:
                if beach_info.condiciones.uv_minimo is not None:
                    attributes["uv_min"] = beach_info.condiciones.uv_minimo

            elif key == ENTITY_WIND_SPEED and beach_info.condiciones:
                if beach_info.condiciones.direccion_viento is not None:
                    attributes["direction"] = round(
                        beach_info.condiciones.direccion_viento, 1
                    )

            elif key == ENTITY_DESCRIPTION and beach_info.descripcion:
                # Store full description in attributes since state is truncated
                attributes["full_description"] = beach_info.descripcion.strip()
                attributes["length"] = len(beach_info.descripcion)

            elif key == ENTITY_BEACH_NAME:
                # Add beach ID as attribute
                attributes["beach_id"] = beach_info.id
                attributes["municipality"] = beach_info.municipio
                attributes["coast"] = beach_info.costa

                latitude = None
                longitude = None
                if beach_info.coordenadas:
                    latitude, longitude = beach_info.coordenadas
                else:
                    latitude = self.coordinator.config_entry.data.get(
                        CONF_BEACH_LATITUDE
                    )
                    longitude = self.coordinator.config_entry.data.get(
                        CONF_BEACH_LONGITUDE
                    )

                if isinstance(latitude, str):
                    try:
                        latitude = float(latitude)
                    except ValueError:
                        latitude = None
                if isinstance(longitude, str):
                    try:
                        longitude = float(longitude)
                    except ValueError:
                        longitude = None

                if latitude is not None and longitude is not None:
                    attributes["latitude"] = latitude
                    attributes["longitude"] = longitude

                # Add images and icons
                if beach_info.imagenes:
                    attributes["images"] = beach_info.imagenes
                    attributes["image_count"] = len(beach_info.imagenes)
                    attributes["primary_image"] = (
                        beach_info.imagenes[0] if beach_info.imagenes else None
                    )

                if beach_info.iconos:
                    # Water quality icons
                    attributes["icon_water_no_info"] = beach_info.iconos.get(
                        "estat_aigua_noinfo"
                    )
                    attributes["icon_water_good"] = beach_info.iconos.get(
                        "estat_aigua_bona"
                    )
                    attributes["icon_water_caution"] = beach_info.iconos.get(
                        "estat_aigua_precauci"
                    )

                    # Jellyfish icons
                    attributes["icon_jellyfish_none"] = beach_info.iconos.get(
                        "meduses_sense_presencia"
                    )
                    attributes["icon_jellyfish_safe"] = beach_info.iconos.get(
                        "meduses_sense_perill"
                    )
                    attributes["icon_jellyfish_danger"] = beach_info.iconos.get(
                        "meduses_amb_perill"
                    )
                    attributes["icon_jellyfish_high_danger"] = beach_info.iconos.get(
                        "meduses_molt_perill"
                    )
                    attributes["icon_jellyfish_no_info"] = beach_info.iconos.get(
                        "meduses_noinfo"
                    )

        except (AttributeError, KeyError) as err:
            LOGGER.debug("Error getting attributes for %s: %s", key, err)

        return attributes

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture for the beach name sensor."""
        # Only add picture to beach_name sensor
        if self.entity_description.key != ENTITY_BEACH_NAME:
            return None

        if not self.coordinator.data:
            return None

        beach_info = self.coordinator.data
        if beach_info.imagenes and len(beach_info.imagenes) > 0:
            # Return the first (primary) image URL
            return f"https://aca-web.gencat.cat/images/platges/{beach_info.imagenes[0]}"

        return None
