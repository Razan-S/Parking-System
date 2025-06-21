from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QWidget, QStackedLayout, QVBoxLayout, QLabel, QPushButton, QMessageBox
from src.gui.CamSelector import CameraSelector
from src.gui.segmentor import RoadSegmenterGUI

class Window(QMainWindow):
    def __init__(self, cameras=None):
        super().__init__()

        if cameras is None or len(cameras) == 0:
            QMessageBox.warning(self, "No cameras available.", "Please check your camera configuration.")
            self.camera_names = ["No Cameras Available"]
            self.camera_statuses = ["offline"]
        else:
            self.camera_names = [camera['name'] for camera in cameras]
            self.camera_statuses = [camera['status'] for camera in cameras]

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Illegal Parking Monitoring")
        self.setGeometry(0, 0, 300, 300)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
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
        self.config_page = RoadSegmenterGUI(video_path="video/test.MP4")

        self.dashboard.switch_to_config_page.connect(self.show_config_page)
        self.config_page.switch_to_dashboard_page.connect(self.show_dashboard)
        
        # Set up config page (example content)
        config_layout = QVBoxLayout(self.config_page)
        config_layout.setContentsMargins(20, 20, 20, 20)
        config_label = QLabel("Configuration Content")
        config_label.setStyleSheet("font-size: 18px; color: #333333;")
        config_layout.addWidget(config_label)
        
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
    
    def show_config_page(self):
        """Switch to config page"""
        self.stack_widget.setCurrentWidget(self.config_page)

class Dashboard(QWidget):
    switch_to_config_page = pyqtSignal(str)

    def __init__(self, cameras_name=None, camera_statuses=None):
        super().__init__()
        self.camera_names = cameras_name if cameras_name else []
        self.camera_statuses = camera_statuses if camera_statuses else []

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Dashboard")
        self.setGeometry(0, 0, 1400, 800)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.button_selected = self.camera_names[0] if self.camera_names else None

        self.camera_selector_ui()

    def camera_selector_ui(self):
        # Create a container widget for the camera selector content
        container_widget = QWidget()
        layout = QVBoxLayout(container_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Add camera selector widget
        widget = CameraSelector(self.camera_names, self.camera_statuses)
        layout.addWidget(widget)
        
        # Create a centered button container
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 10)
        
        config_button = QPushButton("Config This Camera!")
        config_button.setFixedSize(200, 40)
        config_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                background-color: #007ACC;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        config_button.clicked.connect(self.change_to_config_page)
        
        # Center the button
        button_layout.addWidget(config_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(button_container)
        
        # Add stretch to push everything up but keep button visible
        layout.addStretch()

        # Connect the signal to handle camera changes
        widget.camera_changed.connect(self.on_camera_selection_changed)

        self.main_layout.addWidget(container_widget)
    
    def on_camera_selection_changed(self, camera_name):
        """Handle when user selects a different camera"""
        print(f"DASHBOARD: Selected camera: {camera_name}")
        # Here you can add logic to switch camera feeds, update UI, etc.
        self.button_selected = camera_name

    def get_selected_camera(self):
        """Get the currently selected camera name"""
        return self.button_selected
    
    def change_to_config_page(self):
        """Switch to the configuration page"""
        selected_camera = self.get_selected_camera()
        print(f"Changing to config page... {selected_camera}")
        if selected_camera:
            self.switch_to_config_page.emit(selected_camera)
        else:
            QMessageBox.warning(self, "No Camera Selected", "Please select a camera before configuring.")
            print("No camera selected.")
