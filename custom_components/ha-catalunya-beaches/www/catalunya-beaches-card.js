/**
 * Catalunya Beaches Card
 * Custom Lovelace card for the Catalunya Beaches Home Assistant integration.
 * https://github.com/tamaygz/ha-catalunya-beaches
 */

(function () {
  "use strict";

  const CARD_VERSION = "1.0.0";
  const CARD_TYPE = "catalunya-beaches-card";

  // Known entity key suffixes for each platform — longest first for correct prefix extraction.
  const SENSOR_SUFFIXES = [
    "water_temperature",
    "air_temperature",
    "water_quality",
    "jellyfish_status",
    "sky_condition",
    "last_test_date",
    "beach_info",
    "beach_name",
    "uv_index",
    "wave_height",
    "wind_speed",
    "description",
  ];

  const BINARY_SENSOR_SUFFIXES = [
    "lifeguard_present",
    "water_quality_good",
    "jellyfish_alert",
    "rain_risk_high",
    "out_of_season",
  ];

  const ALL_SUFFIXES = [...SENSOR_SUFFIXES, ...BINARY_SENSOR_SUFFIXES].sort(
    (a, b) => b.length - a.length
  );

  /**
   * Extract the HA device slug from any entity_id belonging to this integration.
   * Entity IDs look like: sensor.<slug>_<suffix> or binary_sensor.<slug>_<suffix>
   */
  function slugFromEntityId(entityId) {
    const plain = entityId.replace(/^(?:sensor|binary_sensor)\./, "");
    for (const suffix of ALL_SUFFIXES) {
      const tail = "_" + suffix;
      if (plain.endsWith(tail)) {
        return plain.slice(0, -tail.length);
      }
    }
    return null;
  }

  /** Water quality state → CSS color */
  function qualityColor(state) {
    if (!state) return "var(--secondary-text-color, #888)";
    switch (state.toLowerCase()) {
      case "excellent":
      case "good":
        return "var(--success-color, #2e7d32)";
      case "acceptable":
        return "#cc6600";
      case "poor":
      case "very_poor":
        return "var(--error-color, #c62828)";
      case "out_of_season":
        return "var(--disabled-color, #666)";
      default:
        return "var(--secondary-text-color, #888)";
    }
  }

  /** UV index → accent color */
  function uvColor(raw) {
    const v = parseFloat(raw);
    if (isNaN(v)) return "inherit";
    if (v >= 8) return "var(--error-color, #c62828)";
    if (v >= 6) return "#cc6600";
    if (v >= 3) return "#e6a817";
    return "inherit";
  }

  const QUALITY_LABELS = {
    excellent: "Excellent",
    good: "Good",
    acceptable: "Acceptable",
    poor: "Poor",
    very_poor: "Very Poor",
    out_of_season: "Out of Season",
    unknown: "Unknown",
  };

  const JELLYFISH_LABELS = {
    none: "None",
    low: "Low",
    moderate: "Moderate",
    high: "High",
    very_high: "Very High",
    out_of_season: "Out of Season",
    unknown: "Unknown",
  };

  function label(map, state) {
    if (!state) return "—";
    return map[state.toLowerCase()] ?? state;
  }

  // ─────────────────────────────────────────────────────────────────────────────

  class CatalunyaBeachesCard extends HTMLElement {
    // ── Lifecycle ───────────────────────────────────────────────────────────

    setConfig(config) {
      if (!config.entity) {
        throw new Error("'entity' is required.");
      }
      const slug = slugFromEntityId(config.entity);
      if (!slug) {
        throw new Error(
          `Cannot determine beach from entity "${config.entity}". ` +
            "Select any sensor or binary_sensor from a Catalunya Beaches device."
        );
      }
      this._slug = slug;
      this._config = {
        show_image: true,
        show_conditions: true,
        show_safety: true,
        show_details: false,
        compact: false,
        ...config,
      };
      if (this._hass) this._render();
    }

    set hass(hass) {
      this._hass = hass;
      if (this._config) this._render();
    }

    connectedCallback() {
      if (this._hass && this._config) this._render();
    }

    // ── Card meta ────────────────────────────────────────────────────────────

    static getStubConfig() {
      return {
        entity: "sensor.my_beach_beach_name",
        show_image: true,
        show_conditions: true,
        show_safety: true,
        show_details: false,
        compact: false,
      };
    }

    static getConfigForm() {
      return {
        schema: [
          {
            name: "entity",
            required: true,
            selector: { entity: { domain: ["sensor", "binary_sensor"] } },
          },
          {
            type: "expandable",
            title: "Display options",
            schema: [
              {
                type: "grid",
                name: "",
                schema: [
                  { name: "show_image", selector: { boolean: {} } },
                  { name: "show_conditions", selector: { boolean: {} } },
                  { name: "show_safety", selector: { boolean: {} } },
                  { name: "show_details", selector: { boolean: {} } },
                  { name: "compact", selector: { boolean: {} } },
                ],
              },
            ],
          },
        ],
        computeLabel(schema) {
          const map = {
            entity: "Beach entity",
            show_image: "Show beach image",
            show_conditions: "Show conditions",
            show_safety: "Show safety indicators",
            show_details: "Show quality details",
            compact: "Compact layout",
          };
          return map[schema.name] ?? schema.name;
        },
        computeHelper(schema) {
          if (schema.name === "entity") {
            return "Pick any sensor or binary_sensor belonging to the Catalunya Beaches device.";
          }
          return undefined;
        },
      };
    }

    getCardSize() {
      return this._config?.compact ? 3 : 6;
    }

    getGridOptions() {
      return {
        columns: 12,
        rows: this._config?.compact ? 3 : 6,
        min_columns: 6,
        min_rows: 3,
      };
    }

    // ── Entity helpers ───────────────────────────────────────────────────────

    _sid(suffix) {
      return `sensor.${this._slug}_${suffix}`;
    }

    _bid(suffix) {
      return `binary_sensor.${this._slug}_${suffix}`;
    }

    _state(id) {
      return this._hass?.states?.[id]?.state ?? null;
    }

    _attr(id, key) {
      return this._hass?.states?.[id]?.attributes?.[key] ?? null;
    }

    _fmt(val, unit = "") {
      if (val == null || val === "unavailable" || val === "unknown") return "—";
      return unit ? `${val}\u202f${unit}` : String(val);
    }

    // ── Rendering ────────────────────────────────────────────────────────────

    _render() {
      const cfg = this._config;
      const compact = cfg.compact;

      // Entity IDs
      const nameId = this._sid("beach_name");
      const qualityId = this._sid("water_quality");
      const jellyfishId = this._sid("jellyfish_status");
      const waterTempId = this._sid("water_temperature");
      const airTempId = this._sid("air_temperature");
      const uvId = this._sid("uv_index");
      const waveId = this._sid("wave_height");
      const windId = this._sid("wind_speed");
      const skyId = this._sid("sky_condition");
      const lifeguardId = this._bid("lifeguard_present");
      const wqGoodId = this._bid("water_quality_good");
      const jellyfishAlertId = this._bid("jellyfish_alert");
      const rainRiskId = this._bid("rain_risk_high");
      const offSeasonId = this._bid("out_of_season");

      // Values
      const beachDisplay =
        this._attr(nameId, "friendly_name") ??
        this._slug.replace(/_/g, " ");

      const imageUrl =
        this._attr(nameId, "entity_picture") ??
        this._attr(nameId, "primary_image") ??
        null;

      const qualityRaw = this._state(qualityId);
      const qualityDisplay = label(QUALITY_LABELS, qualityRaw);
      const qColor = qualityColor(qualityRaw);
      const qualityInfo = this._attr(qualityId, "estado_info") ?? "";
      const qualityUpdated = this._attr(qualityId, "last_update") ?? "";

      const waterTemp = this._fmt(this._state(waterTempId), "°C");
      const airTemp = this._fmt(this._state(airTempId), "°C");
      const uvRaw = this._state(uvId);
      const uv = this._fmt(uvRaw);
      const uvCss = uvColor(uvRaw);
      const waves = this._fmt(this._state(waveId), "m");
      const wind = this._fmt(this._state(windId), "km/h");
      const sky = this._fmt(this._state(skyId));

      const lifeguard = this._state(lifeguardId);
      const wqGood = this._state(wqGoodId);
      const jellyfishAlert = this._state(jellyfishAlertId);
      const rainRisk = this._state(rainRiskId);
      const offSeason = this._state(offSeasonId);
      const jellyfishRaw = this._state(jellyfishId);
      const jellyfishDisplay = label(JELLYFISH_LABELS, jellyfishRaw);
      const jellyfishSpecies =
        (this._attr(jellyfishId, "species") ?? []).join(", ") || null;

      // Ensure outer ha-card exists once
      if (!this._card) {
        this.innerHTML = "";
        this._card = document.createElement("ha-card");
        this.appendChild(this._card);
        this._injectStyles();
      }

      const imgH = compact ? "80px" : "160px";

      this._card.innerHTML = `
        ${
          cfg.show_image && imageUrl
            ? `<div class="cb-hero" style="height:${imgH};background-image:url('${imageUrl}')">
                 <div class="cb-hero-name">${beachDisplay}</div>
               </div>`
            : `<div class="cb-title">${beachDisplay}</div>`
        }

        <div class="cb-quality" style="border-color:${qColor};background:${qColor}1a">
          <span class="cb-quality-label">Water Quality</span>
          <span class="cb-quality-value" style="color:${qColor}">${qualityDisplay}</span>
          ${!compact && qualityInfo ? `<span class="cb-quality-info">${qualityInfo}</span>` : ""}
        </div>

        ${
          cfg.show_conditions
            ? `<div class="cb-section">
                 ${!compact ? '<div class="cb-section-title">Conditions</div>' : ""}
                 <div class="cb-grid">
                   ${this._condCell("🌡️", "Water", waterTemp)}
                   ${this._condCell("🌤️", "Air", airTemp)}
                   ${this._condCell("☀️", "UV", `<span style="color:${uvCss}">${uv}</span>`)}
                   ${this._condCell("🌊", "Waves", waves)}
                   ${this._condCell("💨", "Wind", wind)}
                   ${this._condCell("🌥️", "Sky", sky)}
                 </div>
               </div>`
            : ""
        }

        ${
          cfg.show_safety
            ? `<div class="cb-section">
                 ${!compact ? '<div class="cb-section-title">Safety</div>' : ""}
                 <div class="cb-safety">
                   ${this._safetyRow("👮", "Lifeguard", lifeguard, false)}
                   ${this._safetyRow("✅", "Water OK", wqGood, false)}
                   ${this._jellyfishRow(jellyfishDisplay, jellyfishAlert)}
                   ${this._safetyRow("🌧️", "Rain risk high", rainRisk, true)}
                   ${!compact ? this._safetyRow("📅", "Off season", offSeason, true) : ""}
                 </div>
               </div>`
            : ""
        }

        ${
          cfg.show_details &&
          (qualityInfo || jellyfishSpecies || qualityUpdated)
            ? `<div class="cb-section cb-details">
                 ${!compact ? '<div class="cb-section-title">Details</div>' : ""}
                 ${qualityInfo ? `<div class="cb-detail-row"><span>Quality info</span><span>${qualityInfo}</span></div>` : ""}
                 ${jellyfishSpecies ? `<div class="cb-detail-row"><span>Jellyfish species</span><span>${jellyfishSpecies}</span></div>` : ""}
                 ${qualityUpdated ? `<div class="cb-detail-row"><span>Quality updated</span><span>${qualityUpdated}</span></div>` : ""}
               </div>`
            : ""
        }
      `;
    }

    _condCell(icon, lbl, value) {
      return `<div class="cb-cond">
        <span class="cb-cond-icon">${icon}</span>
        <span class="cb-cond-label">${lbl}</span>
        <span class="cb-cond-value">${value}</span>
      </div>`;
    }

    /**
     * @param {boolean} alertWhenOn  true = on is bad (rain risk, off season), false = on is good (lifeguard, water ok)
     */
    _safetyRow(icon, lbl, state, alertWhenOn) {
      let color = "var(--secondary-text-color, #888)";
      let display = state ?? "—";

      if (state === "on") {
        color = alertWhenOn
          ? "var(--error-color, #c62828)"
          : "var(--success-color, #2e7d32)";
        display = alertWhenOn ? "⚠\ufe0f Yes" : "✔ Yes";
      } else if (state === "off") {
        color = alertWhenOn
          ? "var(--success-color, #2e7d32)"
          : "var(--secondary-text-color, #888)";
        display = alertWhenOn ? "✔ No" : "✘ No";
      } else if (state === "unavailable" || state === "unknown") {
        display = "—";
      }

      return `<div class="cb-safety-row">
        <span>${icon} ${lbl}</span>
        <span class="cb-safety-val" style="color:${color}">${display}</span>
      </div>`;
    }

    _jellyfishRow(jellyfishDisplay, alertState) {
      let color = "var(--secondary-text-color, #888)";
      if (alertState === "on") color = "var(--error-color, #c62828)";
      else if (alertState === "off") color = "var(--success-color, #2e7d32)";

      return `<div class="cb-safety-row">
        <span>🪼 Jellyfish</span>
        <span class="cb-safety-val" style="color:${color}">${jellyfishDisplay}</span>
      </div>`;
    }

    _injectStyles() {
      const s = document.createElement("style");
      s.textContent = `
        :host { display: block; }
        ha-card { overflow: hidden; padding-bottom: 6px; }

        /* Hero image */
        .cb-hero {
          width: 100%;
          background-size: cover;
          background-position: center;
          display: flex;
          align-items: flex-end;
        }
        .cb-hero-name {
          width: 100%;
          padding: 6px 14px 8px;
          background: linear-gradient(transparent, rgba(0,0,0,.65));
          color: #fff;
          font-size: 1rem;
          font-weight: 500;
          letter-spacing: .02em;
        }

        /* Title (no-image fallback) */
        .cb-title {
          padding: 14px 14px 4px;
          font-size: 1rem;
          font-weight: 500;
          color: var(--primary-text-color);
        }

        /* Quality badge */
        .cb-quality {
          margin: 8px 10px 2px;
          padding: 8px 12px;
          border-radius: 8px;
          border-left: 4px solid;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .cb-quality-label {
          font-size: .68rem;
          text-transform: uppercase;
          letter-spacing: .06em;
          opacity: .65;
        }
        .cb-quality-value {
          font-size: 1rem;
          font-weight: 600;
        }
        .cb-quality-info {
          font-size: .78rem;
          opacity: .8;
          margin-top: 1px;
        }

        /* Generic section wrapper */
        .cb-section {
          padding: 4px 10px 4px;
        }
        .cb-section-title {
          font-size: .67rem;
          text-transform: uppercase;
          letter-spacing: .06em;
          opacity: .5;
          padding: 4px 0 3px;
        }

        /* Conditions grid */
        .cb-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 4px;
        }
        .cb-cond {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 6px 4px;
          background: var(--secondary-background-color);
          border-radius: 6px;
        }
        .cb-cond-icon  { font-size: 1.1rem; }
        .cb-cond-label { font-size: .6rem; opacity: .6; margin-top: 2px; }
        .cb-cond-value { font-size: .85rem; font-weight: 500; margin-top: 1px; }

        /* Safety rows */
        .cb-safety { display: flex; flex-direction: column; }
        .cb-safety-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 5px 2px;
          font-size: .88rem;
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.07));
        }
        .cb-safety-row:last-child { border-bottom: none; }
        .cb-safety-val { font-weight: 500; }

        /* Details section */
        .cb-details {
          border-top: 1px solid var(--divider-color, rgba(0,0,0,.07));
          margin-top: 2px;
        }
        .cb-detail-row {
          display: flex;
          justify-content: space-between;
          gap: 8px;
          font-size: .8rem;
          padding: 3px 2px;
          opacity: .85;
        }
        .cb-detail-row span:last-child {
          text-align: right;
          max-width: 58%;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      `;
      this._card.appendChild(s);
    }
  }

  // ── Register ────────────────────────────────────────────────────────────────

  if (!customElements.get(CARD_TYPE)) {
    customElements.define(CARD_TYPE, CatalunyaBeachesCard);
    console.info(
      `%c CATALUNYA-BEACHES-CARD %c v${CARD_VERSION} `,
      "background:#2e7d32;color:#fff;font-weight:700;padding:2px 6px;border-radius:4px 0 0 4px",
      "background:#1b5e20;color:#fff;padding:2px 6px;border-radius:0 4px 4px 0"
    );
  }

  window.customCards = window.customCards || [];
  if (!window.customCards.some((c) => c.type === CARD_TYPE)) {
    window.customCards.push({
      type: CARD_TYPE,
      name: "Catalunya Beach Card",
      description:
        "Displays beach conditions, safety indicators, and water quality from the Catalunya Beaches integration.",
      preview: true,
      documentationURL: "https://github.com/tamaygz/ha-catalunya-beaches",
    });
  }
})();
