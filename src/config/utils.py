import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

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
    
    def get_camera_by_id(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Get camera configuration by ID
        
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
        Get camera configuration by name
        
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
    
    def update_camera_status(self, camera_id: str, status: str) -> bool:
        """
        Update camera status
        
        Args:
            camera_id: The camera ID to update
            status: New status ('working', 'not_working', 'error')
            
        Returns:
            True if successful, False otherwise
        """
        cameras = self.get_all_cameras()
        for camera in cameras:
            if camera.get('camera_id') == camera_id:
                camera['camera_status'] = status
                return self.save_config()
        return False
    
    def update_parking_status(self, camera_id: str, parking_status: str) -> bool:
        """
        Update parking status for a camera
        
        Args:
            camera_id: The camera ID to update
            parking_status: New parking status ('available', 'occupied', 'unknown')
            
        Returns:
            True if successful, False otherwise
        """
        cameras = self.get_all_cameras()
        for camera in cameras:
            if camera.get('camera_id') == camera_id:
                camera['parking_status'] = parking_status
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
        if not self._config_data:
            self.load_config()
        
        # Validate required fields
        required_fields = ['camera_id', 'camera_name', 'location']
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
    
    def remove_camera(self, camera_id: str) -> bool:
        """
        Remove a camera configuration
        
        Args:
            camera_id: The camera ID to remove
            
        Returns:
            True if successful, False otherwise
        """
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
        if not self._config_data:
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
                'camera_status': camera.get('camera_status', 'unknown'),
                'parking_status': camera.get('parking_status', 'unknown'),
                'image': camera.get('image_path', ''),
                'ip_address': camera.get('ip_address', ''),
                'video_source': camera.get('video_source', ''),
                'resolution': camera.get('resolution', {}),
                'fps': camera.get('fps', 0),
                'coordinates': camera.get('coordinates', {}),
                'detection_zones': camera.get('detection_zones', []),
                'alerts': camera.get('alerts', {}),
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