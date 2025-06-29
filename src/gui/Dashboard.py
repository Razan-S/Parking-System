from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from src.gui.CamSelector import CameraSelector
from src.gui.CamCard import CamCardFrame
from src.config.utils import CameraConfigManager
from src.CardManager import CardManager
import os

class Dashboard(QWidget):
    switch_to_config_page = pyqtSignal(str)

    def __init__(self, cameras_name=None, camera_statuses=None):
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
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create both camera selector and camera cards
        self.setup_dashboard_ui()

    def setup_dashboard_ui(self):
        """Setup the complete dashboard UI with both camera selector and cards"""
        
        # First add the camera selector at the top
        self.add_camera_selector()
        # Then add the camera cards below
        self.add_camera_cards()

    def add_camera_selector(self):
        """Add the camera selector widget at the top"""
        # Create camera selector
        self.camera_selector = CameraSelector(self.camera_names, self.camera_statuses)
        self.camera_selector.camera_selected.connect(lambda: self.change_to_config_page(self.camera_selector.get_selected_camera()))
        self.camera_selector.camera_changed.connect(self.on_camera_selection_changed)
          # Add to layout
        self.main_layout.addWidget(self.camera_selector)

    def add_camera_cards(self):
        """Add camera cards in a grid layout"""
        # Get camera data from JSON configuration
        cameras_data = self.config_manager.get_cameras_for_ui()
          # Ensure image paths are absolute
        ROOT_DIR = os.path.abspath(os.curdir)
        for camera in cameras_data:
            if camera.get('image') and not os.path.isabs(camera['image']):
                camera['image'] = os.path.join(ROOT_DIR, camera['image'])

        cameras_card = CamCardFrame()
        cameras_card.card_clicked.connect(lambda cam_id: self.handle_camera_card_click(cam_id))
        self.main_layout.addWidget(cameras_card)

    def handle_camera_card_click(self, camera_id):
        """Handle camera card click by finding the camera name and updating selector"""
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
    
    def refresh_camera_data(self):
        """Refresh camera data from JSON configuration"""
        self.camera_names = self.config_manager.get_camera_names()
        self.camera_statuses = self.config_manager.get_camera_statuses()
          # Update camera selector with new data
        if hasattr(self, 'camera_selector'):
            # Update the camera selector buttons with new statuses
            for i, camera_name in enumerate(self.camera_names):
                if i < len(self.camera_statuses):
                    self.camera_selector.update_camera_status(camera_name, self.camera_statuses[i])
    
    def update_camera_status_in_config(self, camera_name: str, status: str):
        """Update camera status in configuration file using both camera_id and camera_name"""
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
    
    def refresh_camera_cards(self):
        """Refresh camera cards with updated data from configuration"""
        # Find and update the CamCardFrame widget
        for i in range(self.main_layout.count()):
            widget = self.main_layout.itemAt(i).widget()
            if hasattr(widget, '__class__') and widget.__class__.__name__ == 'CamCardFrame':
                # Remove the old widget
                widget.setParent(None)
                # Create and add a new one with updated data
                cameras_data = self.config_manager.get_cameras_for_ui()
                ROOT_DIR = os.path.abspath(os.curdir)
                for camera in cameras_data:
                    if camera.get('image') and not os.path.isabs(camera['image']):
                        camera['image'] = os.path.join(ROOT_DIR, camera['image'])
                new_cameras_card = CamCardFrame(cameras_data=cameras_data)
                self.main_layout.insertWidget(i, new_cameras_card)
                break
