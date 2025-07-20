from PyQt6.QtCore import Qt, QThreadPool, QTimer
from PyQt6.QtWidgets import QMainWindow, QWidget, QStackedLayout, QVBoxLayout, QLabel, QMessageBox, QApplication
from src.gui.segmentor import RoadSegmenterGUI
from src.gui.Dashboard import Dashboard
from src.config.utils import CameraConfigManager
import os

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize camera config manager
        self.config_manager = CameraConfigManager()

            # Load from JSON configuration
        cameras_from_config = self.config_manager.get_all_cameras()
        if not cameras_from_config:
            QMessageBox.warning(self, "No cameras available.", "Please check your camera configuration.")
            self.camera_names = ["No Cameras Available"]
            self.camera_statuses = ["not_working"]
        else:
            self.camera_names = self.config_manager.get_camera_names()
            self.camera_statuses = self.config_manager.get_camera_statuses()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Illegal Parking Monitoring")
        self.setGeometry(0, 0, 300, 300)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
        """)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout (no margins to make header full width)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create fixed header
        self.create_header(main_layout)
        
        # Create content area for pages
        self.create_content_area(main_layout)

    def create_header(self, main_layout):
        """Create the fixed header at the top of the window"""
        header_label = QLabel("Illegal Parking Monitoring")
        header_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_label.setStyleSheet("""
            QLabel {
                font-size: 24px; 
                font-weight: bold; 
                color: #ffffff;
                background-color: #000000;
                border-bottom: 1px solid #666666;
            }
        """)
        header_label.setFixedHeight(50)
        header_label.setContentsMargins(20, 0, 20, 0)
        
        # Add header to layout
        main_layout.addWidget(header_label)

    def create_content_area(self, main_layout):
        """Create the content area where different pages can be displayed"""
        # Create pages
        self.dashboard = Dashboard(cameras_name=self.camera_names, camera_statuses=self.camera_statuses)
        self.config_page = RoadSegmenterGUI()

        self.dashboard.switch_to_config_page.connect(lambda camera: self.show_config_page(camera=camera))
        self.config_page.switch_to_dashboard_page.connect(self.show_dashboard)
        
        # Pass camera manager to config page so it can get frames
        self.config_page.set_camera_manager(self.dashboard.camera_manager)
        
        # Create stacked widget for page switching
        self.stack_widget = QStackedLayout()
        self.stack_widget.addWidget(self.dashboard)
        self.stack_widget.addWidget(self.config_page)
        
        # Create container widget for the stacked layout
        content_container = QWidget()
        content_container.setLayout(self.stack_widget)
        
        # Add content area to main layout
        main_layout.addWidget(content_container)

    def show_dashboard(self):
        """Switch to dashboard page"""
        self.stack_widget.setCurrentWidget(self.dashboard)
    
    def show_config_page(self, camera=None):
        """Switch to config page"""
        if camera is None:
            QMessageBox.warning(self, "No camera selected", "Please select a camera to configure.")
            return
    
        # camera = self.config_manager.get_camera_by_name(cam_name)
        if camera.get("camera_id") is None:
            cam_name = camera.get("camera_name", "Unknown")
            QMessageBox.warning(self, "Invalid camera", f"Camera {cam_name} does not have a valid camera_id.")
            return

        self.config_page.set_camera(camera.get("camera_id"))
        self.stack_widget.setCurrentWidget(self.config_page)

    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(self, 'Exit', 'Are you sure you want to exit?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Accept the close event immediately to close the window
            event.accept()
            
            # Use QTimer to defer cleanup so window closes immediately
            QTimer.singleShot(100, self.shutdown_threads_deferred)
            
        else:
            event.ignore()
    
    def shutdown_threads_deferred(self):
        """Shutdown threads after the window has closed"""
        try:
            self.shutdown_threads()
        except Exception as e:
            print(f"Error during deferred shutdown: {e}")
        finally:
            # Force quit the application after cleanup
            QApplication.instance().quit()
    
    def shutdown_threads(self):
        """Shutdown all threads and clean up resources"""
        print("Shutting down application threads...")
        
        try:
            # Shutdown dashboard camera manager threads first
            if hasattr(self, 'dashboard') and hasattr(self.dashboard, 'camera_manager'):
                print("Shutting down camera manager...")
                self.dashboard.camera_manager.shutdown()
        except Exception as e:
            print(f"Error shutting down camera manager: {e}")
        
        try:
            # Clean up dashboard resources
            if hasattr(self, 'dashboard'):
                print("Cleaning up dashboard...")
                self.dashboard.cleanup()
        except Exception as e:
            print(f"Error cleaning up dashboard: {e}")
        
        try:
            # Clean up config page resources if it has any
            if hasattr(self, 'config_page') and hasattr(self.config_page, 'cleanup'):
                print("Cleaning up config page...")
                self.config_page.cleanup()
        except Exception as e:
            print(f"Error cleaning up config page: {e}")
        
        # Check for any remaining threads with shorter timeout
        try:
            thread_pool = QThreadPool.globalInstance()
            active_count = thread_pool.activeThreadCount()
            if active_count > 0:
                print(f"Waiting for {active_count} remaining global threads...")
                # Clear any remaining tasks
                thread_pool.clear()
                # Only wait 2 seconds for global thread pool
                if not thread_pool.waitForDone(2000):
                    remaining = thread_pool.activeThreadCount()
                    print(f"Warning: {remaining} threads still active after timeout")
                else:
                    print("All threads successfully terminated")
            else:
                print("No remaining global threads to clean up")
        except Exception as e:
            print(f"Error during thread pool cleanup: {e}")
        
        print("Thread shutdown complete")

            