"""Data models for Provision ISR API responses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _extract_value(data: dict[str, Any], key: str, default: Any = None) -> Any:
    """Extract value from XML dict, handling CDATA and type attributes.
    
    Args:
        data: Dictionary from xmltodict
        key: Key to extract
        default: Default value if key not found
        
    Returns:
        Extracted value
    """
    value = data.get(key, default)
    
    # Handle CDATA wrapper
    if isinstance(value, dict) and "#text" in value:
        return value["#text"]
    
    # Handle boolean strings
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return value.lower() == "true"
    
    # Handle numeric strings
    if isinstance(value, str) and value.isdigit():
        return int(value)
    
    return value


@dataclass
class DeviceInfo:
    """Device information from GetDeviceInfo."""
    
    device_name: str
    model: str
    brand: str
    device_description: str
    software_version: str
    software_build_date: str
    hardware_version: str
    mac: str
    serial_number: str
    api_version: str
    
    # Channel counts
    channel_max_count: int
    audio_in_count: int = 0
    audio_out_count: int = 0
    alarm_in_count: int = 0
    alarm_out_count: int = 0
    
    # Capabilities
    integrated_ptz: bool = False
    support_rs485_ptz: bool = False
    support_sd_card: bool = False
    support_api_long_polling: bool = False
    support_motion_sens: bool = False
    support_https: bool = False
    
    # Additional info
    device_type: int | None = None
    onvif_version: str | None = None
    kernel_version: str | None = None
    device_activated: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceInfo:
        """Create DeviceInfo from parsed XML dict.
        
        Args:
            data: Dictionary from xmltodict parsing of deviceInfo element
            
        Returns:
            DeviceInfo instance
        """
        return cls(
            device_name=_extract_value(data, "deviceName", "Unknown"),
            model=_extract_value(data, "model", "Unknown"),
            brand=_extract_value(data, "brand", "Provision ISR"),
            device_description=_extract_value(data, "deviceDescription", "IP Camera"),
            software_version=_extract_value(data, "softwareVersion", "Unknown"),
            software_build_date=_extract_value(data, "softwareBuildDate", "Unknown"),
            hardware_version=_extract_value(data, "hardwareVersion", "Unknown"),
            mac=_extract_value(data, "mac", "00:00:00:00:00:00"),
            serial_number=_extract_value(data, "sn", "Unknown"),
            api_version=_extract_value(data, "apiVersion", "1.0"),
            channel_max_count=_extract_value(data, "chlMaxCount", 1),
            audio_in_count=_extract_value(data, "audioInCount", 0),
            audio_out_count=_extract_value(data, "audioOutCount", 0),
            alarm_in_count=_extract_value(data, "alarmInCount", 0),
            alarm_out_count=_extract_value(data, "alarmOutCount", 0),
            integrated_ptz=_extract_value(data, "integratedPtz", False),
            support_rs485_ptz=_extract_value(data, "supportRS485Ptz", False),
            support_sd_card=_extract_value(data, "supportSDCard", False),
            support_api_long_polling=_extract_value(data, "supportAPILongPolling", False),
            support_motion_sens=_extract_value(data, "supportMotionSens", False),
            support_https=_extract_value(data, "supportHttps", False),
            device_type=_extract_value(data, "deviceType"),
            onvif_version=_extract_value(data, "onvifVer"),
            kernel_version=_extract_value(data, "kernelVersion"),
            device_activated=_extract_value(data, "deviceActivated", True),
        )

    def is_nvr(self) -> bool:
        """Check if device is an NVR (multiple channels).
        
        Returns:
            True if device appears to be an NVR
        """
        # If max channel count > 1, it's likely an NVR
        # Also check device description
        return (
            self.channel_max_count > 1
            or "NVR" in self.device_description.upper()
        )


@dataclass
class Channel:
    """Channel information."""
    
    channel_id: str
    status: str  # online, offline, videoOn, videoLoss
    
    @property
    def is_online(self) -> bool:
        """Check if channel is online."""
        return self.status in ("online", "videoOn")


@dataclass
class ChannelList:
    """Channel list from GetChannelList (NVR only)."""
    
    channels: list[Channel]
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChannelList:
        """Create ChannelList from parsed XML dict.
        
        Args:
            data: Dictionary from xmltodict parsing
            
        Returns:
            ChannelList instance
        """
        channels = []
        channel_list = data.get("channelIDList", {})
        
        # Handle list items
        items = channel_list.get("item", [])
        if not isinstance(items, list):
            items = [items]
        
        for item in items:
            if isinstance(item, dict):
                channel_id = item.get("#text", "")
                status = item.get("@channelStatus", "offline")
            else:
                # Simple string value
                channel_id = str(item)
                status = "online"
            
            channels.append(Channel(channel_id=channel_id, status=status))
        
        return cls(channels=channels)


@dataclass
class DiskInfo:
    """Disk information from GetDiskInfo."""
    
    total_space_mb: int
    free_space_mb: int
    status: str  # read, read/write, unformat, formatting, exception
    disk_id: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiskInfo:
        """Create DiskInfo from parsed XML dict.
        
        Args:
            data: Dictionary from xmltodict parsing
            
        Returns:
            DiskInfo instance
        """
        disk_list = data.get("diskInfo", {})
        items = disk_list.get("item", [])
        
        # Take first disk if multiple
        if isinstance(items, list) and items:
            disk_data = items[0]
        elif isinstance(items, dict):
            disk_data = items
        else:
            # No disk found
            return cls(
                total_space_mb=0,
                free_space_mb=0,
                status="exception",
            )
        
        return cls(
            disk_id=_extract_value(disk_data, "id"),
            total_space_mb=_extract_value(disk_data, "totalSpace", 0),
            free_space_mb=_extract_value(disk_data, "freeSpace", 0),
            status=_extract_value(disk_data, "diskStatus", "exception"),
        )
    
    @property
    def is_healthy(self) -> bool:
        """Check if disk is healthy and writable."""
        return self.status in ("read/write", "read")


@dataclass
class StreamInfo:
    """Individual stream information."""
    
    stream_id: int
    stream_name: str
    resolution: str
    max_frame_rate: int
    encode_type: str
    
    def get_rtsp_url(self, host: str, port: int, username: str, password: str, is_nvr: bool = False, channel_id: int = 1) -> str:
        """Build RTSP URL for this stream.
        
        Args:
            host: Device IP
            port: RTSP port
            username: Username for auth
            password: Password for auth
            is_nvr: True if device is NVR, False if standalone camera
            channel_id: Channel ID (for NVR)
            
        Returns:
            RTSP URL
        """
        if is_nvr:
            # NVR format: rtsp://user:pass@host:port?chID=X&streamType=main
            stream_type = "main" if self.stream_id == 1 else "sub"
            return f"rtsp://{username}:{password}@{host}:{port}?chID={channel_id}&streamType={stream_type}"
        else:
            # IPC format: rtsp://user:pass@host:port/streamName
            return f"rtsp://{username}:{password}@{host}:{port}/{self.stream_name}"


@dataclass
class StreamCaps:
    """Stream capabilities from GetStreamCaps."""
    
    rtsp_port: int
    streams: list[StreamInfo]
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StreamCaps:
        """Create StreamCaps from parsed XML dict.
        
        Args:
            data: Dictionary from xmltodict parsing
            
        Returns:
            StreamCaps instance
        """
        rtsp_port = _extract_value(data, "rtspPort", 554)
        
        stream_list = data.get("streamList", {})
        items = stream_list.get("item", [])
        
        if not isinstance(items, list):
            items = [items]
        
        streams = []
        for item in items:
            if not isinstance(item, dict):
                continue
            
            stream_id = int(item.get("@id", 0))
            stream_name = _extract_value(item, "streamName", f"profile{stream_id}")
            
            # Get resolution capabilities
            resolution_caps = item.get("resolutionCaps", {})
            res_items = resolution_caps.get("item", [])
            if not isinstance(res_items, list):
                res_items = [res_items]
            
            # Take first resolution option
            resolution = "1920x1080"  # default
            max_frame_rate = 25  # default
            
            if res_items and isinstance(res_items[0], dict):
                resolution = _extract_value(res_items[0], "#text", resolution)
                max_frame_rate = _extract_value(res_items[0], "@maxFrameRate", max_frame_rate)
            elif res_items and isinstance(res_items[0], str):
                resolution = res_items[0]
            
            # Get encode type
            encode_caps = item.get("encodeTypeCaps", {})
            enc_items = encode_caps.get("item", [])
            if not isinstance(enc_items, list):
                enc_items = [enc_items]
            
            encode_type = enc_items[0] if enc_items else "h264"
            
            streams.append(StreamInfo(
                stream_id=stream_id,
                stream_name=stream_name,
                resolution=resolution,
                max_frame_rate=max_frame_rate,
                encode_type=encode_type,
            ))
        
        return cls(
            rtsp_port=rtsp_port,
            streams=streams,
        )
    
    def get_main_stream(self) -> StreamInfo | None:
        """Get main stream (highest quality)."""
        return self.streams[0] if self.streams else None
    
    def get_sub_stream(self) -> StreamInfo | None:
        """Get sub stream (lower quality for preview)."""
        return self.streams[1] if len(self.streams) > 1 else None
