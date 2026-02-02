# Hikvision Next - Enhanced Version

> **Note**: This is a fork of [maciej-or/hikvision_next](https://github.com/maciej-or/hikvision_next) with critical bug fixes and improvements.
>
> Disclaimer!

This is a community-made integration.

It is not affiliated with, authorized, or endorsed by Provision-ISR. The Provision-ISR name and logo are trademarks of their respective owners. This project does not attempt to misuse, exploit, or misrepresent the brand. Use at your own risk.

## 🚀 What's Fixed in This Fork

### 🎥 ONVIF PTZ Support
Added PTZ (Pan-Tilt-Zoom) camera controls via ONVIF protocol.

**Features**:
- PTZ movement controls (up, down, left, right, zoom in/out)
- Preset positions
- Patrol routes

**Credit**: Merged from [zyloid's fork](https://github.com/zyloid/hikvision_next)

### ⚡ Instant Binary Sensor Updates
**Problem**: Motion detection and other binary sensors were delayed by up to 2 minutes due to polling every 120 seconds.

**Solution**: Binary sensors now respond **instantly** by properly utilizing Hikvision's real-time event stream with `eventState` (active/inactive) parsing.

**Before**: 
- Motion detected → wait up to 2 minutes for sensor to update
- Sensor stuck ON (never turned OFF automatically)

**After**:
- Motion detected → sensor turns ON **instantly** (<1 second)
- Motion ends → sensor turns OFF **instantly**
- Perfect for automations that need real-time response

---

## 📦 Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the **3 dots** (top right) → **Custom repositories**
3. Add this repository:
   - **URL**: `https://github.com/daveinc/hikvision_next`
   - **Category**: `Integration`
4. Click **"Explore & Download Repositories"**
5. Search for **"Hikvision Next"**
6. Download and restart Home Assistant

### Manual Installation

1. Download this repository
2. Copy the `custom_components/hikvision_next` folder to your HA `config/custom_components/` directory
3. Restart Home Assistant

---

## ✅ Tested On

- **NVR Model**: DS-7216HQHI-K1
- **Firmware**: V4.20.000 build 190724
- Know to be working with : 
Annke N46PCK
DS-7108NI-Q1/8P
DS-7608NI-I2
DS-7608NI-I2/8P
DS-7608NXI-I2/8P/S
DS-7608NXI-K1/8P
DS-7616NI-E2/16P
DS-7616NI-I2/16P
DS-7616NI-Q2
DS-7616NI-Q2/16P
DS-7616NXI-I2/16P/S
DS-7716NI-I4/16P
DS-7732NI-M4
ERI-K104-P4
DVR
iDS-7204HUHI-M1/FA/A
iDS-7204HUHI-M1/P
iDS-7208HQHI-M1(A)/S(C)
IP Camera
Annke C800 (I91BM)
DS-2CD2047G2-LU/SL
DS-2CD2047G2H-LIU
DS-2CD2087G2-LU
DS-2CD2146G2-ISU
DS-2CD2155FWD-I
DS-2CD2346G2-IU
DS-2CD2386G2-IU
DS-2CD2387G2-LU
DS-2CD2387G2H-LISU/SL
DS-2CD2425FWD-IW
DS-2CD2443G0-IW
DS-2CD2532F-IWS
DS-2CD2546G2-IS
DS-2CD2747G2-LZS
DS-2CD2785G1-IZS
DS-2CD2H46G2-IZS (C)
DS-2CD2T46G2-ISU/SL
DS-2CD2T87G2-L
DS-2CD2T87G2P-LSU/SL
DS-2DE4425IW-DE (PTZ)
DS-2SE4C425MWG-E/26
- **Home Assistant**: 2025.X+ (should work on older versions too)

Please report your working configurations in [Issues](https://github.com/daveinc/hikvision_next/issues) to help others!

---

## 🔧 Technical Details

### Changes Made

**1. Models (`isapi/models.py`)**
- Added `event_state: str` field to `AlertInfo` dataclass
- Stores "active" or "inactive" state from event notifications

**2. ISAPI Client (`isapi/isapi.py`)**
- Modified `parse_event_notification()` to extract `<eventState>` from XML
- Passes event state to `AlertInfo` object

**3. Notifications Handler (`notifications.py`)**
- Updated `trigger_sensor()` to use `event_state` for binary sensor state
- Sets sensor ON when `eventState == "active"`
- Sets sensor OFF when `eventState == "inactive"`
- Fires HA events only on motion start (not on motion end)

### Why This Works

Hikvision devices send real-time HTTP POST notifications with XML like:
```xml
<EventNotificationAlert>
  <eventType>VMD</eventType>
  <eventState>active</eventState>  <!-- Motion started -->
  ...
</EventNotificationAlert>
```

And when motion ends:
```xml
<EventNotificationAlert>
  <eventType>VMD</eventType>
  <eventState>inactive</eventState>  <!-- Motion ended -->
  ...
</EventNotificationAlert>
```

The original integration was ignoring the `eventState` field and relying on slow polling instead.

---

## 🐛 Known Issues from Original

These are **still present** (not fixed in this fork yet):

- Camera stream entities may not appear (reported in [home-assistant/core#xxxxx](https://github.com/home-assistant/core/issues))
- [Add any other known issues you're aware of]

---

## 🤝 Contributing

Found a bug? Have an improvement? 

1. Open an [Issue](https://github.com/daveinc/hikvision_next/issues)
2. Or submit a Pull Request!

Since the original repository appears unmaintained (last update 2+ years ago), I'm maintaining this fork for the community.

---

## 📝 Credits

- **Original Author**: [maciej-or](https://github.com/maciej-or) - Created the excellent foundation
- **This Fork**: Fixed instant binary sensor updates
- **Contributors**: [List any contributors who help you]

---

## 📄 License

[Same license as original - usually MIT or Apache 2.0, check the original repo]

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/daveinc/hikvision_next/issues)
- **Community**: Home Assistant Community Forums
- **Documentation**: [Original ISAPI Documentation](link if you have it)

---

## 🔮 Roadmap

Potential future improvements (help wanted!):

- [ ] Fix camera stream entity creation
- [ ] Reduce polling interval for non-critical sensors
- [ ] Add support for [feature X]
- [ ] Improve error handling
- [ ] Add more comprehensive tests

**Want to help?** Pick an item and open an issue to discuss implementation!
