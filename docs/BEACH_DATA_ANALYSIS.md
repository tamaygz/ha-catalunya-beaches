# Beach Data Analysis - 10 Sample Beaches

## Summary of API Response Variations

### Beaches Analyzed:
1. **ID 0** - Platja Gran (Portbou) - Costa Brava North
2. **ID 1** - Platja d'en Goixa-els Morts (Colera) - Costa Brava North
3. **ID 3** - Platja de Grifeu (Llançà) - Costa Brava North
4. **ID 25** - **BEACH DOES NOT EXIST** (existe: "N")
5. **ID 50** - Platja Fonda (Begur) - Costa Brava
6. **ID 75** - Platja dels Canyerets (Sant Feliu de Guíxols) - Costa Brava
7. **ID 100** - Platja del Poblenou-la Riera (Pineda de Mar) - Maresme
8. **ID 150** - Platja del Fòrum (Sant Adrià de Besos) - Barcelona North
9. **ID 153** - Platja de la Nova Mar Bella (Barcelona) - Barcelona North
10. **ID 200** - Platja Llarga (Roda de Berà) - Costa Daurada

---

## Key Findings

### 1. **Non-Existent Beaches**
Beach ID 25 returned: `{"existe":"N"}` with minimal structure.

**Impact on Code:** ✅ Already handled - API client should check for this.

---

### 2. **Out of Season Status**
All beaches currently show `"foraTemporada": true` (November 11, 2025).

**Fields affected:**
- `calidadPlaya.estado_etiqueta`: `"_FORA_DE_TEMPORADA_"`
- `calidadPlaya.estado`: `"Out of season"`
- `medusas.peligrosidadEtiqueta`: `"_FORA_DE_TEMPORADA_"`

**Impact on Code:** ✅ Properly handled in binary_sensor `out_of_season`.

---

### 3. **Water Quality States Found**
From historical data analysis:
- `"Excellent"` - Most common
- `"Good"` - Found in beach 100, 150, 153
- `"Temporary disturbance (Rain)"` - Found in beach 100, 150
- `"Temporary disturbance"` - Found in beach 150
- `"Persistence of temporary disturbance"` - Found in beach 150

**Impact on Code:** ⚠️ Need to add these states to water quality mapping.

---

### 4. **Beach Characteristics Structure**

#### Physical Characteristics (`caracteristicasFisicas`):
```json
{
  "tipoplaya": "Beach",
  "tipoarena": "Coarse" | "Medium sand" | "Very coarse sand",
  "entorno": "Urban" | "Natural",
  "pendienteentradaagua": "Very strong" | "Medium" | "Gentle",
  "orientacion": "SSE" | "NE" | etc,
  "longitud": "265" (meters),
  "anchuramedia": "45" (meters),
  "paseomaritimo": "Yes" | "No",
  "caminoronda": "Yes" | "No",
  "socorrismo": "Yes" | "No"
}
```

#### Environmental Characteristics (`caracteristicasAmbientales`):
```json
{
  "riesgoalteracioncalidadporlluvias": "High" | "Low" | "Medium",
  "riesgoproliferacionfitoplacton": "Low" | "High",
  "temperaturamediaaguajunio": 20.1,
  "temperaturamediaaguajulio": 23.6,
  "temperaturamediaaguaagosto": 23.9,
  "temperaturamediaaguaseptiembre": 23.3
}
```

**Impact on Code:** ⚠️ These fields are NOT in our current data models but could be useful.

---

### 5. **Sky Condition Codes**
Found values: `"_20_"`, `"_21_"`, `"_3_"`

**Translation examples:**
- `"_3_"` → "Low to medium cloud cover"

**Impact on Code:** ⚠️ Need to verify sky condition mappings.

---

### 6. **UV Index Range**
Found values: `"1"` (Low)

**Impact on Code:** ✅ Already handled as string/int.

---

