from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QHBoxLayout, QPushButton, QDialog, QDialog
from src.gui.CamSelector import CameraSelector
from src.gui.CamCard import CamCardFrame
from src.gui.ConfigPopup import ConfigPopup
from src.config.utils import CameraConfigManager
from src.CameraManager import CameraManager
from src.enums import CameraStatus, ParkingStatus
import os

class Dashboard(QWidget):
    switch_to_config_page = pyqtSignal(dict)

    def __init__(self, cameras_name=None, camera_statuses=None, use_gpu=False):
        super().__init__()
        
        # Initialize camera config manager
        self.config_manager = CameraConfigManager()
        
        # Load camera data from JSON configuration
        if cameras_name is None or camera_statuses is None:
            self.camera_names = self.config_manager.get_camera_names()
            self.camera_statuses = self.config_manager.get_camera_statuses()
        else:
            self.camera_names = cameras_name
            self.camera_statuses = camera_statuses
            
        self.selected_camera = self.camera_names[0] if self.camera_names else None

        # Initialize camera manager - it will get camera IDs from config automatically
        self.camera_manager = CameraManager(use_gpu=use_gpu)
        
        # Connect camera manager signals - new simplified signals
        self.camera_manager.data_updated.connect(self.on_data_updated)
        self.camera_manager.error_occurred.connect(self.on_camera_error)
        self.camera_manager.camera_processed.connect(self.on_camera_processed)
        
        # Start monitoring
        self.camera_manager.start_monitoring()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Dashboard")
        self.setGeometry(0, 0, 1400, 800)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
            }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(5)  # Add spacing between components

        # Create both camera selector and camera cards
        self.setup_dashboard_ui()

    def setup_dashboard_ui(self):
        """Setup the complete dashboard UI with both camera selector and cards"""
        
        # Add the camera selector
        self.add_camera_selector()
        # Add the camera cards below
        self.add_camera_cards()
        # Add config button as overlay (last so it's on top)
        self.add_config_button()

    def add_config_button(self):
        """Add the configuration button as an overlay at the top right"""
        # Create config button with absolute positioning
        self.config_button = QPushButton("⚙️", self)
        self.config_button.setToolTip("Configure Cameras")
        self.config_button.clicked.connect(self.show_config_popup)
        self.config_button.setFixedSize(30, 30)  # Small square button
        self.config_button.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #5a5a5a;
                border-radius: 15px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #6a6a6a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        
        # Position the button at top right corner
        self.config_button.move(self.width() - 50, 20)  # 50px from right, 20px from top
        self.config_button.raise_()  # Bring to front

    def resizeEvent(self, event):
        """Handle window resize to reposition the config button"""
        super().resizeEvent(event)
        if hasattr(self, 'config_button'):
            # Reposition the button at top right corner
            self.config_button.move(self.width() - 50, 20)

    def add_camera_selector(self):
        """Add the camera selector widget"""
        # Create camera selector
        self.camera_selector = CameraSelector()
        self.camera_selector.camera_selected.connect(lambda: self.change_to_config_page(self.camera_selector.get_selected_camera()))
        self.camera_selector.camera_changed.connect(self.on_camera_selection_changed)
        
        # Add to layout
        self.main_layout.addWidget(self.camera_selector)

    def add_camera_cards(self):
        """Add camera cards in a grid layout"""
        # Get camera data from JSON configuration
        self.config_manager.load_config()
        cameras_data = self.config_manager.get_cameras_for_ui()
          # Ensure image paths are absolute
        ROOT_DIR = os.path.abspath(os.curdir)
        for camera in cameras_data:
            if camera.get('image') and not os.path.isabs(camera['image']):
                camera['image'] = os.path.join(ROOT_DIR, camera['image'])

        cameras_card = CamCardFrame()
        cameras_card.card_clicked.connect(lambda cam_id: self.handle_camera_card_click(cam_id))
        # Add with stretch factor to make the camera cards area take more space
        self.main_layout.addWidget(cameras_card, 2)

    def handle_camera_card_click(self, camera_id):
        """Handle camera card click by finding the camera name and updating selector"""
        self.config_manager.load_config()
        camera = self.config_manager.get_camera_by_id(camera_id)
        if camera:
            camera_name = camera.get('camera_name')
            if camera_name:
                self.camera_selector.set_selected_camera(camera_name)
        else:
            print(f"Camera with ID {camera_id} not found")

    def refresh_card_selection(self):
        """Refresh the visual selection of camera cards"""
        # This would ideally update the card styling
        # For now, we'll just store the selection
        print(f"Selected camera updated to: {self.selected_camera}")
    
    def on_camera_selection_changed(self, camera_name):
        """Handle when user selects a different camera (legacy method)"""
        print(f"DASHBOARD: Selected camera: {camera_name}")
        self.selected_camera = camera_name

    def get_selected_camera(self):
        """Get the currently selected camera name"""
        selected_camera = self.camera_selector.get_selected_camera()

        return selected_camera
    
    def change_to_config_page(self, selected_camera=None):
        """Switch to the configuration page"""
        print(f"Changing to config page... {selected_camera}")
        if selected_camera:
            self.switch_to_config_page.emit(selected_camera)
        else:
            QMessageBox.warning(self, "No Camera Selected", "Please select a camera before configuring.")
            print("No camera selected.")

    def update_camera_status_in_config(self, camera_name: str, status: str):
        """Update camera status in configuration file using both camera_id and camera_name"""
        self.config_manager.load_config()
        camera = self.config_manager.get_camera_by_name(camera_name)
        if camera:
            camera_id = camera.get('camera_id')
            if camera_id:
                # Validate camera exists with both fields
                if self.config_manager.validate_camera_exists(camera_id, camera_name):
                    success = self.config_manager.update_camera_status(camera_id, camera_name, status)

                    if success:
                        self.refresh_camera_data()
                    else:
                        print(f"Failed to update camera status for {camera_name}")
                else:
                    print(f"Camera validation failed for {camera_name}")
            else:
                print(f"Camera ID not found for {camera_name}")
        else:
            print(f"Camera {camera_name} not found")
    
    def update_parking_status_in_config(self, camera_name: str, parking_status: str):
        """Update parking status in configuration file using both camera_id and camera_name"""
        self.config_manager.load_config()
        camera = self.config_manager.get_camera_by_name(camera_name)
        if camera:
            camera_id = camera.get('camera_id')
            if camera_id:
                # Validate camera exists with both fields
                if self.config_manager.validate_camera_exists(camera_id, camera_name):
                    success = self.config_manager.update_parking_status(camera_id, camera_name, parking_status)
                    if success:
                        # Refresh the camera cards to show updated status
                        self.refresh_camera_cards()
                    else:
                        print(f"Failed to update parking status for {camera_name}")
                else:
                    print(f"Camera validation failed for {camera_name}")
            else:
                print(f"Camera ID not found for {camera_name}")
        else:
            print(f"Camera {camera_name} not found")
    
    def refresh_camera_data(self):
        """Refresh camera data from JSON configuration"""
        print("Dashboard: Refreshing camera data...")
        
        # Reload configuration from file to get latest changes
        self.config_manager.load_config()
        
        # Get fresh data
        self.camera_names = self.config_manager.get_camera_names()
        self.camera_statuses = self.config_manager.get_camera_statuses()
    
        self.camera_selector.update_camera_statuses()
    
    def refresh_camera_cards(self):
        """Refresh camera cards with updated data from configuration"""
        # Find and update the CamCardFrame widget
        for i in range(self.main_layout.count()):
            widget = self.main_layout.itemAt(i).widget()
            if hasattr(widget, '__class__') and widget.__class__.__name__ == 'CamCardFrame':
                # Update the existing widget instead of recreating it
                widget.update_camera_cards()
                break

    def on_data_updated(self, camera_id: str):
        """Handle when camera data is updated in JSON - refresh UI from config"""
        print(f"Data updated for camera {camera_id}, refreshing UI from JSON")
        
        # Refresh camera data from JSON
        self.refresh_camera_data()
        
        # Refresh camera cards to show updated status
        self.refresh_camera_cards()
    
    def on_camera_error(self, camera_id: str, error_message: str):
        """Handle camera errors"""
        print(f"Camera error for {camera_id}: {error_message}")
        
        # Update camera status to error in config
        self.config_manager.load_config()
        camera = self.config_manager.get_camera_by_id(camera_id)
        if camera:
            camera_name = camera.get('camera_name', '')
            if camera_name:
                self.update_camera_status_in_config(camera_name, CameraStatus.ERROR.value)
                self.update_parking_status_in_config(camera_name, ParkingStatus.UNKNOWN.value)
    
    def on_camera_processed(self, camera_id: str):
        """Handle when camera processing is complete"""
        print(f"Camera {camera_id} processing complete")
        # Could add specific UI updates here if needed
    
    def cleanup(self):
        """Clean up resources when dashboard is closed"""
        if hasattr(self, 'camera_manager'):
            self.camera_manager.shutdown()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

    def show_config_popup(self):
        """Show the camera configuration popup"""
        config_popup = ConfigPopup()
        
        # Connect to the configuration_changed signal
        config_popup.configuration_changed.connect(self.refresh_ui_after_config_changes)
        
        result = config_popup.exec()
        
        # If user clicked OK or Apply, refresh the dashboard
        if result == QDialog.DialogCode.Accepted:
            self.refresh_camera_data()
            self.refresh_camera_cards()
    
    def refresh_ui_after_config_changes(self):
        """Refresh UI after configuration changes"""
        self.refresh_camera_data()
        self.refresh_camera_cards()
