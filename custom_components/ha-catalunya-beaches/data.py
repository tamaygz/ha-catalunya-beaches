"""Custom types for ha-catalunya-beaches."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import CatalunyaBeachesApiClient
    from .coordinator import BeachDataUpdateCoordinator

type CatalunyaBeachesConfigEntry = ConfigEntry[CatalunyaBeachesData]


@dataclass
class CatalunyaBeachesData:
    """Data for the Catalunya Beaches integration."""

    client: CatalunyaBeachesApiClient
    coordinator: BeachDataUpdateCoordinator
    integration: Integration


@dataclass
class BeachListItem:
    """Beach information from the beach list API."""

    id: int
    nombre: str
    descripcion: str
    imagen_url: str
    tipoarena: str
    temperaturaagua: float | None
    estadocielo: str
    comarca: str
    costa: str
    municipio: str
    longitud: str
    latitud: str
    calidadaguaetiqueta: str
    vigilanciaysocorrismo: str
    medusaetiqueta: str | None
    medusasliteral: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BeachListItem:
        """Create BeachListItem from API response dict."""
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            descripcion=data.get("descripcion", ""),
            imagen_url=data.get("imagen_url", ""),
            tipoarena=data.get("tipoarena", ""),
            temperaturaagua=float(data["temperaturaagua"])
            if data.get("temperaturaagua")
            else None,
            estadocielo=data.get("estadocielo", ""),
            comarca=data.get("comarca", ""),
            costa=data.get("costa", ""),
            municipio=data.get("municipio", ""),
            longitud=data.get("longitud", ""),
            latitud=data.get("latitud", ""),
            calidadaguaetiqueta=data.get("calidadaguaetiqueta", ""),
            vigilanciaysocorrismo=data.get("vigilanciaysocorrismo", ""),
            medusaetiqueta=data.get("medusaetiqueta"),
            medusasliteral=data.get("medusasliteral"),
        )


@dataclass
class WaterQuality:
    """Water quality information."""

    estado: str
    estado_info: str
    a_destacar: str | None
    timestamp: datetime | None
    icono: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WaterQuality:
        """Create WaterQuality from API response dict."""
        timestamp = None
        if ts_data := data.get("timestamp_calidad"):
            if isinstance(ts_data, dict) and "date" in ts_data:
                try:
                    dt_str = ts_data["date"].replace(".000000", "")
                    timestamp = datetime.fromisoformat(dt_str)
                    # Ensure timezone is set (use Europe/Madrid if not present)
                    if timestamp.tzinfo is None:
                        tz = ZoneInfo(ts_data.get("timezone", "Europe/Madrid"))
                        timestamp = timestamp.replace(tzinfo=tz)
                except (ValueError, AttributeError, KeyError):
                    pass

        return cls(
            estado=data.get("estado", ""),
            estado_info=data.get("estado_info", ""),
            a_destacar=data.get("a_destacar"),
            timestamp=timestamp,
            icono=data.get("icono", ""),
        )


@dataclass
class JellyfishStatus:
    """Jellyfish information."""

    peligrosidad: str
    peligrosidad_etiqueta: str
    icono: str
    fecha_modificacion: datetime | None
    especies: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JellyfishStatus:
        """Create JellyfishStatus from API response dict."""
        fecha_modificacion = None
        if fecha_data := data.get("fechaModificacion"):
            if isinstance(fecha_data, dict) and "date" in fecha_data:
                try:
                    dt_str = fecha_data["date"].replace(".000000", "")
                    fecha_modificacion = datetime.fromisoformat(dt_str)
                    # Ensure timezone is set (use Europe/Madrid if not present)
                    if fecha_modificacion.tzinfo is None:
                        tz = ZoneInfo(fecha_data.get("timezone", "Europe/Madrid"))
                        fecha_modificacion = fecha_modificacion.replace(tzinfo=tz)
                except (ValueError, AttributeError, KeyError):
                    pass

        return cls(
            peligrosidad=data.get("peligrosidadTrad", ""),
            peligrosidad_etiqueta=data.get("peligrosidadEtiqueta", ""),
            icono=data.get("icono", ""),
            fecha_modificacion=fecha_modificacion,
            especies=data.get("llistatMeduses", []),
        )


@dataclass
class WeatherConditions:
    """Current weather and sea conditions."""

    temperatura: float | None
    temperatura_agua: float | None
    cielo_etiqueta: str
    cielo_traduccion: str
    altura_olas: float | None
    velocidad_viento: float | None
    direccion_viento: float | None
    uv_minimo: int | None
    uv_maximo: int | None
    fecha: str
    hora: str

    @classmethod
    def from_dict(
        cls, estado_playa: dict[str, Any], estado_mar: dict[str, Any]
    ) -> WeatherConditions:
        """Create WeatherConditions from API response dicts."""
        return cls(
            temperatura=float(estado_playa["temperatura"])
            if estado_playa.get("temperatura")
            else None,
            temperatura_agua=float(estado_playa["temperaturaAgua"])
            if estado_playa.get("temperaturaAgua")
            else None,
            cielo_etiqueta=estado_playa.get("etiquetaCielo", ""),
            cielo_traduccion=estado_playa.get("traduccionCielo", ""),
            altura_olas=float(estado_mar["alturaolas"])
            if estado_mar.get("alturaolas")
            else None,
            velocidad_viento=float(estado_mar["velocidadviento"])
            if estado_mar.get("velocidadviento")
            else None,
            direccion_viento=float(estado_mar["direccionviento"])
            if estado_mar.get("direccionviento")
            else None,
            uv_minimo=int(estado_mar["uvminimo"])
            if estado_mar.get("uvminimo")
            else None,
            uv_maximo=int(estado_mar["uvmaximo"])
            if estado_mar.get("uvmaximo")
            else None,
            fecha=estado_playa.get("fecha", ""),
            hora=estado_playa.get("hora", ""),
        )


@dataclass
class BeachCharacteristics:
    """Physical characteristics of the beach."""

    tipo_playa: str
    tipo_arena: str
    entorno: str
    orientacion: str
    longitud: str
    anchura_media: str
    socorrismo: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BeachCharacteristics:
        """Create BeachCharacteristics from API response dict."""
        return cls(
            tipo_playa=data.get("tipoplaya", ""),
            tipo_arena=data.get("tipoarena", ""),
            entorno=data.get("entorno", ""),
            orientacion=data.get("orientacion", ""),
            longitud=data.get("longitud", ""),
            anchura_media=data.get("anchuramedia", ""),
            socorrismo=data.get("socorrismo", ""),
        )


@dataclass
class EnvironmentalCharacteristics:
    """Environmental characteristics and risks."""

    riesgo_lluvia: str
    riesgo_fitoplancton: str
    temp_media_junio: float | None
    temp_media_julio: float | None
    temp_media_agosto: float | None
    temp_media_septiembre: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvironmentalCharacteristics:
        """Create EnvironmentalCharacteristics from API response dict."""
        return cls(
            riesgo_lluvia=data.get("riesgoalteracioncalidadporlluvias", ""),
            riesgo_fitoplancton=data.get("riesgoproliferacionfitoplacton", ""),
            temp_media_junio=float(data["temperaturamediaaguajunio"])
            if data.get("temperaturamediaaguajunio")
            else None,
            temp_media_julio=float(data["temperaturamediaaguajulio"])
            if data.get("temperaturamediaaguajulio")
            else None,
            temp_media_agosto=float(data["temperaturamediaaguaagosto"])
            if data.get("temperaturamediaaguaagosto")
            else None,
            temp_media_septiembre=float(data["temperaturamediaaguaseptiembre"])
            if data.get("temperaturamediaaguaseptiembre")
            else None,
        )


@dataclass
class WaterTestResult:
    """Individual water test result."""

    fecha: datetime | None
    temperatura_agua: float | None
    estado: str
    ef: int | None
    ec: int | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WaterTestResult:
        """Create WaterTestResult from API response dict."""
        fecha = None
        if fecha_data := data.get("fechadato"):
            if isinstance(fecha_data, dict) and "date" in fecha_data:
                try:
                    dt_str = fecha_data["date"].replace(".000000", "")
                    fecha = datetime.fromisoformat(dt_str)
                    # Ensure timezone is set (use Europe/Madrid if not present)
                    if fecha.tzinfo is None:
                        tz = ZoneInfo(fecha_data.get("timezone", "Europe/Madrid"))
                        fecha = fecha.replace(tzinfo=tz)
                except (ValueError, AttributeError, KeyError):
                    pass

        return cls(
            fecha=fecha,
            temperatura_agua=float(data["temperaturaagua"])
            if data.get("temperaturaagua")
            else None,
            estado=data.get("codigoestado", ""),
            ef=int(data["ef"]) if data.get("ef") else None,
            ec=int(data["ec"]) if data.get("ec") else None,
        )


@dataclass
class BeachInfo:
    """Complete beach information from detail API."""

    id: int
    nombre: str
    descripcion: str
    municipio: str
    costa: str
    coordenadas: tuple[float, float] | None
    fora_temporada: bool
    imagenes: list[str]
    calidad_playa: WaterQuality | None
    medusas: JellyfishStatus | None
    condiciones: WeatherConditions | None
    caracteristicas_fisicas: BeachCharacteristics | None
    caracteristicas_ambientales: EnvironmentalCharacteristics | None
    ultimos_analisis: list[WaterTestResult]
    playascercanas: list[dict[str, Any]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BeachInfo:
        """Create BeachInfo from API response dict."""
        items = data.get("items", {})
        playa = items.get("playa", {})

        # Check if beach exists
        if playa.get("existe") == "N":
            msg = "Beach does not exist"
            raise ValueError(msg)

        # Extract coordinates
        coordenadas = None
        if coords := playa.get("coordenadasPC"):
            if coords and isinstance(coords, list) and len(coords) > 0:
                try:
                    coordenadas = (
                        float(coords[0].get("coordenaday", 0)),
                        float(coords[0].get("coordenadax", 0)),
                    )
                except (ValueError, KeyError, TypeError):
                    pass

        # Extract images
        imagenes = []
        if imgs := playa.get("imatgesPlatja"):
            imagenes = [img.get("url", "") for img in imgs if img.get("url")]

        # Parse nested structures
        calidad_playa = None
        if calidad_data := items.get("calidadPlaya"):
            calidad_playa = WaterQuality.from_dict(calidad_data)

        medusas = None
        if medusas_data := items.get("medusas"):
            medusas = JellyfishStatus.from_dict(medusas_data)

        condiciones = None
        if items.get("estadoPlaya") and items.get("estadoMar"):
            condiciones = WeatherConditions.from_dict(
                items["estadoPlaya"],
                items["estadoMar"],
            )

        caracteristicas_fisicas = None
        if fisicas := playa.get("caracteristicasFisicas"):
            caracteristicas_fisicas = BeachCharacteristics.from_dict(fisicas)

        caracteristicas_ambientales = None
        if ambientales := playa.get("caracteristicasAmbientales"):
            caracteristicas_ambientales = EnvironmentalCharacteristics.from_dict(
                ambientales
            )

        # Parse water test results
        ultimos_analisis = []
        if analisis := playa.get("tablaAnalisisTemporadaCurso"):
            ultimos_analisis = [WaterTestResult.from_dict(test) for test in analisis]

        return cls(
            id=playa.get("id", 0),
            nombre=playa.get("nombre", ""),
            descripcion=playa.get("descripcioPlatja", ""),
            municipio=playa.get("municipio", ""),
            costa=playa.get("costa", ""),
            coordenadas=coordenadas,
            fora_temporada=items.get("foraTemporada", False),
            imagenes=imagenes,
            calidad_playa=calidad_playa,
            medusas=medusas,
            condiciones=condiciones,
            caracteristicas_fisicas=caracteristicas_fisicas,
            caracteristicas_ambientales=caracteristicas_ambientales,
            ultimos_analisis=ultimos_analisis,
            playascercanas=playa.get("playascercanas", []),
        )
