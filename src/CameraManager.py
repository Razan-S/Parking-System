from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, QRunnable, QThreadPool, pyqtSlot
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

class CameraFetchingWorkerSignals(QObject):
    """Defines the signals available from a running camera worker thread."""
    finished = pyqtSignal(str, object)  # camera_id, result

class CameraFetchingWorker(QRunnable):
    """Worker for processing a single camera"""

    def __init__(self, fn, camera_id):
        super().__init__()
        self.fn = fn
        self.camera_id = camera_id
        self.signals = CameraFetchingWorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(self.camera_id)
            # Check if signals object still exists before emitting
            if hasattr(self, 'signals') and self.signals is not None:
                try:
                    self.signals.finished.emit(self.camera_id, result)
                except RuntimeError as e:
                    if "has been deleted" in str(e):
                        print(f"Signals object deleted during emission for camera {self.camera_id}")
                    else:
                        print(f"Signal emission error for camera {self.camera_id}: {e}")
        except Exception as e:
            print(f"Worker thread error for camera {self.camera_id}: {str(e)}")
            # Only print traceback if it's not a shutdown-related error
            if "has been deleted" not in str(e):
                traceback.print_exc()
            
            # Try to emit finished signal with None result
            if hasattr(self, 'signals') and self.signals is not None:
                try:
                    self.signals.finished.emit(self.camera_id, None)
                except RuntimeError as signal_error:
                    if "has been deleted" in str(signal_error):
                        print(f"Signals object deleted during error emission for camera {self.camera_id}")
                    else:
                        print(f"Error signal emission failed for camera {self.camera_id}: {signal_error}")

