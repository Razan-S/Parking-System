from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, QRunnable, QThreadPool
from PyQt6.QtWidgets import QMessageBox
from src.config.utils import CameraConfigManager
from src.enums import ParkingStatus, CameraStatus
from src.utils import capture_one_frame_silent
import numpy as np
import cv2 as cv
import os
import time
import traceback

from src.yolo import DetectionModule

class CameraWorker(QObject):
    """Worker class that will be moved to a separate thread"""
    # Simplified signals - no data passing, just notifications
    data_updated = pyqtSignal(str)  # camera_id - signals UI to refresh from JSON
    error_occurred = pyqtSignal(str, str)  # camera_id, error_message
    camera_processed = pyqtSignal(str)  # camera_id - processing complete notification
    
    def __init__(self, camera_ids: list[str], interval: int = 5000):
        super().__init__()
        self.config_manager = CameraConfigManager()
        self.camera_ids = camera_ids
        self.detection_module = DetectionModule()
        self.running = False
        self.latest_image_dir = os.path.join(os.path.abspath(os.curdir), "image", "latest")
        self.interval = interval
        self.timer = None  # Will be created in the worker thread
        
        # Create latest image directory if it doesn't exist
        os.makedirs(self.latest_image_dir, exist_ok=True)
        print(f"Latest image directory: {self.latest_image_dir}")
    
    def start_timer(self):
        """Initialize and start timer in the worker thread"""
        if self.timer is None:
            self.timer = QTimer()
            self.timer.setInterval(self.interval)
            self.timer.timeout.connect(self.process_all_cameras)
        self.timer.start()
        print(f"Timer started in worker thread with interval {self.interval}ms")
    
    def stop_timer(self):
        """Stop and clean up timer in the worker thread"""
        if self.timer is not None:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None
        print("Timer stopped and cleaned up in worker thread")
    
    def set_interval(self, interval: int):
        """Set the timer interval"""
        self.interval = interval
        if self.timer is not None:
            self.timer.setInterval(interval)
            print(f"Timer interval updated to {interval}ms")
    
    def process_all_cameras(self):
        """Process all cameras in the list - called by timer"""
        if not self.running:
            return
            
        print("Processing all cameras...")
        for camera_id in self.camera_ids:
            if not self.running:
                break
            self.process_single_camera(camera_id)
    
    def process_single_camera(self, camera_id: str):
        """Process a single camera - capture frame, detect, save to JSON, and notify UI"""
        try:
            # Get camera configuration
            camera_config = self.config_manager.get_camera_by_id(camera_id)
            if not camera_config:
                self.error_occurred.emit(camera_id, f"Camera configuration not found for {camera_id}")
                return
            
            # Capture frame (non-blocking)
            frame = self.capture_frame_async(camera_id)
            if frame is None:
                self.error_occurred.emit(camera_id, f"Failed to capture frame from {camera_id}")
                return
            
            # Save the frame as an image file
            image_path = self.save_frame_as_image(camera_id, frame)
            if image_path:
                # Update the camera configuration with the new image path
                self.config_manager.update_camera_image(camera_id, image_path)
            
            # Get detection zones from configuration
            detection_zones = camera_config.get('detection_zones', [])
            parking_status = ParkingStatus.UNKNOWN.value  # Default
            
            if detection_zones:
                parking_status = self.detection_module.run(frame, detection_zones)
                print(f"Parking status for camera {camera_id}: {parking_status}")
            
            # Save parking status to JSON config
            self.config_manager.update_parking_status_legacy(camera_id, parking_status)
            
            # Update camera status to working (since we successfully processed)
            self.config_manager.update_camera_status_legacy(camera_id, "working")
            
            print(f"Camera {camera_id}: Processing complete, status = {parking_status}")
            
            # Notify UI to refresh data from JSON (no data passing)
            self.data_updated.emit(camera_id)
            self.camera_processed.emit(camera_id)
                
        except Exception as e:
            error_msg = f"Error processing camera {camera_id}: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            
            # Update camera status to error in JSON
            try:
                self.config_manager.update_camera_status_legacy(camera_id, CameraStatus.ERROR.value)
                self.data_updated.emit(camera_id)  # Notify UI even on error
            except:
                pass
                
            self.error_occurred.emit(camera_id, error_msg)
    
    def save_frame_as_image(self, camera_id: str, frame: np.ndarray) -> str:
        """Save a frame as an image file and return the path"""
        try:
            if frame is None:
                return None
                
            # Create a unique filename using camera_id
            filename = f"{camera_id}.jpg"
            filepath = os.path.join(self.latest_image_dir, filename)
            
            # Save the frame as an image
            cv.imwrite(filepath, frame)
            print(f"Saved frame from camera {camera_id} to {filepath}")
            
            # Return the relative path from the project root
            rel_path = os.path.join("image", "latest", filename)
            return rel_path
            
        except Exception as e:
            print(f"Error saving frame as image for camera {camera_id}: {str(e)}")
            return None
    
    def capture_frame_async(self, camera_id: str) -> np.ndarray:
        """Capture a single frame from the camera with timeout to prevent blocking"""
        try:
            # Use the utility function to capture one frame with timeout
            frame = capture_one_frame_silent(camera_id)
            return frame
        except Exception as e:
            print(f"Error capturing frame from {camera_id}: {str(e)}")
            return None
    
    def get_latest_frame_for_camera(self, camera_id: str) -> np.ndarray:
        """Get the latest frame for a specific camera (for config page)"""
        try:
            print(f"Getting latest frame for camera {camera_id}")
            return self.capture_frame_async(camera_id)
        except Exception as e:
            print(f"Error getting latest frame for {camera_id}: {str(e)}")
            return None

