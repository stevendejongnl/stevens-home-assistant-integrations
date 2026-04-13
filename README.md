# Steven's Home Assistant Integrations

Custom Home Assistant integrations for personal home automation projects.

## Integrations

### Dude, Where's My Package? (DWMP)

Track your packages from PostNL, DHL, DPD, GLS, and Amazon directly in Home Assistant.

**Requires:** A running [Dude, Where's My Package?](https://github.com/stevendejongnl/dude-wheres-my-package) instance with password authentication enabled.

#### Sensor

`sensor.dwmp_packages` — state is the number of active (non-delivered) packages.

| Attribute | Description |
|-----------|-------------|
| `active` | Active packages with full event timeline |
| `delivered` | Delivered packages (metadata only) |
| `total_active` | Count of active packages |
| `total_delivered` | Count of delivered packages |

#### Lovelace Card

Bundled custom card with carrier badges (PostNL, DHL, DPD, GLS, Amazon), status colors, and expandable event timeline. Automatically registered as a Lovelace resource on setup.

```yaml
type: custom:dwmp-tracking-card
entity: sensor.dwmp_packages
show_delivered: false  # optional: show delivered packages section
show_timeline: true    # optional: expandable event timeline per package
```

#### Events

Fires `dwmp_package_status_changed` on the HA event bus when a package status changes.

| Field | Description |
|-------|-------------|
| `tracking_number` | Package tracking number |
| `carrier` | Carrier name (postnl, dhl, dpd, amazon) |
| `label` | Package label (if set) |
| `old_status` | Previous status |
| `new_status` | New status |

#### Automation Example

Send a notification when any package status changes:

```yaml
- id: dwmp_package_status_notification
  alias: "DWMP: Package status update"
  triggers:
  - trigger: event
    event_type: dwmp_package_status_changed
  actions:
  - action: notify.steven
    data:
      title: "📦 Package Update"
      message: >-
        {{ trigger.event.data.carrier | upper }}:
        {{ trigger.event.data.tracking_number }}
        → {{ trigger.event.data.new_status | replace("_", " ") }}
        {% if trigger.event.data.label %}({{ trigger.event.data.label }}){% endif %}
  mode: queued
  max: 10
```

### Temperature Comparison

Compare indoor and outdoor temperatures year-over-year with weather correction. Uses Home Assistant's long-term statistics to compute rolling averages and compare them to the same period last year.

#### Sensors

| Sensor | Description |
|--------|-------------|
| `*_inside_average` | Rolling N-day average inside temperature |
| `*_outside_average` | Rolling N-day average outside temperature |
| `*_inside_last_year` | Inside average from the same period last year |
| `*_outside_last_year` | Outside average from the same period last year |
| `*_corrected_difference` | Year-over-year corrected difference |

**Formula:** `(inside_last_year - inside_now) + (outside_now - outside_last_year) * weight`

The outdoor correction accounts for weather differences — if this year is colder outside, the raw inside difference is adjusted so you can see if your home is actually performing better or worse than last year.

#### Lovelace Card

Bundled custom card with sparklines, trend indicators, and delta badges.

```yaml
type: custom:temperature-comparison-card
entity: sensor.temperature_comparison_corrected_difference
show_sparklines: true    # optional: 14-day sparkline graphs
show_last_year: true     # optional: last year comparison row
```

#### Options

After setup, configure via Settings > Integrations > Temperature Comparison > Configure:

| Option | Default | Description |
|--------|---------|-------------|
| Rolling average period | 7 days | Number of days for the average (1–30) |
| Outdoor correction weight | 0.5 | How much outdoor changes affect the result (0–2) |
| Update interval | 1800s | How often to recompute statistics (300–7200s) |

## Installation

1. Open HACS in your Home Assistant instance
2. Add this repository as a custom repository (type: Integration)
3. Install the integration
4. Restart Home Assistant
5. Go to Settings > Integrations > Add Integration
6. Search for "Dude, Where's My Package?" or "Temperature Comparison"
7. Follow the setup wizard
8. Lovelace cards are registered automatically — add them to your dashboard
