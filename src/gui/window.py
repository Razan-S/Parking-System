from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QWidget, QStackedLayout, QVBoxLayout, QLabel, QMessageBox
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