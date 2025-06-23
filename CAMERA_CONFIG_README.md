# Camera Configuration Documentation

## Overview

The Parking System now uses a JSON-based configuration system to manage camera data. This provides a more realistic and structured approach to storing camera information, making it easier to read, write, and maintain camera configurations.

## Configuration File Location

The camera configuration is stored in:
```
src/config/mock-cameras-configuration.json
```

## JSON Structure

### Main Configuration Structure
```json
{
  "cameras": [...],
  "system_settings": {...},
  "last_updated": "2024-12-23T10:00:00Z",
  "config_version": "1.0.0"
}
```

### Camera Object Structure
Each camera in the `cameras` array has the following properties:

```json
{
  "camera_id": "CAM_001",           // Unique identifier for the camera
  "camera_name": "Main Gate Camera", // Display name
  "location": "Building Main Entrance", // Physical location
  "ip_address": "192.168.1.101",   // Camera IP address
  "port": 8080,                    // Camera port
  "username": "admin",             // Authentication username
  "password": "password123",       // Authentication password
  "camera_status": "working",      // Status: "working", "not_working", "error"
  "parking_status": "available",   // Parking: "available", "occupied", "unknown"
  "image_path": "image/mock-cctv-1.jpg", // Path to camera image
  "video_source": "rtsp://192.168.1.101:554/stream1", // Video stream URL
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "fps": 30,                       // Frames per second
  "coordinates": {
    "latitude": 13.7563,
    "longitude": 100.5018
  },
  "detection_zones": [             // Areas for parking detection
    {
      "zone_id": "ZONE_001",
      "zone_name": "Parking Area A",
      "polygon_points": [
        {"x": 100, "y": 150},
        {"x": 400, "y": 150},
        {"x": 450, "y": 300},
        {"x": 50, "y": 300}
      ]
    }
  ],
  "alerts": {
    "email_notifications": true,
    "sms_notifications": false,
    "sound_alert": true
  },
  "last_maintenance": "2024-12-15T10:30:00Z",
  "installation_date": "2024-01-15T09:00:00Z"
}
```

### System Settings Structure
```json
{
  "default_detection_confidence": 0.7,
  "alert_cooldown_minutes": 5,
  "auto_cleanup_days": 30,
  "backup_enabled": true,
  "backup_schedule": "daily",
  "timezone": "Asia/Bangkok",
  "language": "en"
}
```

## Usage in Code

### Using the CameraConfigManager

```python
from src.config.utils import CameraConfigManager

# Initialize the config manager
config_manager = CameraConfigManager()

# Get all cameras
cameras = config_manager.get_all_cameras()

# Get camera names for UI
camera_names = config_manager.get_camera_names()

# Get camera statuses
camera_statuses = config_manager.get_camera_statuses()

# Get a specific camera by name
camera = config_manager.get_camera_by_name("Main Gate Camera")

# Get a specific camera by ID
camera = config_manager.get_camera_by_id("CAM_001")

# Update camera status
config_manager.update_camera_status("CAM_001", "working")

# Update parking status
config_manager.update_parking_status("CAM_001", "occupied")

# Get data formatted for UI components
ui_cameras = config_manager.get_cameras_for_ui()
```

### UI Integration

The Dashboard and Window classes now automatically load camera data from the JSON configuration:

```python
# The Dashboard will automatically load from JSON if no parameters are provided
dashboard = Dashboard()

# Or you can still provide manual data for backward compatibility
dashboard = Dashboard(cameras_name=["Cam1", "Cam2"], camera_statuses=["working", "error"])
```

## Configuration Management Methods

### Reading Configuration
- `load_config()`: Load configuration from JSON file
- `get_all_cameras()`: Get all camera configurations
- `get_camera_by_id(camera_id)`: Get camera by ID
- `get_camera_by_name(camera_name)`: Get camera by name
- `get_camera_names()`: Get list of camera names
- `get_camera_statuses()`: Get list of camera statuses
- `get_system_settings()`: Get system settings

### Writing Configuration
- `save_config()`: Save current configuration to file
- `update_camera_status(camera_id, status)`: Update camera status
- `update_parking_status(camera_id, parking_status)`: Update parking status
- `add_camera(camera_config)`: Add new camera
- `remove_camera(camera_id)`: Remove camera
- `update_system_settings(settings)`: Update system settings

### UI Specific
- `get_cameras_for_ui()`: Get camera data formatted for UI components
- `refresh_camera_data()`: Refresh camera data from configuration
- `update_camera_status_in_config()`: Update status and refresh UI
- `update_parking_status_in_config()`: Update parking status and refresh UI

## Example Configuration

The system comes with a pre-configured example with 4 cameras:

1. **Main Gate Camera** (CAM_001) - Working, Available parking
2. **Parking Lot A Camera** (CAM_002) - Working, Occupied parking
3. **Security Checkpoint** (CAM_003) - Error status, Unknown parking
4. **Back Gate Monitor** (CAM_004) - Not working, Available parking

## Testing

You can test the configuration system using the provided test script:

```bash
python test_camera_config.py
```

This will verify that:
- JSON configuration loads correctly
- All camera data is accessible
- UI formatting works properly
- System settings are available

## Backward Compatibility

The system maintains backward compatibility with the old manual camera configuration format. You can still pass camera data directly to components if needed:

```python
# Old format still works
cameras = [
    {"name": "Camera 1", "status": "online"},
    {"name": "Camera 2", "status": "offline"}
]
dashboard = Dashboard(cameras_name=[c["name"] for c in cameras], 
                     camera_statuses=[c["status"] for c in cameras])
```

## Benefits of JSON Configuration

1. **Realistic Data Structure**: Matches real-world camera system requirements
2. **Easy to Read/Write**: Human-readable format for configuration
3. **Extensible**: Easy to add new properties without code changes
4. **Centralized**: All camera configuration in one place
5. **Version Control Friendly**: Easy to track changes in configuration
6. **Professional**: Industry-standard approach for configuration management

## File Paths

- Configuration File: `src/config/mock-cameras-configuration.json`
- Utility Functions: `src/config/utils.py`
- Dashboard Integration: `src/gui/Dashboard.py`
- Window Integration: `src/gui/window.py`
- Test Script: `test_camera_config.py`
