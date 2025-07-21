from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QDialog, QDialogButtonBox, QLabel, 
    QPushButton, QListWidget, QLineEdit, QSpinBox, QGroupBox,
    QFormLayout, QWidget, QSplitter, QMessageBox, QListWidgetItem
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from src.config.utils import CameraConfigManager
from datetime import datetime
from random import randint
from src.enums import CameraStatus, ParkingStatus
import os
import shutil

class ConfigPopup(QDialog):
    # Signal to notify when configuration changes are made
    configuration_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Camera Configuration")
        self.setMinimumSize(500, 300)
        self.resize(700, 500)
        
        # Initialize camera manager
        self.camera_manager = CameraConfigManager()
        
        # Track current mode and camera being edited
        self.current_mode = None  # "add" or "edit"
        self.current_camera_id = None  # ID of camera being edited, None for new
        
        # Track if changes were made during this session
        self.changes_made = False
        
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

            # Set edit mode
            self.current_mode = "edit"
            self.current_camera_id = camera_data.get('camera_id')
        else:
            self.clear_camera_form()
            self.delete_button.setEnabled(False)
            
            # Clear mode when no selection
            self.current_mode = None
            self.current_camera_id = None
            
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
        
        # Load latest configuration to get accurate camera count
        self.camera_manager.load_config()
        
        # Generate new camera ID
        cameras = self.camera_manager.get_all_cameras()
        camera_count = len(cameras) + 1
        new_id = f"CAM_{camera_count:03d}"
        
        # Ensure ID is unique
        while self.camera_manager.is_id_exists(new_id):
            camera_count += 1
            new_id = f"CAM_{camera_count:03d}"
        
        # Set default values
        self.camera_name_edit.setText(f"New Camera {camera_count}")
        self.camera_name_edit.setFocus()
        self.camera_name_edit.selectAll()
        
        # Deselect current item
        self.camera_list.setCurrentRow(-1)
        
        # Set add mode
        self.current_mode = "add"
        self.current_camera_id = new_id  # Store the new ID that will be used
        
    def delete_camera(self):
        """Delete the selected camera"""
        current_item = self.camera_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "No camera selected for deletion.")
            return
            
        camera_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not camera_data:
            QMessageBox.critical(self, "Error", "No camera data found for selected item.")
            return
            
        camera_name = camera_data.get('camera_name', 'Unknown')
        camera_id = camera_data.get('camera_id', 'Unknown')
        
        # Debug output
        print(f"DEBUG: Attempting to delete camera: {camera_name} (ID: {camera_id})")
        print(f"DEBUG: self.current_camera_id: {self.current_camera_id}")
        print(f"DEBUG: camera_data: {camera_data}")
        
        reply = QMessageBox.question(
            self, 
            "Delete Camera", 
            f"Are you sure you want to delete camera '{camera_name}' (ID: {camera_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Load latest configuration before deleting
                self.camera_manager.load_config()
                
                # Use camera_id from camera_data instead of self.current_camera_id
                print(f"DEBUG: Calling remove_camera with ID: {camera_id}, Name: {camera_name}")
                result = self.camera_manager.remove_camera(camera_id=camera_id, camera_name=camera_name)
                
                print(f"DEBUG: remove_camera returned: {result}")
                
                if result:
                    row = self.camera_list.row(current_item)
                    self.camera_list.takeItem(row)
                    self.clear_camera_form()
                    
                    # Reset mode and current camera ID
                    self.current_mode = None
                    self.current_camera_id = None
                    
                    # Mark that changes were made
                    self.changes_made = True
                    
                    # Create a message box that auto-closes
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("Success")
                    msg_box.setText(f"Camera '{camera_name}' deleted successfully.")
                    msg_box.setIcon(QMessageBox.Icon.Information)
                    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                    
                    # Auto-close after 2 seconds
                    timer = QTimer()
                    timer.timeout.connect(msg_box.accept)
                    timer.start(2000)
                    
                    msg_box.exec()
                else:
                    QMessageBox.critical(
                        self, 
                        "Error", 
                        f"Failed to delete camera '{camera_name}' (ID: {camera_id}).\n\n"
                        "The camera may not exist in the configuration file or "
                        "there was an error saving the changes."
                    )
            except Exception as e:
                print(f"DEBUG: Exception during deletion: {str(e)}")
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"An error occurred while deleting camera '{camera_name}':\n\n{str(e)}"
                )
     
    def apply_changes(self):
        """Apply changes without closing dialog"""
        try:
            if self.current_mode == "add":
                self.save_new_camera()
            elif self.current_mode == "edit":
                self.update_existing_camera()
            else:
                QMessageBox.information(
                    self, 
                    "No Changes", 
                    "No camera selected or no changes to apply."
                )
                return
                
            # Mark that changes were made
            self.changes_made = True
            
            # Reload the camera list to reflect changes
            self.load_cameras()
            
            QMessageBox.information(
                self, 
                "Success", 
                "Changes applied successfully!"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to apply changes: {str(e)}"
            )
    
    def save_new_camera(self):
        """Save a new camera to the configuration"""
        form_data = self.get_camera_form_data()
        
        # Validate required fields
        self.validate_camera_form(form_data, is_new_camera=True)
        
        # IMPORTANT: Load latest configuration first
        self.camera_manager.load_config()
        
        # Generate unique camera ID
        cameras = self.camera_manager.get_all_cameras()
        camera_count = len(cameras) + 1
        new_id = f'CAM_{camera_count:03d}'
        
        # Ensure ID is unique
        while self.camera_manager.is_id_exists(new_id):
            camera_count += 1
            new_id = f'CAM_{camera_count:03d}'

        if not new_id:
            raise ValueError("Failed to generate a unique camera ID")

        # Add required fields for new camera
        form_data['camera_id'] = new_id
        form_data['camera_status'] = CameraStatus.NOT_WORKING.value
        form_data['parking_status'] = ParkingStatus.UNKNOWN.value
        form_data['image_path'] = ""
        form_data['detection_zones'] = []
        form_data['last_maintenance'] = None
        form_data['installation_date'] = datetime.now().isoformat()
        form_data['last_updated'] = datetime.now().isoformat()
        
        # Save to configuration
        success = self.camera_manager.add_camera(form_data)
        if not success:
            raise ValueError("Failed to add camera to configuration")
        
        print(f"DEBUG: Camera saved successfully: {success}")
        
        # Mark that changes were made and emit signal immediately
        self.changes_made = True
        self.configuration_changed.emit()
        
        # Reset mode
        self.current_mode = None
        self.current_camera_id = None
        
    def update_existing_camera(self):
        """Update an existing camera in the configuration"""
        form_data = self.get_camera_form_data()
        
        # IMPORTANT: Load latest configuration first
        self.camera_manager.load_config()
        
        old_config = self.camera_manager.get_camera_by_id(self.current_camera_id)

        if not old_config:
            raise ValueError(f"Camera with ID {self.current_camera_id} not found")
        
        self.validate_camera_form(form_data, is_new_camera=False)

        print(f"DEBUG: Updating camera {self.current_camera_id} with data: {form_data}")

        # Preserve existing metadata and update form data
        form_data['camera_id'] = self.current_camera_id
        form_data['camera_status'] = old_config.get('camera_status', CameraStatus.NOT_WORKING.value)
        form_data['parking_status'] = old_config.get('parking_status', ParkingStatus.UNKNOWN.value)
        form_data['image_path'] = old_config.get('image_path', "")
        form_data['detection_zones'] = old_config.get('detection_zones', [])
        form_data['last_maintenance'] = old_config.get('last_maintenance')
        form_data['installation_date'] = old_config.get('installation_date')
        form_data['last_updated'] = datetime.now().isoformat()

        # Update the camera in the configuration directly
        cameras = self.camera_manager.get_all_cameras()
        for i, camera in enumerate(cameras):
            if camera.get('camera_id') == self.current_camera_id:
                # Replace the entire camera object
                self.camera_manager._config_data['cameras'][i] = form_data
                break
        
        # Save the configuration
        success = self.camera_manager.save_config()
        if not success:
            raise ValueError("Failed to save camera configuration")
        
        print(f"DEBUG: Camera updated successfully")

        # Mark that changes were made and emit signal immediately
        self.changes_made = True
        self.configuration_changed.emit()

        # Update the list item if camera name changed
        old_camera_name = old_config.get('camera_name', '')
        if form_data['camera_name'] != old_camera_name:
            current_item = self.camera_list.currentItem()
            if current_item:
                current_item.setText(f"{form_data['camera_name']} ({self.current_camera_id})")
                current_item.setData(Qt.ItemDataRole.UserRole, form_data)

        # Reset mode
        self.current_mode = None
        self.current_camera_id = None

    def validate_camera_form(self, form_data, is_new_camera=True):
        """Validate camera form data"""
        errors = []
        
        # Check required fields
        if not form_data['camera_name'].strip():
            errors.append("Camera name is required")
        
        if is_new_camera and not form_data['video_source'].strip():
            errors.append("Video source is required for new cameras")
        
        # Validate IP address format if provided
        if form_data['ip_address'].strip():
            import re
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, form_data['ip_address']):
                errors.append("Invalid IP address format")
        
        # Validate port range
        if not (1 <= form_data['port'] <= 65535):
            errors.append("Port must be between 1 and 65535")
        
        if errors:
            raise ValueError("\n".join(errors))
        
    def has_unsaved_changes(self):
        """Check if there are unsaved changes in the form"""
        if self.current_mode == "add":
            # Check if form has any non-default values
            form_data = self.get_camera_form_data()
            return any([
                form_data['camera_name'] != f"New Camera {len(self.camera_manager.get_all_cameras()) + 1}",
                form_data['location'].strip(),
                form_data['ip_address'].strip(),
                form_data['port'] != 8080,
                form_data['username'].strip(),
                form_data['password'].strip(),
                form_data['video_source'].strip()
            ])
        elif self.current_mode == "edit" and self.current_camera_id:
            # Compare current form data with original camera data
            current_item = self.camera_list.currentItem()
            if current_item:
                original_data = current_item.data(Qt.ItemDataRole.UserRole)
                form_data = self.get_camera_form_data()
                return any([
                    form_data['camera_name'] != original_data.get('camera_name', ''),
                    form_data['location'] != original_data.get('location', ''),
                    form_data['ip_address'] != original_data.get('ip_address', ''),
                    form_data['port'] != original_data.get('port', 8080),
                    form_data['username'] != original_data.get('username', ''),
                    form_data['password'] != original_data.get('password', ''),
                    form_data['video_source'] != original_data.get('video_source', '')
                ])
        return False
    
    def is_add_mode(self):
        """Check if currently in add mode"""
        return self.current_mode == "add"
    
    def is_edit_mode(self):
        """Check if currently in edit mode"""
        return self.current_mode == "edit"
    
    def get_current_operation(self):
        """Get a string describing the current operation"""
        if self.current_mode == "add":
            return f"Adding new camera: {self.current_camera_id}"
        elif self.current_mode == "edit":
            return f"Editing camera: {self.current_camera_id}"
        else:
            return "No operation in progress"
    
    def get_camera_form_data(self):
        """Get current form data as a dictionary"""
        return {
            'camera_name': self.camera_name_edit.text().strip(),
            'location': self.location_edit.text().strip(),
            'ip_address': self.ip_address_edit.text().strip(),
            'port': self.port_spin.value(),
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text().strip(),
            'video_source': self.video_source_edit.text().strip()
        }
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        # Emit signal if any changes were made during this session
        if self.changes_made:
            self.configuration_changed.emit()
        
        # Accept the close event
        super().closeEvent(event)