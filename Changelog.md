# Changelog

All notable changes to this fork will be documented in this file.

## [Unreleased]

### 🔄 From Original Repository
This fork is based on [maciej-or/hikvision_next](https://github.com/maciej-or/hikvision_next) (last updated ~2023)

---

## [1.0.0] - 2026-01-30

### 🎉 Initial Fork Release

### ✨ Added
- **Instant binary sensor state updates** using Hikvision's event stream
  - Binary sensors now respond in <1 second instead of up to 120 seconds
  - Sensors properly turn OFF when events end (previously stayed ON indefinitely)

### 🔧 Changed
- **models.py**: Added `event_state` field to `AlertInfo` dataclass
- **isapi.py**: Modified `parse_event_notification()` to extract `eventState` from alert XML
- **notifications.py**: Updated `trigger_sensor()` to set sensor state based on `event_state` value
  - `eventState="active"` → Sensor turns ON
  - `eventState="inactive"` → Sensor turns OFF

### 🐛 Fixed
- Motion detection sensors now respond instantly to state changes
- Binary sensors properly reset to OFF state when motion ends
- Eliminated 2-minute polling delay for event detection

### 📝 Technical Details
The original integration was receiving instant event notifications from Hikvision devices but ignoring the `<eventState>active/inactive</eventState>` field in the XML payload. Instead, it relied on polling the device every 120 seconds to check event state, causing significant delays.

This fix properly parses and utilizes the real-time event state information that was already being sent by the devices.

### ✅ Tested On
- DS-7216HQHI-K1 NVR
- [Add your firmware version]
- Home Assistant 2024.x

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to help improve this fork.

## Original Repository

For the original version (unmaintained), see: https://github.com/maciej-or/hikvision_next
