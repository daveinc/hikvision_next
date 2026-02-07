# Development Log - Hikvision Next Enhanced Features

**Branch:** dev  
**Started:** 2026-02-02  
**Goal:** Add comprehensive ISAPI status monitoring and device controls

---

## Feature Checklist

### Phase 1: Device Control Buttons
- [ ] Create `button.py` platform
- [ ] Add Reboot button entity
- [ ] Add Shutdown button entity
- [ ] Add `reboot()` method to ISAPI client
- [ ] Add `shutdown()` method to ISAPI client
- [ ] Update `__init__.py` to load button platform
- [ ] Test on actual NVR
- [ ] Document in README

**ISAPI Endpoints:**
- `PUT /ISAPI/System/reboot`
- `PUT /ISAPI/System/shutdown?format=json`

---

### Phase 2: System Status Sensors (CPU/Memory)
- [ ] Add `get_system_status()` to ISAPI client
- [ ] Add `get_system_status()` to hikvision_device
- [ ] Update `SecondaryCoordinator` to fetch system status
- [ ] Add `SystemCPUSensor` to sensor.py
- [ ] Add `SystemMemorySensor` to sensor.py
- [ ] Test and verify data updates

**ISAPI Endpoints:**
- `GET /ISAPI/System/status`

---

### Phase 3: Channel Status Sensors
**Goal:** Expose recording status, connection status, signal quality per channel

- [ ] Research actual API response format (create debug sensor first)
- [ ] Add `get_all_channel_status()` to ISAPI client
- [ ] Add `get_channel_status(channel_id)` to ISAPI client
- [ ] Update coordinator to fetch channel status
- [ ] Create `ChannelStatusSensor` class
- [ ] Parse and expose relevant attributes:
  - [ ] Recording status (yes/no)
  - [ ] Connection status (online/offline)
  - [ ] Signal quality (if available)
  - [ ] Video loss detection
- [ ] Test with multi-channel NVR
- [ ] Add per-channel sensors for each camera

**ISAPI Endpoints:**
- `GET /ISAPI/System/workingstatus/chanStatus?format=json`
- `POST /ISAPI/System/Video/inputs/channels?format=json`
- `POST /ISAPI/System/Video/inputs/channels/<id>?format=json`

---

### Phase 4: I/O Status Sensors
**Goal:** Expose triggered alarm inputs/outputs beyond current binary sensors

- [ ] Research actual API response format
- [ ] Add `get_io_status()` to ISAPI client
- [ ] Update coordinator to fetch I/O status
- [ ] Determine if new sensors needed (may already be covered)
- [ ] Test with actual I/O triggers

**ISAPI Endpoints:**
- `GET /ISAPI/System/workingstatus/IOStatus?format=json`

---

### Phase 5: HDD Working Status
**Goal:** Enhanced HDD monitoring beyond current storage sensors

- [ ] Research actual API response format
- [ ] Add `get_hdd_status()` to ISAPI client
- [ ] Update coordinator to fetch HDD status
- [ ] Add recording status per HDD
- [ ] Add HDD health indicators
- [ ] Test with multiple HDDs

**ISAPI Endpoints:**
- `GET /ISAPI/System/workingstatus/hdStatus?format=json`

---

### Phase 6: Device Capabilities Detection
**Goal:** Auto-detect what features the device supports

- [ ] Add `get_device_capabilities()` to ISAPI client
- [ ] Parse capability XML/JSON
- [ ] Only create entities for supported features
- [ ] Handle gracefully when features unavailable

**ISAPI Endpoints:**
- `GET /ISAPI/System/capabilities`
- `GET /ISAPI/System/workingstatus/capabilities?format=json`

---

### Phase 7: Auto-Discovery (Optional/Future)
**Goal:** Automatically discover Hikvision devices on network during setup

- [ ] Research SADP protocol (UDP port 37020)
- [ ] Research SSDP/UPnP discovery
- [ ] Implement discovery service
- [ ] Add to config flow as optional step
- [ ] Test on various network configurations

**Notes:** This is complex and may require separate library. Consider for v2.0.

---

## Development Workflow

### Adding Each Feature:

1. **Research** - Check actual API response with debug sensor
2. **Implement** - Add ISAPI method, coordinator update, sensor class
3. **Test** - Verify on real hardware
4. **Commit** - `git commit -m "feat: add [feature name]"`
5. **Document** - Update this log with findings

### Testing Checklist Per Feature:

- [ ] Entity creates successfully
- [ ] Data updates correctly
- [ ] No errors in logs
- [ ] Survives HA restart
- [ ] Handles device offline gracefully
- [ ] Attributes populated correctly

---

## Known Issues / Blockers

*(Add issues as they're discovered)*

- None yet

---

## Testing Notes

**Test Environment:**
- NVR Model: DS-7216HQHI-K1
- Firmware: [Your version]
- Cameras Connected: 1 Analog , 1 IP
- Home Assistant Version: 
    Core
    2026.1.3
    Supervisor
    2026.01.1
    Operating System
    17.0

**Test Results:**
*(Sensors seem to respond on time after a round of trials, detection is immediate - achieved step 1 succefully. hurray!)*

---

## Decisions Log

**2026-02-02:**
- Created dev branch for feature development
- Decided to add debug sensors first to inspect API responses
- Will implement features incrementally rather than all at once

---

## Resources

- [Hikvision Next Original Repo](https://github.com/maciej-or/hikvision_next)
- [my Fork](https://github.com/daveinc/hikvision_next)

---

## Completion Status

**Overall Progress:** 0/? phases complete (TBA)

Last Updated: 2026-02-02
