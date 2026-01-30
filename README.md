# Hikvision Next - Enhanced Version

> **Note**: This is a fork of [maciej-or/hikvision_next](https://github.com/maciej-or/hikvision_next) with critical bug fixes and improvements.

## 🚀 What's Fixed in This Fork

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
   - **URL**: `https://github.com/YOUR_USERNAME/hikvision_next`
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
- **Firmware**: [Add your firmware version]
- **Home Assistant**: 2024.1+ (should work on older versions too)

Please report your working configurations in [Issues](https://github.com/YOUR_USERNAME/hikvision_next/issues) to help others!

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

1. Open an [Issue](https://github.com/YOUR_USERNAME/hikvision_next/issues)
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

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/hikvision_next/issues)
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
