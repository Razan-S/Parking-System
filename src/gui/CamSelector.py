from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QButtonGroup, QFrame, QSizePolicy, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen
from src.enums import CameraStatus
from src.config.utils import CameraConfigManager

class CameraToggleButton(QPushButton):
    def __init__(self, camera_id, camera_name, status=CameraStatus.NOT_WORKING.value, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
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
        circle_y = self.height() // 2 - 6  # Center vertically
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
    
    def get_camera_id(self):
        return self.camera_id
    
    def get_camera(self):
        return {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "camera_status": self.status
        }

class CameraSelector(QWidget):
    camera_selected = pyqtSignal(dict)  # Signal to emit when camera selection changes
    camera_changed = pyqtSignal(str)  # Signal to emit when camera is toggled

    def __init__(self, parent=None):
        super().__init__(parent)

        self.config_manager = CameraConfigManager()
        cameras = self.config_manager.get_all_cameras()

        self.cameras = cameras if cameras else []
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

        # Create scroll area for camera buttons
        self.scroll_area = QScrollArea()  # Store reference to scroll area
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Set a maximum height to force scrolling when there are many cameras
        # Each button is 40px + 10px spacing, so calculate based on actual vs max cameras
        max_visible_cameras = 2.5  # Show 2.5 cameras to hint at more content below
        button_height = 40
        button_spacing = 10
        margins = 20  # Top and bottom margins
        
        # Use the smaller of actual cameras or max visible cameras for height calculation
        visible_cameras = min(len(self.cameras), max_visible_cameras)
        if visible_cameras == 0:
            visible_cameras = 1  # Minimum height for empty state
            
        max_height = int((visible_cameras * (button_height + button_spacing)) + margins)
        self.scroll_area.setMaximumHeight(max_height)
        self.scroll_area.setMinimumHeight(max_height)  # Also set minimum to prevent extra space
        
        # Only show vertical scrollbar if more than 2 cameras
        if len(self.cameras) > 2:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a9eff;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #3a8eef;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #2a7edf;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Create a widget to hold the buttons
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        
        # Create vertical layout for toggle buttons and store reference
        self.buttons_layout = QVBoxLayout(self.scroll_widget)
        self.buttons_layout.setSpacing(10)  # Space between buttons
        self.buttons_layout.setContentsMargins(10, 10, 10, 10)
        self.buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        
        # Create toggle buttons for each camera
        for i, camera in enumerate(self.cameras):
            status = camera.get('camera_status', CameraStatus.NOT_WORKING.value)
            camera_name = camera.get('camera_name', f"Camera {i + 1}")
            camera_id = camera.get('camera_id', f"cam_{i + 1}")
            
            toggle_button = CameraToggleButton(camera_id=camera_id, camera_name=camera_name, status=status)
            
            # Set the first camera as selected by default
            if i == 0:
                toggle_button.setChecked(True)
            
            # Connect signal to emit camera change
            toggle_button.toggled.connect(lambda checked, cam=camera.get("camera_name", "Unknown"): self.on_camera_changed(checked, cam))
            
            self.toggle_buttons.append(toggle_button)
            self.button_group.addButton(toggle_button)
            self.buttons_layout.addWidget(toggle_button, 0, Qt.AlignmentFlag.AlignHCenter)
        
        # Add stretch to keep buttons at top
        self.buttons_layout.addStretch()
        
        # Add the scroll area to the main layout
        layout.addWidget(self.scroll_area, 1)  # Give it stretch factor of 1

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
            # Auto-scroll to the selected camera
            for toggle_button in self.toggle_buttons:
                if toggle_button.get_camera_name() == camera and toggle_button.isChecked():
                    self.scroll_to_selected_camera(toggle_button)
                    break

    def get_selected_camera(self):
        """Get the currently selected camera"""
        for toggle_button in self.toggle_buttons:
            if toggle_button.isChecked():
                return toggle_button.get_camera()
        return None

    def set_selected_camera(self, camera_name):
        """Programmatically select a camera"""
        for toggle_button in self.toggle_buttons:
            if toggle_button.get_camera_name() == camera_name:
                toggle_button.setChecked(True)
                self.scroll_to_selected_camera(toggle_button)
                break

    def scroll_to_selected_camera(self, selected_button):
        """Automatically scroll to make the selected camera visible"""
        if not hasattr(self, 'scroll_area') or not selected_button:
            return
        
        # Use QTimer to ensure the UI is updated before scrolling
        QTimer.singleShot(10, lambda: self._perform_scroll_to_button(selected_button))
    
    def _perform_scroll_to_button(self, selected_button):
        """Perform the actual scrolling to the button"""
        if not selected_button or not hasattr(self, 'scroll_area'):
            return
            
        # Ensure the widget has been properly laid out
        self.scroll_widget.updateGeometry()
        
        # Get the button's position relative to the scroll widget
        button_pos = selected_button.pos()
        button_height = selected_button.height()
        
        # Get scroll area dimensions
        scroll_area_height = self.scroll_area.viewport().height()
        
        # Calculate the desired scroll position to center the button
        desired_scroll_pos = button_pos.y() - (scroll_area_height // 2) + (button_height // 2)
        
        # Ensure the scroll position is within valid bounds
        scroll_bar = self.scroll_area.verticalScrollBar()
        max_scroll = scroll_bar.maximum()
        min_scroll = scroll_bar.minimum()
        
        # Clamp the desired position to valid range
        final_scroll_pos = max(min_scroll, min(desired_scroll_pos, max_scroll))
        
        # Smoothly scroll to the position
        scroll_bar.setValue(final_scroll_pos)
        
        print(f"[CameraSelector] Auto-scrolled to camera: {selected_button.get_camera_name()}")

    def update_camera_status(self, camera_name, status):
        """Update the status of a specific camera"""
        for toggle_button in self.toggle_buttons:
            if toggle_button.get_camera_name() == camera_name:
                toggle_button.set_status(status)
                break

    def update_camera_statuses(self):
        """Refresh camera data from JSON configuration and update UI"""
        # Reload configuration from file
        print("[CameraSelector] Updating Cameras Statuses")
        self.config_manager.load_config()
        cameras = self.config_manager.get_all_cameras()
        
        print(f"[CameraSelector] Loaded {len(cameras)} cameras from config")
        for i, cam in enumerate(cameras):
            print(f"[CameraSelector] Camera {i}: {cam.get('camera_name', 'Unknown')} ({cam.get('camera_id', 'Unknown')})")
        
        # Store current selection to restore it
        current_selection = self.get_selected_camera()
        current_selection_name = current_selection.get('camera_name') if current_selection else None
        print(f"[CameraSelector] Current selection: {current_selection_name}")
        
        # Update internal data - store full camera objects, not just names
        self.cameras = cameras if cameras else []
        
        # Just recreate the buttons without touching the layout
        self.recreate_buttons()
        
        # Restore selection if possible
        if current_selection_name:
            self.set_selected_camera(current_selection_name)
        elif self.cameras:
            first_camera_name = self.cameras[0].get('camera_name', '')
            self.set_selected_camera(first_camera_name)

    def get_all_camera_statuses(self):
        """Get all camera statuses as a dictionary"""
        statuses = {}
        for toggle_button in self.toggle_buttons:
            statuses[toggle_button.get_camera_name()] = toggle_button.status
        return statuses
    
    def on_config_button_clicked(self):
        """Handle the configuration button click"""
        self.selected_camera = self.get_selected_camera()
        if self.selected_camera:
            # Emit signal or handle configuration logic here
            self.camera_selected.emit(self.selected_camera)
        else:
            QMessageBox.warning(self, "No Camera Selected", "Please select a camera to configure.")

    def recreate_buttons(self):
        """Recreate only the camera buttons without touching the main layout"""
        print(f"[CameraSelector] recreate_buttons called with {len(self.cameras)} cameras")
        
        if not hasattr(self, 'buttons_layout'):
            print("[CameraSelector] ERROR: buttons_layout not found!")
            return
            
        # Clear existing buttons
        self.clear_buttons_only(self.buttons_layout)
        
        # Update scroll area policy based on camera count
        if hasattr(self, 'scroll_area'):
            # Update maximum height based on camera count
            max_visible_cameras = 2.5  # Show 2.5 cameras to hint at more content below
            button_height = 40
            button_spacing = 10
            margins = 20  # Top and bottom margins
            
            # Use the smaller of actual cameras or max visible cameras for height calculation
            visible_cameras = min(len(self.cameras), max_visible_cameras)
            if visible_cameras == 0:
                visible_cameras = 1  # Minimum height for empty state
                
            max_height = int((visible_cameras * (button_height + button_spacing)) + margins)
            self.scroll_area.setMaximumHeight(max_height)
            self.scroll_area.setMinimumHeight(max_height)  # Also set minimum to prevent extra space
            
            if len(self.cameras) > 2:
                self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            else:
                self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create new buttons
        for i, camera in enumerate(self.cameras):
            status = camera.get('camera_status', CameraStatus.NOT_WORKING.value)
            camera_name = camera.get('camera_name', f"Camera {i + 1}")
            camera_id = camera.get('camera_id', f"cam_{i + 1}")
            
            print(f"[CameraSelector] Creating button for: {camera_name} ({camera_id})")
            
            toggle_button = CameraToggleButton(camera_id=camera_id, camera_name=camera_name, status=status)
            
            # Set the first camera as selected by default
            if i == 0:
                toggle_button.setChecked(True)
            
            # Connect signal to emit camera change
            toggle_button.toggled.connect(lambda checked, cam=camera_name: self.on_camera_changed(checked, cam))
            
            self.toggle_buttons.append(toggle_button)
            self.button_group.addButton(toggle_button)
            self.buttons_layout.addWidget(toggle_button, 0, Qt.AlignmentFlag.AlignHCenter)
            
            print(f"[CameraSelector] Added button to layout: {camera_name}")
        
        # Add stretch to keep buttons at top
        self.buttons_layout.addStretch()
        
        print(f"[CameraSelector] Total buttons created: {len(self.toggle_buttons)}")

    def clear_buttons_only(self, buttons_layout):
        """Clear only the camera buttons from the buttons layout"""
        print(f"[CameraSelector] Clearing {len(self.toggle_buttons)} existing buttons")
        
        # Disconnect signals first
        for button in self.toggle_buttons:
            try:
                button.toggled.disconnect()
            except:
                pass
        
        # Clear the button group
        if hasattr(self, 'button_group'):
            self.button_group.setExclusive(False)
            for button in self.button_group.buttons():
                self.button_group.removeButton(button)
        
        # Remove widgets from the buttons layout
        while buttons_layout.count():
            child = buttons_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
                child.widget().deleteLater()
        
        # Clear the buttons list and recreate button group
        self.toggle_buttons = []
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        print("[CameraSelector] Buttons cleared successfully")