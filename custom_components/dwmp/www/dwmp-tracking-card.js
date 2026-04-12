const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class DWMPTrackingCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _expanded: { type: Object },
    };
  }

  constructor() {
    super();
    this._expanded = {};
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity");
    }
    this.config = config;
  }

  getCardSize() {
    return 3;
  }

  static getStubConfig() {
    return { entity: "sensor.dwmp_active_packages" };
  }

  _toggleExpand(pkgId) {
    this._expanded = {
      ...this._expanded,
      [pkgId]: !this._expanded[pkgId],
    };
  }

  _getCarrierColor(carrier) {
    const colors = {
      postnl: { bg: "rgba(255, 107, 0, 0.13)", text: "#ff8a50" },
      dhl: { bg: "rgba(255, 204, 0, 0.13)", text: "#ffd93d" },
      dpd: { bg: "rgba(220, 20, 60, 0.13)", text: "#ff6b81" },
      amazon: { bg: "rgba(255, 153, 0, 0.13)", text: "#ffad42" },
    };
    return colors[carrier] || { bg: "rgba(99, 110, 114, 0.13)", text: "#8b8fa3" };
  }

  _getStatusStyle(status) {
    const styles = {
      delivered: { bg: "rgba(0, 184, 148, 0.13)", text: "#00b894" },
      in_transit: { bg: "rgba(116, 185, 255, 0.13)", text: "#74b9ff" },
      out_for_delivery: { bg: "rgba(253, 203, 110, 0.13)", text: "#fdcb6e" },
      pre_transit: { bg: "rgba(99, 110, 114, 0.13)", text: "#8b8fa3" },
      failed_attempt: { bg: "rgba(225, 112, 85, 0.13)", text: "#e17055" },
      returned: { bg: "rgba(214, 48, 49, 0.13)", text: "#d63031" },
      exception: { bg: "rgba(214, 48, 49, 0.13)", text: "#d63031" },
      unknown: { bg: "rgba(99, 110, 114, 0.13)", text: "#8b8fa3" },
    };
    return styles[status] || styles.unknown;
  }

  _formatStatus(status) {
    return (status || "unknown").replace(/_/g, " ");
  }

  _formatTime(timestamp) {
    if (!timestamp) return "";
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString("nl-NL", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return timestamp;
    }
  }

  _renderTimeline(events) {
    if (!events || events.length === 0) {
      return html`<div class="no-events">No tracking events yet</div>`;
    }
    const sorted = [...events].reverse();
    return html`
      <div class="timeline">
        ${sorted.map(
          (event, i) => html`
            <div class="timeline-event">
              <div class="timeline-dot ${i === 0 ? "active" : ""}"></div>
              <div class="timeline-content">
                <div class="timeline-desc">${event.description}</div>
                <div class="timeline-details">
                  <span class="timeline-time">${this._formatTime(event.timestamp)}</span>
                  ${event.location
                    ? html`<span class="timeline-loc">${event.location}</span>`
                    : ""}
                </div>
              </div>
            </div>
          `
        )}
      </div>
    `;
  }

  _renderPackage(pkg) {
    const carrier = this._getCarrierColor(pkg.carrier);
    const status = this._getStatusStyle(pkg.status);
    const isExpanded = this._expanded[pkg.id];

    return html`
      <div class="package">
        <div class="pkg-header" @click=${() => this._toggleExpand(pkg.id)}>
          <div class="pkg-main">
            <span
              class="pkg-carrier"
              style="background:${carrier.bg};color:${carrier.text}"
            >
              ${pkg.carrier}
            </span>
            <div class="pkg-info">
              <div class="pkg-tracking">${pkg.tracking_number}</div>
              <div class="pkg-details">
                ${pkg.label ? html`<span class="pkg-label">${pkg.label}</span>` : ""}
              </div>
            </div>
          </div>
          <div class="pkg-meta">
            <span
              class="status-badge"
              style="background:${status.bg};color:${status.text}"
            >
              ${this._formatStatus(pkg.status)}
            </span>
            <span class="pkg-date">${this._formatTime(pkg.updated_at)}</span>
          </div>
        </div>
        ${isExpanded && this.config.show_timeline !== false
          ? html`<div class="pkg-body">${this._renderTimeline(pkg.events)}</div>`
          : ""}
      </div>
    `;
  }

  render() {
    if (!this.hass || !this.config) return html``;

    const entity = this.hass.states[this.config.entity];
    if (!entity) {
      return html`
        <ha-card>
          <div class="card-content">
            <div class="no-events">Entity ${this.config.entity} not found</div>
          </div>
        </ha-card>
      `;
    }

    const packages = entity.attributes.packages || [];
    const activeCount = entity.state;

    return html`
      <ha-card>
        <div class="card-header">
          <div class="header-title">
            <ha-icon icon="mdi:package-variant"></ha-icon>
            <span>Packages</span>
          </div>
          <span class="header-badge">${activeCount}</span>
        </div>
        <div class="card-content">
          ${packages.length === 0
            ? html`<div class="no-events">No active packages</div>`
            : packages.map((pkg) => this._renderPackage(pkg))}
        </div>
      </ha-card>
    `;
  }

  static get styles() {
    return css`
      :host {
        --dwmp-accent: #6c5ce7;
        --dwmp-radius: 10px;
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
        color: var(--dwmp-accent);
        --mdc-icon-size: 24px;
      }

      .header-badge {
        background: var(--dwmp-accent);
        color: white;
        font-size: 0.75rem;
        font-weight: 700;
        min-width: 22px;
        height: 22px;
        line-height: 22px;
        border-radius: 11px;
        text-align: center;
        padding: 0 7px;
      }

      .card-content {
        padding: 12px 16px 16px;
      }

      .package {
        background: var(--card-background-color, var(--ha-card-background));
        border: 1px solid var(--divider-color);
        border-radius: var(--dwmp-radius);
        margin-bottom: 8px;
        overflow: hidden;
      }

      .package:last-child {
        margin-bottom: 0;
      }

      .pkg-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 14px;
        cursor: pointer;
        user-select: none;
      }

      .pkg-header:hover {
        background: var(--secondary-background-color);
      }

      .pkg-main {
        display: flex;
        align-items: center;
        gap: 10px;
        flex: 1;
        min-width: 0;
      }

      .pkg-carrier {
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 3px 6px;
        border-radius: 5px;
        white-space: nowrap;
        width: 54px;
        text-align: center;
        flex-shrink: 0;
      }

      .pkg-info {
        flex: 1;
        min-width: 0;
      }

      .pkg-tracking {
        font-family: "SF Mono", "Fira Code", "Cascadia Code", monospace;
        font-size: 0.8rem;
        color: var(--primary-text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .pkg-details {
        font-size: 0.75rem;
        color: var(--secondary-text-color);
        margin-top: 1px;
      }

      .pkg-label {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        display: block;
      }

      .pkg-meta {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 3px;
        flex-shrink: 0;
        margin-left: 8px;
      }

      .status-badge {
        font-size: 0.65rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 12px;
        white-space: nowrap;
        text-transform: capitalize;
      }

      .pkg-date {
        font-size: 0.65rem;
        color: var(--secondary-text-color);
        white-space: nowrap;
      }

      /* Timeline */
      .pkg-body {
        padding: 0 14px 12px;
        border-top: 1px solid var(--divider-color);
      }

      .timeline {
        padding: 10px 0 2px;
      }

      .timeline-event {
        display: flex;
        gap: 12px;
        padding: 7px 0;
        position: relative;
      }

      .timeline-event::before {
        content: "";
        position: absolute;
        left: 5px;
        top: 24px;
        bottom: -7px;
        width: 2px;
        background: var(--divider-color);
      }

      .timeline-event:last-child::before {
        display: none;
      }

      .timeline-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-top: 3px;
        flex-shrink: 0;
        border: 2px solid var(--divider-color);
        background: var(--card-background-color, var(--ha-card-background));
      }

      .timeline-dot.active {
        border-color: var(--dwmp-accent);
        background: var(--dwmp-accent);
        box-shadow: 0 0 6px rgba(108, 92, 231, 0.4);
      }

      .timeline-content {
        flex: 1;
      }

      .timeline-desc {
        font-size: 0.8rem;
        color: var(--primary-text-color);
      }

      .timeline-details {
        display: flex;
        gap: 10px;
        margin-top: 1px;
      }

      .timeline-time,
      .timeline-loc {
        font-size: 0.7rem;
        color: var(--secondary-text-color);
      }

      .no-events {
        text-align: center;
        padding: 20px;
        color: var(--secondary-text-color);
        font-size: 0.85rem;
      }
    `;
  }
}

customElements.define("dwmp-tracking-card", DWMPTrackingCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "dwmp-tracking-card",
  name: "DWMP Package Tracking",
  description: "Track your packages from PostNL, DHL, DPD, and Amazon",
  preview: true,
});