class CameraWorker(QObject):
    """Worker class that will be moved to a separate thread"""
    # Simplified signals - no data passing, just notifications
    data_updated = pyqtSignal(str)  # camera_id - signals UI to refresh from JSON
    error_occurred = pyqtSignal(str, str)  # camera_id, error_message
    camera_processed = pyqtSignal(str)  # camera_id - processing complete notification
    
    def __init__(self, camera_ids: list[str], interval: int = 5000, use_gpu: bool = False):
        super().__init__()
        self.config_manager = CameraConfigManager()
        self.camera_ids = camera_ids
        self.active_workers = 0  # Track active workers
        self.detection_module = DetectionModule(use_gpu=use_gpu)
        self.running = False
        self.is_fetching = False # Flag to prevent overlapping fetches
        self.latest_image_dir = os.path.join(os.path.abspath(os.curdir), "image", "latest")
        self.interval = interval
        self.timer = None  # Will be created in the worker thread

        self.threadpool = QThreadPool()
        
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
    
    def force_stop_workers(self):
        """Force stop all active workers in the thread pool"""
        print("Force stopping all active workers...")
        self.running = False
        self.is_fetching = False
        self.active_workers = 0
        
        if hasattr(self, 'threadpool'):
            # Clear all pending tasks immediately
            self.threadpool.clear()
            print("Cleared pending thread pool tasks")
            
            # Try to wait for active threads briefly
            active_count = self.threadpool.activeThreadCount()
            if active_count > 0:
                print(f"Waiting briefly for {active_count} active workers...")
                if not self.threadpool.waitForDone(500):  # Only wait 0.5 seconds
                    remaining = self.threadpool.activeThreadCount()
                    print(f"Force stopping {remaining} workers that didn't finish")
                # Note: QThreadPool doesn't have a force terminate method for individual workers
                # but setting self.running = False will cause them to exit gracefully
    
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
        
        if self.is_fetching:
            print("Already fetching, skipping this cycle")
            return
        
        self.is_fetching = True
        
        # Reload camera list from JSON configuration to pick up new cameras
        try:
            config = self.config_manager.load_config()
            current_camera_ids = [camera.get('camera_id') for camera in config.get('cameras', []) if camera.get('camera_id')]
            self.camera_ids = current_camera_ids
            print(f"Reloaded {len(current_camera_ids)} cameras from configuration")
        except Exception as e:
            print(f"Error reloading camera configuration: {e}")
            # Fall back to existing camera_ids if reload fails
        
        # Double-check we're still running after config reload
        if not self.running:
            self.is_fetching = False
            return
        
        self.active_workers = len(self.camera_ids)
        
        print("Starting parallel camera processing...")
        for camera_id in self.camera_ids:
            if not self.running:
                # If we stopped running during the loop, reduce active workers count
                self.active_workers = 0
                self.is_fetching = False
                break
            
            # Create worker for each camera
            worker = CameraFetchingWorker(self.process_single_camera, camera_id)
            worker.signals.finished.connect(self.handle_worker_finished)
            self.threadpool.start(worker)

    def handle_worker_finished(self, camera_id: str, result: object):
        """Handle worker finished signal"""
        if result is None:
            print(f"Worker for camera {camera_id} failed")
            # Don't emit error here, let process_single_camera handle it
        
        self.active_workers -= 1
        if self.active_workers <= 0:
            self.is_fetching = False
            print("All workers finished fetching")
            
        # If we're not running anymore, reset the counter to prevent hanging
        if not self.running:
            self.active_workers = 0
            self.is_fetching = False
    
    def process_single_camera(self, camera_id: str):
        """Process a single camera - capture frame, detect, save to JSON, and notify UI"""
        try:
            # Check if we're still running before processing
            if not self.running:
                print(f"Camera worker shutting down, skipping processing for {camera_id}")
                return
            
            # Get camera configuration
            camera_config = self.config_manager.get_camera_by_id(camera_id)
            if not camera_config:
                if self.running:  # Only emit if still running
                    self.error_occurred.emit(camera_id, f"Camera configuration not found for {camera_id}")
                return
            
            # Capture frame (non-blocking)
            frame = self.get_latest_frame_for_camera(camera_id)
            if frame is None:
                if self.running:  # Only emit if still running
                    self.error_occurred.emit(camera_id, f"Failed to capture frame from {camera_id}")
                return
            
            # Check again if we're still running after frame capture (which can take time)
            if not self.running:
                print(f"Camera worker shutting down during processing for {camera_id}")
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
            
            # Only emit signals if we're still running and object exists
            if self.running:
                try:
                    # Notify UI to refresh data from JSON (no data passing)
                    self.data_updated.emit(camera_id)
                    self.camera_processed.emit(camera_id)
                except RuntimeError as e:
                    if "has been deleted" in str(e):
                        print(f"Worker object deleted during signal emission for {camera_id}")
                    else:
                        raise
                
        except Exception as e:
            # Only handle errors if we're still running
            if self.running:
                error_msg = f"Error processing camera {camera_id}: {str(e)}"
                print(error_msg)
                print(traceback.format_exc())
                
                # Update camera status to error in JSON
                try:
                    self.config_manager.update_camera_status_legacy(camera_id, CameraStatus.ERROR.value)
                    if self.running:  # Double check before emitting
                        try:
                            self.data_updated.emit(camera_id)  # Notify UI even on error
                        except RuntimeError as signal_error:
                            if "has been deleted" in str(signal_error):
                                print(f"Worker object deleted during error signal emission for {camera_id}")
                            else:
                                print(f"Signal error: {signal_error}")
                except Exception as config_error:
                    print(f"Failed to update camera status to error: {config_error}")
                    
                # Try to emit error signal if object still exists
                try:
                    if self.running:
                        self.error_occurred.emit(camera_id, error_msg)
                except RuntimeError as signal_error:
                    if "has been deleted" in str(signal_error):
                        print(f"Worker object deleted during error signal emission for {camera_id}")
                    else:
                        print(f"Error signal emission failed: {signal_error}")
            else:
                print(f"Camera worker shutting down, ignoring error for {camera_id}: {str(e)}")
    
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

    def get_latest_frame_for_camera(self, camera_id: str) -> np.ndarray:
        """Get the latest frame for a specific camera (for config page)"""
        try:
            print(f"Getting latest frame for camera {camera_id}")
            frame = capture_one_frame_silent(camera_id)
            return frame
        except Exception as e:
            print(f"Error getting latest frame for {camera_id}: {str(e)}")
            return None

