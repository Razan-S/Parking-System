from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QDialog, QDialogButtonBox, QLabel, 
    QPushButton, QListWidget, QLineEdit, QSpinBox, QGroupBox,
    QFormLayout, QWidget, QSplitter, QMessageBox, QListWidgetItem
)
from PyQt6.QtCore import QTimer, Qt
from src.config.utils import CameraConfigManager

class ConfigPopup(QDialog):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Camera Configuration")
        self.setMinimumSize(500, 300)
        self.resize(700, 500)
        
        # Initialize camera manager
        self.camera_manager = CameraConfigManager()
        
        # Setup UI
        self.setup_ui()
        self.load_cameras()
        
    def setup_ui(self):
        """Setup the main UI layout"""
        main_layout = QVBoxLayout()
        
        # Create splitter for left panel (camera list) and right panel (camera details)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Camera list
        left_panel = self.create_camera_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Camera configuration
        right_panel = self.create_camera_config_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)  # Camera list takes 1/3
        splitter.setStretchFactor(1, 2)  # Camera config takes 2/3
        
        main_layout.addWidget(splitter)
        
        # Dialog buttons
        QBtn = (
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_changes)
        
        main_layout.addWidget(self.buttonBox)
        self.setLayout(main_layout)
        
    def create_camera_list_panel(self):
        """Create the left panel with camera list and controls"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Cameras")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Camera list
        self.camera_list = QListWidget()
        self.camera_list.itemSelectionChanged.connect(self.on_camera_selected)
        layout.addWidget(self.camera_list)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        self.add_button = QPushButton("Add Camera")
        self.add_button.clicked.connect(self.add_camera)
        button_layout.addWidget(self.add_button)
        
        self.delete_button = QPushButton("Delete Camera")
        self.delete_button.clicked.connect(self.delete_camera)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        self.duplicate_button = QPushButton("Duplicate Camera")
        self.duplicate_button.clicked.connect(self.duplicate_camera)
        self.duplicate_button.setEnabled(False)
        button_layout.addWidget(self.duplicate_button)
        
        layout.addLayout(button_layout)
        panel.setLayout(layout)
        return panel
        
    def create_camera_config_panel(self):
        """Create the right panel with camera configuration form"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Camera Configuration")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Configuration form
        config_group = QGroupBox("Camera Properties")
        form_layout = QFormLayout()
        
        # Camera Name
        self.camera_name_edit = QLineEdit()
        self.camera_name_edit.setPlaceholderText("Enter camera name")
        form_layout.addRow("Camera Name:", self.camera_name_edit)
        
        # Location
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Enter camera location")
        form_layout.addRow("Location:", self.location_edit)
        
        # IP Address
        self.ip_address_edit = QLineEdit()
        self.ip_address_edit.setPlaceholderText("192.168.1.100")
        form_layout.addRow("IP Address:", self.ip_address_edit)
        
        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(8080)
        form_layout.addRow("Port:", self.port_spin)
        
        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        form_layout.addRow("Username:", self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        form_layout.addRow("Password:", self.password_edit)
        
        # Video Source
        self.video_source_edit = QLineEdit()
        self.video_source_edit.setPlaceholderText("rtsp://... or 0 for webcam")
        form_layout.addRow("Video Source:", self.video_source_edit)
        
        config_group.setLayout(form_layout)
        layout.addWidget(config_group)
        
        # Connection test button
        test_layout = QHBoxLayout()
        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_connection)
        self.test_connection_button.setEnabled(False)
        test_layout.addWidget(self.test_connection_button)
        test_layout.addStretch()
        layout.addLayout(test_layout)
        
        # Spacer
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
        
    def load_cameras(self):
        """Load cameras from configuration into the list"""
        self.camera_list.clear()
        
        try:
            cameras = self.camera_manager.get_all_cameras()
            for camera in cameras:
                camera_id = camera.get('camera_id', 'Unknown')
                camera_name = camera.get('camera_name', 'Unnamed Camera')
                
                item = QListWidgetItem(f"{camera_name} ({camera_id})")
                item.setData(Qt.ItemDataRole.UserRole, camera)
                self.camera_list.addItem(item)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load cameras: {str(e)}")
            
    def on_camera_selected(self):
        """Handle camera selection in the list"""
        current_item = self.camera_list.currentItem()
        
        if current_item:
            camera_data = current_item.data(Qt.ItemDataRole.UserRole)
            self.populate_camera_form(camera_data)
            self.delete_button.setEnabled(True)
            self.duplicate_button.setEnabled(True)
            self.test_connection_button.setEnabled(True)
        else:
            self.clear_camera_form()
            self.delete_button.setEnabled(False)
            self.duplicate_button.setEnabled(False)
            self.test_connection_button.setEnabled(False)
            
    def populate_camera_form(self, camera_data):
        """Populate the form with camera data"""
        if not camera_data:
            return
            
        self.camera_name_edit.setText(camera_data.get('camera_name', ''))
        self.location_edit.setText(camera_data.get('location', ''))
        self.ip_address_edit.setText(camera_data.get('ip_address', ''))
        self.port_spin.setValue(camera_data.get('port', 8080))
        self.username_edit.setText(camera_data.get('username', ''))
        self.password_edit.setText(camera_data.get('password', ''))
        self.video_source_edit.setText(camera_data.get('video_source', ''))
        
    def clear_camera_form(self):
        """Clear all form fields"""
        self.camera_name_edit.clear()
        self.location_edit.clear()
        self.ip_address_edit.clear()
        self.port_spin.setValue(8080)
        self.username_edit.clear()
        self.password_edit.clear()
        self.video_source_edit.clear()
        
    def add_camera(self):
        """Add a new camera"""
        # Clear form for new camera
        self.clear_camera_form()
        
        # Generate new camera ID
        cameras = self.camera_manager.get_all_cameras()
        camera_count = len(cameras) + 1
        new_id = f"CAM_{camera_count:03d}"
        
        # Set default values
        self.camera_name_edit.setText(f"New Camera {camera_count}")
        self.camera_name_edit.setFocus()
        self.camera_name_edit.selectAll()
        
        # Deselect current item
        self.camera_list.setCurrentRow(-1)
        
    def delete_camera(self):
        """Delete the selected camera"""
        current_item = self.camera_list.currentItem()
        if not current_item:
            return
            
        camera_data = current_item.data(Qt.ItemDataRole.UserRole)
        camera_name = camera_data.get('camera_name', 'Unknown')
        
        reply = QMessageBox.question(
            self, 
            "Delete Camera", 
            f"Are you sure you want to delete camera '{camera_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from list (actual deletion will be handled when applying changes)
            row = self.camera_list.row(current_item)
            self.camera_list.takeItem(row)
            self.clear_camera_form()
            
    def duplicate_camera(self):
        """Duplicate the selected camera"""
        current_item = self.camera_list.currentItem()
        if not current_item:
            return
            
        camera_data = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Generate new camera ID
        cameras = self.camera_manager.get_all_cameras()
        camera_count = len(cameras) + 1
        new_id = f"CAM_{camera_count:03d}"
        
        # Create new camera data
        new_camera_data = camera_data.copy()
        new_camera_data['camera_id'] = new_id
        new_camera_data['camera_name'] = f"{camera_data.get('camera_name', 'Camera')} (Copy)"
        
        # Add to list
        item = QListWidgetItem(f"{new_camera_data['camera_name']} ({new_id})")
        item.setData(Qt.ItemDataRole.UserRole, new_camera_data)
        self.camera_list.addItem(item)
        
        # Select the new item
        self.camera_list.setCurrentItem(item)
        
    def test_connection(self):
        """Test camera connection (placeholder function)"""
        ip_address = self.ip_address_edit.text()
        port = self.port_spin.value()
        
        if not ip_address:
            QMessageBox.warning(self, "Warning", "Please enter an IP address to test.")
            return
            
        # Placeholder for actual connection test
        QMessageBox.information(
            self, 
            "Connection Test", 
            f"Connection test for {ip_address}:{port}\n\n"
            "Note: This is a placeholder. Actual connection testing "
            "functionality will be implemented later."
        )
        
    def apply_changes(self):
        """Apply changes without closing dialog"""
        # Placeholder for saving changes
        QMessageBox.information(
            self, 
            "Apply Changes", 
            "Changes applied successfully!\n\n"
            "Note: This is a placeholder. Actual save functionality "
            "will be implemented later."
        )
        
    def get_camera_form_data(self):
        """Get current form data as a dictionary"""
        return {
            'camera_name': self.camera_name_edit.text(),
            'location': self.location_edit.text(),
            'ip_address': self.ip_address_edit.text(),
            'port': self.port_spin.value(),
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'video_source': self.video_source_edit.text()
        }