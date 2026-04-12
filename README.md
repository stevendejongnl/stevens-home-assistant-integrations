# Steven's Home Assistant Integrations

Custom Home Assistant integrations for personal home automation projects.

## Integrations

### Dude, Where's My Package? (DWMP)

Track your packages from PostNL, DHL, DPD, and Amazon directly in Home Assistant.

**Features:**
- Sensors for active packages, delivered today, and unread notifications
- Custom Lovelace card with package timeline visualization
- Automation events on package status changes (`dwmp_package_status_changed`)

**Setup:** Add this repository as a custom HACS integration, then configure via Settings > Integrations.

## Installation

1. Open HACS in your Home Assistant instance
2. Add this repository as a custom repository (type: Integration)
3. Install the integration
4. Restart Home Assistant
5. Go to Settings > Integrations > Add Integration > search for the integration name
