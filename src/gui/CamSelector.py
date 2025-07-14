from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QButtonGroup, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
from src.enums import CameraStatus
from src.config.utils import CameraConfigManager

class CameraToggleButton(QPushButton):
    def __init__(self, camera_name, status=CameraStatus.NOT_WORKING.value, parent=None):
        super().__init__(parent)
        self.camera_name = camera_name
        self.status = status  # "working", "error", "not_working"
        self.setCheckable(True)
        self.setFixedSize(500, 40)
        self.setText(camera_name)  # Set the button text normally
        self.setup_style()
        
    def setup_style(self):
        self.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: 500;
                color: #ffffff;
                background-color: #2a2a2a;
                border: 1px solid #666666;
                border-radius: 8px;
                padding: 8px 50px 8px 16px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #4a9eff;
            }
            QPushButton:checked {
                color: #ffffff;
                background-color: #4a9eff;
                border-color: #3a8eef;
            }
            QPushButton:checked:hover {
                background-color: #3a8eef;
            }
        """)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Only draw status circle on the right (let QPushButton handle text)
        circle_x = self.width() - 30
        circle_y = 15
        circle_radius = 6
        
        status_colors = {
            CameraStatus.WORKING.value: QColor("#00ff00"),    # Green
            CameraStatus.NOT_WORKING.value: QColor("#ff0000"),   # Red
            CameraStatus.ERROR.value: QColor("#ff9900")      # Orange
        }
        
        status_color = status_colors.get(self.status, QColor("#9E9E9E"))  # Default gray
        painter.setBrush(status_color)
        painter.setPen(QPen(status_color))
        painter.drawEllipse(circle_x, circle_y, circle_radius * 2, circle_radius * 2)
        
    def set_status(self, status):
        """Update the status and repaint the button"""
        self.status = status
        self.update()
        
    def get_camera_name(self):
        return self.camera_name

class CameraSelector(QWidget):
    camera_selected = pyqtSignal(str)  # Signal to emit when camera selection changes
    camera_changed = pyqtSignal(str)  # Signal to emit when camera is toggled

    def __init__(self, parent=None):
        super().__init__(parent)

        self.config_manager = CameraConfigManager()
        cameras = self.config_manager.get_all_cameras()

        self.cameras = [camera.get('camera_name'," ") for camera in cameras]
        self.statuses = [camera.get('camera_status', CameraStatus.ERROR.value) for camera in cameras]
        self.toggle_buttons = []
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.selected_camera = None
        self.init_ui()

    def init_ui(self):
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 20)  # Reduced top margin from 20 to 5
        layout.setSpacing(15)  # Reduced spacing from 20 to 15
        
        # Add a label for the camera selector
        label = QLabel("Select Camera To Configure")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        layout.addWidget(label)

        # Create vertical layout for toggle buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)  # Space between buttons
        
        # Create toggle buttons for each camera
        for i, camera in enumerate(self.cameras):
            status = self.statuses[i] if i < len(self.statuses) else CameraStatus.NOT_WORKING.value
            toggle_button = CameraToggleButton(camera, status)
            
            # Set the first camera as selected by default
            if i == 0:
                toggle_button.setChecked(True)
            
            # Connect signal to emit camera change
            toggle_button.toggled.connect(lambda checked, cam=camera: self.on_camera_changed(checked, cam))
            
            self.toggle_buttons.append(toggle_button)
            self.button_group.addButton(toggle_button)
            buttons_layout.addWidget(toggle_button)
        # Center the buttons
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        layout.addLayout(buttons_layout)
        layout.addStretch()  # Add stretch to push content to the top

        config_button = QPushButton("Config Selected Camera!")
        config_button.setFixedSize(250, 50)
        config_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                background-color: #4a9eff;
                border: 1px solid #666666;
                border-radius: 12px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background-color: #3a8eef;
            }
            QPushButton:pressed {
                background-color: #2a7edf;
            }
        """)

        config_button.clicked.connect(self.on_config_button_clicked)
        layout.addWidget(config_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def on_camera_changed(self, checked, camera):
        """Handle camera selection change"""
        if checked:
            self.camera_changed.emit(camera)

    def get_selected_camera(self):
        """Get the currently selected camera"""
        for toggle_button in self.toggle_buttons:
            if toggle_button.isChecked():
                return toggle_button.get_camera_name()
        return None

    def set_selected_camera(self, camera_name):
        """Programmatically select a camera"""
        for toggle_button in self.toggle_buttons:
            if toggle_button.get_camera_name() == camera_name:
                toggle_button.setChecked(True)
                break

    def update_camera_status(self, camera_name, status):
        """Update the status of a specific camera"""
        for toggle_button in self.toggle_buttons:
            if toggle_button.get_camera_name() == camera_name:
                toggle_button.set_status(status)
                break

    def get_all_camera_statuses(self):
        """Get all camera statuses as a dictionary"""
        statuses = {}
        for toggle_button in self.toggle_buttons:
            statuses[toggle_button.get_camera_name()] = toggle_button.status
        return statuses
    
    def set_status_camera(self, camera_name, status):
        """Set the status of a specific camera"""
        for toggle_button in self.toggle_buttons:
            if toggle_button.get_camera_name() == camera_name:
                toggle_button.set_status(status)
                break

    def on_config_button_clicked(self):
        """Handle the configuration button click"""
        self.selected_camera = self.get_selected_camera()
        if self.selected_camera:
            # Emit signal or handle configuration logic here
            self.camera_selected.emit(self.selected_camera)
        else:
            QMessageBox.warning(self, "No Camera Selected", "Please select a camera to configure.")
        