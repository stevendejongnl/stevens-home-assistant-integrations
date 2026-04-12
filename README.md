# Steven's Home Assistant Integrations

Custom Home Assistant integrations for personal home automation projects.

## Integrations

### Dude, Where's My Package? (DWMP)

Track your packages from PostNL, DHL, DPD, and Amazon directly in Home Assistant.

**Sensor:** `sensor.dude_where_s_my_package_packages`
- State: number of active (non-delivered) packages
- Attributes:
  - `active` — active packages with full event timeline
  - `delivered` — delivered packages (metadata only)
  - `total_active` / `total_delivered` — counts

**Events:** Fires `dwmp_package_status_changed` on the HA event bus when a package status changes, with `tracking_number`, `carrier`, `label`, `old_status`, and `new_status` data. Use this to trigger automations (e.g. notify when delivered).

**Lovelace Card:** Bundled custom card with carrier badges, status colors, and expandable event timeline.

```yaml
type: custom:dwmp-tracking-card
entity: sensor.dude_where_s_my_package_packages
show_delivered: false  # optional: show delivered packages section
show_timeline: true    # optional: expandable event timeline per package
```

**Requires:** A running [Dude, Where's My Package?](https://github.com/stevendejongnl/dude-wheres-my-package) instance with password authentication enabled.

## Installation

1. Open HACS in your Home Assistant instance
2. Add this repository as a custom repository (type: Integration)
3. Install the integration
4. Restart Home Assistant
5. Go to Settings > Integrations > Add Integration > "Dude, Where's My Package?"
6. Enter your DWMP instance URL and password
7. Add the Lovelace card to your dashboard
