const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class TemperatureComparisonCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity (corrected difference sensor)");
    }
    this.config = {
      show_sparklines: true,
      show_last_year: true,
      ...config,
    };
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return { entity: "sensor.temperature_comparison_corrected_difference" };
  }

  _getEntity(suffix) {
    const base = this.config.entity.replace("_corrected_difference", "");
    return this.hass.states[`${base}_${suffix}`];
  }

  _val(entity) {
    if (!entity || entity.state === "unknown" || entity.state === "unavailable") {
      return null;
    }
    const v = parseFloat(entity.state);
    return isNaN(v) ? null : v;
  }

  _fmt(val) {
    if (val === null || val === undefined) return "n/a";
    return `${val.toFixed(1)}°C`;
  }

  _delta(current, lastYear) {
    if (current === null || lastYear === null) return null;
    return current - lastYear;
  }

  _trendIcon(trend) {
    if (trend === "cooler") return "mdi:trending-down";
    if (trend === "warmer") return "mdi:trending-up";
    return "mdi:trending-neutral";
  }

  _trendColor(trend) {
    if (trend === "cooler") return "var(--tc-cooler, #00b894)";
    if (trend === "warmer") return "var(--tc-warmer, #e17055)";
    return "var(--tc-neutral, var(--secondary-text-color))";
  }

  _renderSparkline(dailyValues, color) {
    if (!dailyValues || dailyValues.length < 2) {
      return html`<div class="sparkline-empty">No data</div>`;
    }

    const means = dailyValues
      .map((d) => d.mean)
      .filter((v) => v !== null && v !== undefined);
    if (means.length < 2) {
      return html`<div class="sparkline-empty">No data</div>`;
    }

    const min = Math.min(...means);
    const max = Math.max(...means);
    const range = max - min || 1;
    const w = 120;
    const h = 32;
    const pad = 2;

    const points = means
      .map((v, i) => {
        const x = pad + (i / (means.length - 1)) * (w - 2 * pad);
        const y = pad + (1 - (v - min) / range) * (h - 2 * pad);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");

    const lastVal = means[means.length - 1];

    return html`
      <div class="sparkline-container">
        <svg viewBox="0 0 ${w} ${h}" class="sparkline-svg">
          <polyline
            points="${points}"
            fill="none"
            stroke="${color}"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <circle
            cx="${pad + ((means.length - 1) / (means.length - 1)) * (w - 2 * pad)}"
            cy="${pad + (1 - (lastVal - min) / range) * (h - 2 * pad)}"
            r="2"
            fill="${color}"
          />
        </svg>
        <span class="sparkline-range">${min.toFixed(1)}–${max.toFixed(1)}°</span>
      </div>
    `;
  }

  _renderDeltaBadge(delta) {
    if (delta === null) return "";
    const sign = delta >= 0 ? "+" : "";
    const cls = delta > 0.3 ? "badge-warm" : delta < -0.3 ? "badge-cool" : "badge-neutral";
    return html`<span class="delta-badge ${cls}">${sign}${delta.toFixed(1)}°</span>`;
  }

  render() {
    if (!this.hass || !this.config) return html``;

    const mainEntity = this.hass.states[this.config.entity];
    if (!mainEntity) {
      return html`
        <ha-card>
          <div class="card-content empty">
            Entity ${this.config.entity} not found
          </div>
        </ha-card>
      `;
    }

    const insideAvg = this._getEntity("inside_average");
    const outsideAvg = this._getEntity("outside_average");
    const insideLY = this._getEntity("inside_last_year");
    const outsideLY = this._getEntity("outside_last_year");

    const insideVal = this._val(insideAvg);
    const outsideVal = this._val(outsideAvg);
    const insideLYVal = this._val(insideLY);
    const outsideLYVal = this._val(outsideLY);
    const corrected = this._val(mainEntity);

    const trend = mainEntity.attributes.trend || "unknown";
    const trendColor = this._trendColor(trend);
    const days = insideAvg?.attributes?.period_days || 7;

    const insideCurrent = insideAvg?.attributes?.current_temperature;
    const outsideCurrent = outsideAvg?.attributes?.current_temperature;

    const insideDaily = insideAvg?.attributes?.daily_values || [];
    const outsideDaily = outsideAvg?.attributes?.daily_values || [];

    return html`
      <ha-card>
        <div class="card-header">
          <div class="header-title">
            <ha-icon icon="mdi:thermometer-check"></ha-icon>
            <span>${this.config.title || "Temperature Comparison"}</span>
          </div>
          <div class="header-trend" style="color: ${trendColor}">
            <ha-icon icon="${this._trendIcon(trend)}" style="color: ${trendColor}; --mdc-icon-size: 20px;"></ha-icon>
          </div>
        </div>

        <div class="card-content">
          <!-- Current readings -->
          <div class="readings">
            <div class="reading-col">
              <div class="reading-label">
                <ha-icon icon="mdi:home-thermometer" class="label-icon"></ha-icon>
                Inside
              </div>
              <div class="reading-current">${this._fmt(insideCurrent)}</div>
              <div class="reading-avg">${days}d avg: ${this._fmt(insideVal)}</div>
              ${this.config.show_sparklines
                ? this._renderSparkline(insideDaily, "var(--tc-inside, #74b9ff)")
                : ""}
            </div>
            <div class="reading-divider"></div>
            <div class="reading-col">
              <div class="reading-label">
                <ha-icon icon="mdi:thermometer" class="label-icon"></ha-icon>
                Outside
              </div>
              <div class="reading-current">${this._fmt(outsideCurrent)}</div>
              <div class="reading-avg">${days}d avg: ${this._fmt(outsideVal)}</div>
              ${this.config.show_sparklines
                ? this._renderSparkline(outsideDaily, "var(--tc-outside, #a29bfe)")
                : ""}
            </div>
          </div>

          <!-- Last year comparison -->
          ${this.config.show_last_year
            ? html`
                <div class="last-year-section">
                  <div class="section-label">Same period last year</div>
                  <div class="last-year-row">
                    <div class="ly-item">
                      <span class="ly-label">Inside</span>
                      <span class="ly-value">${this._fmt(insideLYVal)}</span>
                      ${this._renderDeltaBadge(this._delta(insideVal, insideLYVal))}
                    </div>
                    <div class="ly-item">
                      <span class="ly-label">Outside</span>
                      <span class="ly-value">${this._fmt(outsideLYVal)}</span>
                      ${this._renderDeltaBadge(this._delta(outsideVal, outsideLYVal))}
                    </div>
                  </div>
                </div>
              `
            : ""}

          <!-- Corrected difference -->
          <div class="difference-section" style="border-color: ${trendColor}">
            <div class="diff-label">Corrected difference</div>
            <div class="diff-value" style="color: ${trendColor}">
              ${corrected !== null
                ? html`${corrected > 0 ? "+" : ""}${corrected.toFixed(2)}°C`
                : "insufficient data"}
            </div>
            <div class="diff-trend" style="color: ${trendColor}">
              ${trend === "cooler"
                ? "Cooler than last year"
                : trend === "warmer"
                  ? "Warmer than last year"
                  : trend === "similar"
                    ? "Similar to last year"
                    : ""}
            </div>
          </div>
        </div>
      </ha-card>
    `;
  }

  static get styles() {
    return css`
      :host {
        --tc-cooler: #00b894;
        --tc-warmer: #e17055;
        --tc-neutral: var(--secondary-text-color);
        --tc-inside: #74b9ff;
        --tc-outside: #a29bfe;
        --tc-radius: 10px;
      }

      ha-card {
        overflow: hidden;
      }

      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 16px 0;
      }

      .header-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--primary-text-color);
      }

      .header-title ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 24px;
      }

      .card-content {
        padding: 12px 16px 16px;
      }

      .empty {
        text-align: center;
        padding: 20px;
        color: var(--secondary-text-color);
      }

      /* Readings grid */
      .readings {
        display: flex;
        gap: 0;
        margin-bottom: 12px;
      }

      .reading-col {
        flex: 1;
        text-align: center;
      }

      .reading-divider {
        width: 1px;
        background: var(--divider-color);
        margin: 0 12px;
      }

      .reading-label {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--secondary-text-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
      }

      .label-icon {
        --mdc-icon-size: 16px;
      }

      .reading-current {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-text-color);
        line-height: 1.2;
      }

      .reading-avg {
        font-size: 0.75rem;
        color: var(--secondary-text-color);
        margin-top: 2px;
      }

      /* Sparklines */
      .sparkline-container {
        margin-top: 6px;
        display: flex;
        flex-direction: column;
        align-items: center;
      }

      .sparkline-svg {
        width: 100%;
        max-width: 120px;
        height: 32px;
      }

      .sparkline-range {
        font-size: 0.6rem;
        color: var(--secondary-text-color);
        margin-top: 1px;
      }

      .sparkline-empty {
        font-size: 0.65rem;
        color: var(--secondary-text-color);
        margin-top: 8px;
      }

      /* Last year section */
      .last-year-section {
        border-top: 1px solid var(--divider-color);
        padding-top: 10px;
        margin-bottom: 12px;
      }

      .section-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--secondary-text-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
      }

      .last-year-row {
        display: flex;
        gap: 16px;
      }

      .ly-item {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
      }

      .ly-label {
        color: var(--secondary-text-color);
      }

      .ly-value {
        font-weight: 600;
        color: var(--primary-text-color);
      }

      .delta-badge {
        font-size: 0.65rem;
        font-weight: 600;
        padding: 1px 5px;
        border-radius: 8px;
      }

      .badge-warm {
        background: rgba(225, 112, 85, 0.13);
        color: var(--tc-warmer);
      }

      .badge-cool {
        background: rgba(0, 184, 148, 0.13);
        color: var(--tc-cooler);
      }

      .badge-neutral {
        background: rgba(99, 110, 114, 0.13);
        color: var(--secondary-text-color);
      }

      /* Corrected difference */
      .difference-section {
        border-top: 2px solid var(--divider-color);
        padding-top: 10px;
        text-align: center;
      }

      .diff-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--secondary-text-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
      }

      .diff-value {
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.2;
      }

      .diff-trend {
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 2px;
      }
    `;
  }
}

customElements.define("temperature-comparison-card", TemperatureComparisonCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "temperature-comparison-card",
  name: "Temperature Comparison",
  description: "Compare indoor/outdoor temperatures year-over-year with weather correction",
  preview: true,
});