### 7. **Sea State Data** (`estadoMar`):
```json
{
  "alturaolas": 0.3,         // Wave height in meters
  "direccionolas": 337.6,    // Wave direction in degrees
  "velocidadviento": 1.2,    // Wind speed (km/h)
  "direccionviento": 220.2,  // Wind direction in degrees
  "uvminimo": "1",
  "uvmaximo": "1",
  "uv_max_literal": "Low",
  "uv_min_literal": "Low"
}
```

**Impact on Code:** ✅ Wave height and wind speed already extracted.

---

### 8. **Weather State** (`estadoPlaya`):
```json
{
  "temperatura": 19,                    // Air temperature
  "fecha": "11/11/2025",               // Date
  "hora": "10:00",                     // Time
  "etiquetaCielo": "_3_",              // Sky condition code
  "iconoCielo": "icono_2-47.png",
  "temperaturaAgua": 24.7,             // Water temperature
  "traduccionCielo": "Low to medium cloud cover"
}
```

**Impact on Code:** ✅ Already extracting temperatures and sky condition.

---

### 9. **Jellyfish Data** (`medusas`):
Currently all beaches show:
```json
{
  "peligrosidadEtiqueta": "_FORA_DE_TEMPORADA_",
  "peligrosidadTrad": "Out of season",
  "llistatMeduses": []
}
```

During season, expected values:
- `"_SENSE_PRESENCIA_"` → "None"
- `"_SENSE_PERILL_"` → "Low"
- `"_AMB_PERILL_"` → "Moderate/High"

**Impact on Code:** ⚠️ Need to verify jellyfish status mapping.

---

### 10. **Nearby Beaches** (`playascercanas`):
Some beaches have nearby beach suggestions with distance in km.

**Impact on Code:** ℹ️ Not currently used but could be a future feature.

---

## Required Code Updates

### 1. **Water Quality States** - CRITICAL
Add missing states to `const.py`:

```python
WATER_QUALITY_STATUS = {
    "Excellent": "excellent",
    "Good": "good",
    "Acceptable": "acceptable",
    "Temporary disturbance (Rain)": "acceptable",  # NEW
    "Temporary disturbance": "acceptable",         # NEW
    "Persistence of temporary disturbance": "poor", # NEW
    "Poor": "poor",
    "Very Poor": "very_poor",
}
```

### 2. **Sky Condition Codes** - VERIFY
Current mappings use codes like `"_20_"`, `"_21_"`, but response shows `"_3_"`.
Need to verify if our mapping covers all cases.

### 3. **Jellyfish Status Codes** - VERIFY
Ensure mapping includes:
- `"_FORA_DE_TEMPORADA_"` → "unknown"
- `"_SENSE_PRESENCIA_"` → "none"
- `"_SENSE_PERILL_"` → "low"
- `"_AMB_PERILL_"` → "high"

### 4. **Beach Characteristics** - OPTIONAL ENHANCEMENT
Consider adding these to BeachInfo dataclass:
- Physical characteristics (beach type, sand type, slope, services)
- Environmental characteristics (rain risk, avg temps)

---

## Recommendations

1. ✅ **API Error Handling:** Add check for `existe: "N"` in API client
2. ⚠️ **Water Quality:** Update state mappings to handle rain disturbances
3. ⚠️ **Code Verification:** Check sky/jellyfish mappings against real seasonal data
4. ℹ️ **Future Feature:** Beach characteristics could enhance entity attributes
5. ℹ️ **Future Feature:** Nearby beaches for recommendations

---

## Data Completeness

All 10 beaches (except ID 25) provide:
- ✅ Basic info (name, location, description)
- ✅ Current weather (air/water temp, sky, wind, waves, UV)
- ✅ Water quality status
- ✅ Jellyfish information
- ✅ Historical analysis data
- ✅ Physical/environmental characteristics
- ✅ Lifeguard presence (from `caracteristicasFisicas.socorrismo`)

**Conclusion:** API is comprehensive and consistent across beaches.