class CameraManager(QObject):
    # Simplified signals - just notifications, no data passing
    data_updated = pyqtSignal(str)  # camera_id - UI should refresh from JSON
    error_occurred = pyqtSignal(str, str)  # camera_id, error_message
    camera_processed = pyqtSignal(str)  # camera_id - processing complete
    frame_ready = pyqtSignal(str, np.ndarray)  # For config page only - temporary frame display
    
    def __init__(self, camera_ids: list[str], interval: int = 5000, use_gpu: bool = False):
        super().__init__()
        
        # Create worker thread
        self.worker_thread = QThread()
        self.worker = CameraWorker(camera_ids, interval, use_gpu)
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
            # First add to config manager (saves to JSON)
            self.worker.config_manager.add_camera(camera_id, **kwargs)
            
            # Update local camera list
            if camera_id not in self.camera_ids:
                self.camera_ids.append(camera_id)
            
            # Force worker to reload camera list from JSON to ensure consistency
            try:
                config = self.worker.config_manager.load_config()
                worker_camera_ids = [camera.get('camera_id') for camera in config.get('cameras', []) if camera.get('camera_id')]
                self.worker.camera_ids = worker_camera_ids
                print(f"Worker camera list updated: {worker_camera_ids}")
            except Exception as e:
                print(f"Error updating worker camera list: {e}")
                # Fallback to manual update
                self.worker.camera_ids = self.camera_ids.copy()
            
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
                # Check if the object still exists and is still running
                strong_self = weak_self()
                if strong_self is None or not strong_self.running:
                    print("CameraManager object deleted or stopped, skipping frame capture")
                    return
                
                frame = strong_self.worker.get_latest_frame_for_camera(camera_id)
                if frame is not None:
                    # Check again before emitting
                    strong_self_check = weak_self()
                    if strong_self_check is not None and strong_self_check.running:
                        try:
                            strong_self_check.frame_ready.emit(camera_id, frame)
                        except RuntimeError as e:
                            if "has been deleted" in str(e):
                                print(f"CameraManager deleted during frame emission for {camera_id}")
                else:
                    strong_self_check = weak_self()
                    if strong_self_check is not None and strong_self_check.running:
                        try:
                            strong_self_check.error_occurred.emit(camera_id, "Failed to capture frame for config")
                        except RuntimeError as e:
                            if "has been deleted" in str(e):
                                print(f"CameraManager deleted during error emission for {camera_id}")
            except Exception as e:
                print(f"Error in frame capture thread: {str(e)}")
                # Don't try to emit signals if object might be deleted
                strong_self = weak_self()
                if strong_self is not None and strong_self.running:
                    try:
                        strong_self.error_occurred.emit(camera_id, f"Error getting frame for config: {str(e)}")
                    except RuntimeError as signal_error:
                        if "has been deleted" in str(signal_error):
                            print("CameraManager deleted during error signal emission")
        
        # Only start the thread if we're still running
        if self.running:
            # Run in a separate thread to avoid blocking UI
            class FrameCaptureRunnable(QRunnable):
                def __init__(self, capture_func):
                    super().__init__()
                    self.capture_func = capture_func
                
                def run(self):
                    self.capture_func()
            
            runnable = FrameCaptureRunnable(capture_and_emit)
            QThreadPool.globalInstance().start(runnable)
        else:
            print(f"CameraManager not running, skipping frame capture for {camera_id}")
        
    def shutdown(self):
        """Properly shutdown the camera manager and clean up resources"""
        print("Shutting down CameraManager...")
        self.stop_monitoring()
        
        # Force stop all active workers first
        if hasattr(self, 'worker'):
            self.worker.force_stop_workers()
        
        # Stop the thread pool workers with shorter timeout
        if hasattr(self, 'worker') and hasattr(self.worker, 'threadpool'):
            print("Stopping thread pool workers...")
            self.worker.threadpool.clear()  # Clear pending tasks
            
            # Check if there are any active threads first
            active_count = self.worker.threadpool.activeThreadCount()
            if active_count > 0:
                print(f"Waiting for {active_count} active thread pool workers to finish...")
                # Only wait 1 second for thread pool workers
                if not self.worker.threadpool.waitForDone(1000):
                    remaining = self.worker.threadpool.activeThreadCount()
                    print(f"Force terminating {remaining} remaining thread pool workers")
                else:
                    print("All thread pool workers finished")
            else:
                print("No active thread pool workers to wait for")
        
        # Stop the worker thread with shorter timeout
        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            print("Stopping main worker thread...")
            # Request thread to quit
            self.worker_thread.quit()
            
            # Wait only 1.5 seconds for graceful shutdown
            if not self.worker_thread.wait(1500):
                print("Force terminating worker thread...")
                self.worker_thread.terminate()
                self.worker_thread.wait(500)  # Only wait 0.5 seconds for termination
        
        print("CameraManager shutdown complete")
    
    def __del__(self):
        """Clean up resources when the object is destroyed"""
        self.shutdown()
