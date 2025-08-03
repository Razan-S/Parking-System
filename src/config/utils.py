import json
import os
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime
from src.enums import CameraStatus, ParkingStatus

if TYPE_CHECKING:
    from typing import Self

class CameraReference:
    """
    Helper class to hold camera ID and name together for safer operations
    """
    def __init__(self, camera_id: str, camera_name: str):
        self.camera_id = camera_id
        self.camera_name = camera_name
    
    def __str__(self):
        return f"Camera({self.camera_id}, {self.camera_name})"
    
    def __repr__(self):
        return self.__str__()
    
    def is_valid(self) -> bool:
        """Check if both ID and name are present"""
        return bool(self.camera_id and self.camera_name)

class CameraConfigManager:
    """Manager class for handling camera configuration operations"""
    
    def __init__(self, config_file_path: str = None):
        """
        Initialize the camera configuration manager
        
        Args:
            config_file_path: Path to the JSON configuration file
        """
        if config_file_path is None:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_file_path = os.path.join(current_dir, "mock-cameras-configuration.json")
        
        self.config_file_path = config_file_path
        self._config_data = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load camera configuration from JSON file
        
        Returns:
            Dictionary containing the configuration data
        """
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as file:
                self._config_data = json.load(file)
                return self._config_data
        except FileNotFoundError:
            print(f"Configuration file not found: {self.config_file_path}")
            return self._create_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON configuration: {e}")
            return self._create_default_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return self._create_default_config()
    
    def save_config(self) -> bool:
        """
        Save current configuration to JSON file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update last_updated timestamp
            if self._config_data:
                self._config_data['last_updated'] = datetime.now().isoformat() + 'Z'
            
            with open(self.config_file_path, 'w', encoding='utf-8') as file:
                json.dump(self._config_data, file, indent=2, ensure_ascii=False)
                return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_all_cameras(self) -> List[Dict[str, Any]]:
        """
        Get all camera configurations
        
        Returns:
            List of camera configuration dictionaries
        """
        if not self._config_data:
            self.load_config()
        
        return self._config_data.get('cameras', [])
    
    def get_camera_ids(self) -> List[str]:
        """
        Get list of all camera IDs from configuration
        
        Returns:
            List of camera IDs
        """
        cameras = self.get_all_cameras()
        return [camera.get('camera_id') for camera in cameras if camera.get('camera_id')]
    
    def get_camera_by_id_and_name(self, camera_id: str, camera_name: str) -> Optional[Dict[str, Any]]:
        """
        Get camera configuration by both ID and name (both required)
        
        Args:
            camera_id: The camera ID to search for
            camera_name: The camera name to search for
            
        Returns:
            Camera configuration dictionary or None if not found
        """
        cameras = self.get_all_cameras()
        for camera in cameras:
            if camera.get('camera_id') == camera_id and camera.get('camera_name') == camera_name:
                return camera
        return None
    
    def get_camera_by_id(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Get camera configuration by ID (legacy method - deprecated)
        
        Args:
            camera_id: The camera ID to search for
            
        Returns:
            Camera configuration dictionary or None if not found
        """
        cameras = self.get_all_cameras()
        for camera in cameras:
            if camera.get('camera_id') == camera_id:
                return camera
        return None
    
    def get_camera_by_name(self, camera_name: str) -> Optional[Dict[str, Any]]:
        """
        Get camera configuration by name (legacy method - deprecated)
        
        Args:
            camera_name: The camera name to search for
            
        Returns:
            Camera configuration dictionary or None if not found
        """
        cameras = self.get_all_cameras()
        for camera in cameras:
            if camera.get('camera_name') == camera_name:
                return camera
        return None
    
    def get_camera_names(self) -> List[str]:
        """
        Get list of all camera names
        
        Returns:
            List of camera names
        """
        cameras = self.get_all_cameras()
        return [camera.get('camera_name', 'Unknown') for camera in cameras]
    
    def get_camera_statuses(self) -> List[str]:
        """
        Get list of all camera statuses
        
        Returns:
            List of camera statuses
        """
        cameras = self.get_all_cameras()
        return [camera.get('camera_status', 'unknown') for camera in cameras]
    
    def update_camera_status(self, camera_id: str, camera_name: str, status: str) -> bool:
        """
        Update camera status (requires both camera_id and camera_name)
        
        Args:
            camera_id: The camera ID to update
            camera_name: The camera name to verify
            status: New status ('working', 'not_working', 'error')
            
        Returns:
            True if successful, False otherwise
        """
        # Load latest configuration before updating
        self.load_config()
        
        camera = self.get_camera_by_id_and_name(camera_id, camera_name)
        if camera:
            camera['camera_status'] = status
            return self.save_config()
        return False
    
    def update_camera_status_legacy(self, camera_id: str, status: str) -> bool:
        """
        Update camera status (legacy method - deprecated)
        
        Args:
            camera_id: The camera ID to update
            status: New status ('working', 'not_working', 'error')
            
        Returns:
            True if successful, False otherwise
        """
        # Load latest configuration before updating
        self.load_config()
        
        cameras = self.get_all_cameras()
        for camera in cameras:
            if camera.get('camera_id') == camera_id:
                camera['camera_status'] = status
                return self.save_config()
        return False
    
    def update_parking_status(self, camera_id: str, camera_name: str, parking_status: str) -> bool:
        """
        Update parking status for a camera (requires both camera_id and camera_name)
        
        Args:
            camera_id: The camera ID to update
            camera_name: The camera name to verify
            parking_status: New parking status ('available', 'occupied', 'unknown')
            
        Returns:
            True if successful, False otherwise
        """
        # Load latest configuration before updating
        self.load_config()
        
        camera = self.get_camera_by_id_and_name(camera_id, camera_name)
        if camera:
            camera['parking_status'] = parking_status
            return self.save_config()
        return False
    
    def update_parking_status_legacy(self, camera_id: str, parking_status: str) -> bool:
        """
        Update parking status for a camera (legacy method - deprecated)
        
        Args:
            camera_id: The camera ID to update
            parking_status: New parking status ('available', 'occupied', 'unknown')
            
        Returns:
            True if successful, False otherwise
        """
        # Load latest configuration before updating
        self.load_config()
        
        cameras = self.get_all_cameras()
        for camera in cameras:
            if camera.get('camera_id') == camera_id:
                camera['parking_status'] = parking_status
                return self.save_config()
        return False
    
    def update_detection_zone(self, camera_id: str, camera_name: str, detection_zones: List[Dict]) -> bool:
        """
        Update detection zones for a camera (requires both camera_id and camera_name)
        
        Args:
            camera_id: The camera ID to update
            camera_name: The camera name to verify
            detection_zones: List of frame objects containing zone data
            
        Returns:
            True if successful, False otherwise
        """
        if detection_zones is None or not isinstance(detection_zones, list):
            print("Invalid detection zones provided")
            return False
        
        # Load latest configuration before updating
        self.load_config()
        
        # Convert frame data to detection zones
        zones = []
        for frame_data in detection_zones:
            if not isinstance(frame_data, dict) or 'coordinates' not in frame_data:
                continue
                
            # Convert coordinates to proper format
            polygon_points = []
            for coord in frame_data['coordinates']:
                if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                    polygon_points.append({"x": int(coord[0]), "y": int(coord[1])})
            
            zone = {
                'zone_id': f"zone_{frame_data.get('id', len(zones) + 1):03d}",
                'zone_name': f"Detection Zone {frame_data.get('id', len(zones) + 1)}",
                'polygon_points': polygon_points
            }
            zones.append(zone)

        camera = self.get_camera_by_id_and_name(camera_id, camera_name)
        if camera:
            # Replace all detection zones with new merged zones
            camera['detection_zones'] = zones
            camera['last_updated'] = datetime.now().isoformat() + 'Z'
            return self.save_config()
        return False
    
    def update_detection_zone_legacy(self, camera_id: str, detection_zones: List[Dict]) -> bool:
        """
        Update detection zones for a camera (legacy method - deprecated)
        
        Args:
            camera_id: The camera ID to update
            detection_zones: List of frame objects containing zone data
            
        Returns:
            True if successful, False otherwise
        """
        if detection_zones is None or not isinstance(detection_zones, list):
            print("Invalid detection zones provided")
            return False
        
        # Load latest configuration before updating
        self.load_config()
        
        # Convert frame data to detection zones
        zones = []
        for frame_data in detection_zones:
            if not isinstance(frame_data, dict) or 'coordinates' not in frame_data:
                continue
                
            # Convert coordinates to proper format
            polygon_points = []
            for coord in frame_data['coordinates']:
                if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                    polygon_points.append({"x": int(coord[0]), "y": int(coord[1])})
            
            zone = {
                'zone_id': f"zone_{frame_data.get('id', len(zones) + 1):03d}",
                'zone_name': f"Detection Zone {frame_data.get('id', len(zones) + 1)}",
                'polygon_points': polygon_points
            }
            zones.append(zone)

        cameras = self.get_all_cameras()
        for camera in cameras:
            if camera.get('camera_id') == camera_id:
                # Replace all detection zones with new merged zones
                camera['detection_zones'] = zones
                camera['last_updated'] = datetime.now().isoformat() + 'Z'
                return self.save_config()
        return False
        
    def add_camera(self, camera_config: Dict[str, Any]) -> bool:
        """
        Add a new camera configuration
        
        Args:
            camera_config: Dictionary containing camera configuration
            
        Returns:
            True if successful, False otherwise
        """
        # Load latest configuration before adding
        self.load_config()
        
        # Validate required fields
        required_fields = ['camera_id', 'camera_name', 'video_source', ]
        for field in required_fields:
            if field not in camera_config:
                print(f"Missing required field: {field}")
                return False
        
        # Check if camera ID already exists
        if self.get_camera_by_id(camera_config['camera_id']):
            print(f"Camera with ID {camera_config['camera_id']} already exists")
            return False
        
        self._config_data['cameras'].append(camera_config)
        return self.save_config()
    
    def remove_camera(self, camera_id: str, camera_name: str) -> bool:
        """
        Remove a camera configuration (requires both camera_id and camera_name)
        
        Args:
            camera_id: The camera ID to remove
            camera_name: The camera name to verify
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load latest configuration before removing
            self.load_config()
            
            print(f"DEBUG: remove_camera called with ID: '{camera_id}', Name: '{camera_name}'")
            
            cameras = self.get_all_cameras()
            print(f"DEBUG: Total cameras in config: {len(cameras)}")
            
            # Debug: Print all camera IDs and names
            for i, camera in enumerate(cameras):
                cam_id = camera.get('camera_id', 'MISSING')
                cam_name = camera.get('camera_name', 'MISSING')
                print(f"DEBUG: Camera {i}: ID='{cam_id}', Name='{cam_name}'")
            
            for i, camera in enumerate(cameras):
                cam_id = camera.get('camera_id')
                cam_name = camera.get('camera_name')
                
                print(f"DEBUG: Checking camera {i}: ID='{cam_id}' vs '{camera_id}', Name='{cam_name}' vs '{camera_name}'")
                
                if cam_id == camera_id and cam_name == camera_name:
                    print(f"DEBUG: Found matching camera at index {i}, removing...")
                    del self._config_data['cameras'][i]
                    success = self.save_config()
                    print(f"DEBUG: Save result: {success}")
                    return success
            
            print(f"DEBUG: No matching camera found for ID: '{camera_id}', Name: '{camera_name}'")
            return False
            
        except Exception as e:
            print(f"DEBUG: Exception in remove_camera: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_camera_legacy(self, camera_id: str) -> bool:
        """
        Remove a camera configuration (legacy method - deprecated)
        
        Args:
            camera_id: The camera ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        # Load latest configuration before removing
        self.load_config()
        
        cameras = self.get_all_cameras()
        for i, camera in enumerate(cameras):
            if camera.get('camera_id') == camera_id:
                del self._config_data['cameras'][i]
                return self.save_config()
        return False
    
    def get_system_settings(self) -> Dict[str, Any]:
        """
        Get system settings
        
        Returns:
            Dictionary containing system settings
        """
        if not self._config_data:
            self.load_config()
        
        return self._config_data.get('system_settings', {})
    
    def update_system_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Update system settings
        
        Args:
            settings: Dictionary containing settings to update
            
        Returns:
            True if successful, False otherwise
        """
        # Load latest configuration before updating
        self.load_config()
        
        if 'system_settings' not in self._config_data:
            self._config_data['system_settings'] = {}
        
        self._config_data['system_settings'].update(settings)
        return self.save_config()
    
    def get_cameras_for_ui(self) -> List[Dict[str, Any]]:
        """
        Get camera data formatted for UI components
        
        Returns:
            List of camera dictionaries formatted for UI
        """
        cameras = self.get_all_cameras()
        ui_cameras = []
        
        for camera in cameras:
            ui_camera = {
                'camera_name': camera.get('camera_name', 'Unknown'),
                'camera_id': camera.get('camera_id', '000'),
                'location': camera.get('location', 'Unknown Location'),
                'camera_status': camera.get('camera_status', CameraStatus.NOT_WORKING.value),
                'parking_status': camera.get('parking_status', ParkingStatus.UNKNOWN.value),
                'image': camera.get('image_path', ''),
                'ip_address': camera.get('ip_address', ''),
                'video_source': camera.get('video_source', ''),
                'resolution': camera.get('resolution', {}),
                'detection_zones': camera.get('detection_zones', []),
                'last_maintenance': camera.get('last_maintenance', ''),
                'installation_date': camera.get('installation_date', '')
            }
            ui_cameras.append(ui_camera)
        
        return ui_cameras
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration if file doesn't exist or is corrupted
        
        Returns:
            Default configuration dictionary
        """
        default_config = {
            "cameras": [],
            "system_settings": {
                "default_detection_confidence": 0.7,
                "alert_cooldown_minutes": 5,
                "auto_cleanup_days": 30,
                "backup_enabled": True,
                "backup_schedule": "daily",
                "timezone": "Asia/Bangkok",
                "language": "en"
            },
            "last_updated": datetime.now().isoformat() + 'Z',
            "config_version": "1.0.0"
        }
        
        self._config_data = default_config
        self.save_config()
        return default_config
    
    def get_camera_info(self, camera_id: str = None, camera_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Get camera information using either camera_id or camera_name
        Returns camera with both id and name for validation purposes
        
        Args:
            camera_id: The camera ID to search for (optional)
            camera_name: The camera name to search for (optional)
            
        Returns:
            Camera configuration dictionary or None if not found
        """
        if camera_id and camera_name:
            return self.get_camera_by_id_and_name(camera_id, camera_name)
        elif camera_id:
            return self.get_camera_by_id(camera_id)
        elif camera_name:
            return self.get_camera_by_name(camera_name)
        else:
            return None
    
    def validate_camera_exists(self, camera_id: str, camera_name: str) -> bool:
        """
        Validate that a camera exists with the given ID and name combination
        
        Args:
            camera_id: The camera ID to validate
            camera_name: The camera name to validate
            
        Returns:
            True if camera exists with both matching fields, False otherwise
        """
        camera = self.get_camera_by_id_and_name(camera_id, camera_name)
        return camera is not None

    def is_id_exists(self, camera_id: str) -> bool:
        """
        Check if a camera ID already exists in the configuration
        
        Args:
            camera_id: The camera ID to check
            
        Returns:
            True if ID exists, False otherwise
        """
        cameras = self.get_all_cameras()
        for camera in cameras:
            if camera.get('camera_id') == camera_id:
                return True
        return False

    def update_camera_property(self, camera_id: str, camera_name: str, property_name: str, property_value: Any) -> bool:
        """
        Safely update any camera property using both camera_id and camera_name for validation
        
        Args:
            camera_id: The camera ID to update
            camera_name: The camera name to verify
            property_name: Name of the property to update
            property_value: New value for the property
            
        Returns:
            True if successful, False otherwise
        """
        # Load latest configuration before updating
        self.load_config()
        
        camera = self.get_camera_by_id_and_name(camera_id, camera_name)
        if camera:
            camera[property_name] = property_value
            camera['last_updated'] = datetime.now().isoformat() + 'Z'
            return self.save_config()
        return False
    
    def get_camera_reference(self, camera_id: str = None, camera_name: str = None) -> Optional[CameraReference]:
        """
        Get a CameraReference object for safer operations
        
        Args:
            camera_id: The camera ID to search for (optional)
            camera_name: The camera name to search for (optional)
            
        Returns:
            CameraReference object or None if not found
        """
        camera = self.get_camera_info(camera_id, camera_name)
        if camera:
            return CameraReference(
                camera_id=camera.get('camera_id', ''),
                camera_name=camera.get('camera_name', '')
            )
        return None

    def get_all_camera_references(self) -> List[CameraReference]:
        """
        Get all cameras as CameraReference objects
        
        Returns:
            List of CameraReference objects
        """
        cameras = self.get_all_cameras()
        references = []
        for camera in cameras:
            camera_id = camera.get('camera_id')
            camera_name = camera.get('camera_name')
            if camera_id and camera_name:
                references.append(CameraReference(camera_id, camera_name))
        return references

    def bulk_update_camera_property(self, camera_references: List[CameraReference], property_name: str, property_value: Any) -> Dict[str, bool]:
        """
        Update a property for multiple cameras safely
        
        Args:
            camera_references: List of CameraReference objects
            property_name: Name of the property to update
            property_value: New value for the property
            
        Returns:
            Dictionary mapping camera names to success status
        """
        results = {}
        for camera_ref in camera_references:
            if camera_ref.is_valid():
                success = self.update_camera_property(
                    camera_ref.camera_id, 
                    camera_ref.camera_name, 
                    property_name, 
                    property_value
                )
                results[camera_ref.camera_name] = success
            else:
                results[camera_ref.camera_name] = False
        
        return results

    def verify_camera_integrity(self) -> List[Dict[str, Any]]:
        """
        Verify the integrity of all cameras (check for missing IDs or names)
        
        Returns:
            List of dictionaries describing integrity issues
        """
        cameras = self.get_all_cameras()
        issues = []
        
        for i, camera in enumerate(cameras):
            camera_id = camera.get('camera_id')
            camera_name = camera.get('camera_name')
            
            if not camera_id:
                issues.append({
                    'index': i,
                    'issue': 'missing_camera_id',
                    'camera_name': camera_name or 'Unknown',
                    'description': 'Camera is missing camera_id field'
                })
            
            if not camera_name:
                issues.append({
                    'index': i,
                    'issue': 'missing_camera_name',
                    'camera_id': camera_id or 'Unknown',
                    'description': 'Camera is missing camera_name field'
                })
        
        return issues

    def update_camera_image(self, camera_id: str, image_path: str) -> bool:
        """
        Update the image path for a camera by ID
        
        Args:
            camera_id: The camera ID
            image_path: The new image path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load latest configuration before updating
            self.load_config()
            
            cameras = self.get_all_cameras()
            for i, camera in enumerate(cameras):
                if camera.get('camera_id') == camera_id:
                    # Update the image field
                    self._config_data['cameras'][i]['image_path'] = image_path
                    # Save the updated configuration
                    return self.save_config()
            
            return False  # Camera not found
        except Exception as e:
            print(f"Error updating camera image: {e}")
            return False

# Utility functions for backward compatibility
def load_camera_config(config_file_path: str = None) -> Dict[str, Any]:
    """
    Load camera configuration from JSON file
    
    Args:
        config_file_path: Path to the JSON configuration file
        
    Returns:
        Dictionary containing the configuration data
    """
    manager = CameraConfigManager(config_file_path)
    return manager._config_data

def get_cameras_from_config(config_file_path: str = None) -> List[Dict[str, Any]]:
    """
    Get all cameras from configuration file
    
    Args:
        config_file_path: Path to the JSON configuration file
        
    Returns:
        List of camera configuration dictionaries
    """
    manager = CameraConfigManager(config_file_path)
    return manager.get_all_cameras()

def get_camera_names_from_config(config_file_path: str = None) -> List[str]:
    """
    Get camera names from configuration file
    
    Args:
        config_file_path: Path to the JSON configuration file
        
    Returns:
        List of camera names
    """
    manager = CameraConfigManager(config_file_path)
    return manager.get_camera_names()

def get_camera_statuses_from_config(config_file_path: str = None) -> List[str]:
    """
    Get camera statuses from configuration file
    
    Args:
        config_file_path: Path to the JSON configuration file
        
    Returns:
        List of camera statuses
    """
    manager = CameraConfigManager(config_file_path)
    return manager.get_camera_statuses()