class CameraManager(QObject):
    # Simplified signals - just notifications, no data passing
    data_updated = pyqtSignal(str)  # camera_id - UI should refresh from JSON
    error_occurred = pyqtSignal(str, str)  # camera_id, error_message
    camera_processed = pyqtSignal(str)  # camera_id - processing complete
    frame_ready = pyqtSignal(str, np.ndarray)  # For config page only - temporary frame display
    
    def __init__(self, camera_ids: list[str], interval: int = 5000):
        super().__init__()
        
        # Create worker thread
        self.worker_thread = QThread()
        self.worker = CameraWorker(camera_ids, interval)
        self.worker.moveToThread(self.worker_thread)
        
        # Connect worker signals to our signals (forward them)
        self.worker.data_updated.connect(self.data_updated)
        self.worker.error_occurred.connect(self.error_occurred)
        self.worker.camera_processed.connect(self.camera_processed)
        
        # Connect thread lifecycle signals properly
        self.worker_thread.started.connect(self.worker.start_timer)
        self.worker_thread.finished.connect(self.worker.stop_timer)
        
        # Start worker thread
        self.worker_thread.start()
        
        self.camera_ids = camera_ids
        self.running = False
        
        print(f"CameraManager initialized with {len(camera_ids)} cameras")
        
    def start_monitoring(self):
        """Start the camera monitoring process"""
        if not self.running:
            self.worker.running = True
            self.running = True
            # Timer is already started when thread starts, just enable processing
            print(f"Camera monitoring started for {len(self.camera_ids)} cameras")
    
    def stop_monitoring(self):
        """Stop the camera monitoring process"""
        if self.running:
            self.worker.running = False
            self.running = False
            # Don't stop timer, just disable processing
            print("Camera monitoring stopped")
    
    def set_interval(self, interval: int):
        """Set the timer interval for updates."""
        if hasattr(self.worker, 'set_interval'):
            self.worker.set_interval(interval)
        print(f"Camera monitoring interval updated to {interval}ms")

    def add_camera(self, camera_id: str, **kwargs):
        """Add a new camera to the configuration."""
        try:
            if camera_id not in self.camera_ids:
                self.camera_ids.append(camera_id)
                self.worker.camera_ids = self.camera_ids.copy()
            self.worker.config_manager.add_camera(camera_id, **kwargs)
            print(f"Camera {camera_id} added successfully.")
        except Exception as e:
            self.error_occurred.emit(camera_id, f"Failed to add camera: {str(e)}")
    
    def remove_camera(self, camera_id: str):
        """Remove a camera from monitoring"""
        if camera_id in self.camera_ids:
            self.camera_ids.remove(camera_id)
            self.worker.camera_ids = self.camera_ids.copy()
            print(f"Camera {camera_id} removed from monitoring.")
    
    def get_monitored_cameras(self) -> list[str]:
        """Get list of currently monitored camera IDs"""
        return self.camera_ids.copy()
    
    def is_monitoring(self) -> bool:
        """Check if camera monitoring is active"""
        return self.running
    
    def get_latest_frame_for_config(self, camera_id: str):
        """Get latest frame for config page - runs in separate thread to avoid UI blocking"""
        import weakref
        
        # Create weak reference to avoid object deletion issues
        weak_self = weakref.ref(self)
        
        def capture_and_emit():
            try:
                # Check if the object still exists
                strong_self = weak_self()
                if strong_self is None:
                    print("CameraManager object has been deleted, skipping frame capture")
                    return
                
                frame = strong_self.worker.get_latest_frame_for_camera(camera_id)
                if frame is not None:
                    # Check again before emitting
                    if weak_self() is not None:
                        strong_self.frame_ready.emit(camera_id, frame)
                else:
                    if weak_self() is not None:
                        strong_self.error_occurred.emit(camera_id, "Failed to capture frame for config")
            except Exception as e:
                print(f"Error in frame capture thread: {str(e)}")
                # Don't try to emit signals if object might be deleted
                strong_self = weak_self()
                if strong_self is not None:
                    try:
                        strong_self.error_occurred.emit(camera_id, f"Error getting frame for config: {str(e)}")
                    except:
                        print("Failed to emit error signal - object may be deleted")
        
        # Run in a separate thread to avoid blocking UI
        class FrameCaptureRunnable(QRunnable):
            def __init__(self, capture_func):
                super().__init__()
                self.capture_func = capture_func
            
            def run(self):
                self.capture_func()
        
        runnable = FrameCaptureRunnable(capture_and_emit)
        QThreadPool.globalInstance().start(runnable)
        
    def shutdown(self):
        """Properly shutdown the camera manager and clean up resources"""
        print("Shutting down CameraManager...")
        self.stop_monitoring()
        
        # Stop the worker thread properly
        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            # Request thread to quit
            self.worker_thread.quit()
            
            # Wait for thread to finish gracefully
            if not self.worker_thread.wait(3000):
                print("Force terminating worker thread...")
                self.worker_thread.terminate()
                self.worker_thread.wait(1000)
        
        print("CameraManager shutdown complete")
    
    def __del__(self):
        """Clean up resources when the object is destroyed"""
        self.shutdown()
