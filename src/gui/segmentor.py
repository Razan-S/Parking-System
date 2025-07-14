from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QFrame,
                            QMessageBox, QSplitter, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from src.gui.components import VideoFrameWidget, DarkButton, CoordinateCard
from src.config.utils import CameraConfigManager
from ..utils import is_valid_polygon
import cv2 as cv
import numpy as np
from datetime import datetime

class RoadSegmenterGUI(QMainWindow):
    switch_to_dashboard_page = pyqtSignal(str)

    def __init__(self, camera_id=None):
        super().__init__()
        self.config_manager = CameraConfigManager()
        self.camera_manager = None  # Will be set later by window

        self.camera = self.config_manager.get_camera_by_id(camera_id) if camera_id else None
        self.camera_id = camera_id
        
        if self.camera:
            self.camera_name = self.camera.get('camera_name', 'Road Segmenter')

        # Initialize all attributes first
        self.video_path = None
        self.image_path = self.camera.get('image_path', None) if self.camera else None
        self.current_coordinates = []
        self.frame_counter = 1
        self.saved_frames = []
        self.cap = None
        self.last_frame_time = None
        self.time_label = None
        self.date_label = None
        self.ui_initialized = False
        self.waiting_for_frame = False  # Flag to prevent multiple frame requests
        
        # Initialize timer for clock updates (but don't start yet)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        
        if self.camera_id:
            self.setup()
        else:
            # Initialize UI even without camera for consistency
            self.init_ui()
            self.ui_initialized = True
            self.timer.start(1000)  # Start timer after UI is ready
        
    def init_ui(self):
        self.setWindowTitle("Road Segmenter")
        self.setGeometry(0, 0, 1400, 800)
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")
        
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: #1a1a1a; }")
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        menu_panel = self.create_menu_panel()
        video_panel = self.create_video_panel()

        splitter.addWidget(video_panel)
        splitter.addWidget(menu_panel)
        
        splitter.setSizes([1050, 350])

    def setup(self):
        """Set up the video path and load the first frame"""
        if self.camera_id:
            camera = self.config_manager.get_camera_by_id(self.camera_id)
        else:
            QMessageBox.warning(self, "No Camera ID", "Please set a camera ID before proceeding.")
            return
        
        self.video_path = camera.get('video_source', None)
        self.image_path = camera.get('image_path', None)
        existing_zones = camera.get('detection_zones', [])

        # Only init UI if not already initialized
        if not self.ui_initialized:
            self.init_ui()
            self.ui_initialized = True
            self.timer.start(1000)  # Start timer after UI is ready
            
        self.load_single_frame()
        self.load_existing_detection_zones(existing_zones)

    def load_single_frame(self):
        """Load the current image from camera configuration"""
        try:
            if not self.image_path:
                if not self.camera_id and not self.camera:
                    QMessageBox.warning(self, "No Image Source", "No image source set for the camera.")
                    return
                
                self.image_path = self.camera.get('image_path', None)

            print(f"Loading image from path: {self.image_path}")
            frame = cv.imread(self.image_path)
            if frame is None:
                QMessageBox.warning(self, "Image Load Error", "Failed to load image from the specified path.")
                return
                
            # Display the frame
            if hasattr(self, 'video_widget') and self.video_widget:
                self.video_widget.set_frame(frame)
                if hasattr(self, 'clear_btn'):
                    self.clear_btn.setEnabled(True)
                self.last_frame_time = datetime.now()
                self.update_clock()
            else:
                print("Video widget not available")
                
        except Exception as e:
            print(f"Error loading frame: {e}")
        
    def load_existing_detection_zones(self, existing_zones):
        """Load existing detection zones and display them as coordinate cards"""
        if not existing_zones:
            return
        
        self.existing_frames = []

        for zone in existing_zones:
            polygon_points = zone.get('polygon_points', [])
            if not polygon_points:
                continue
                
            # Convert polygon points to coordinate format
            coordinates = []
            for point in polygon_points:
                coordinates.append([point.get('x', 0), point.get('y', 0)])

            if coordinates:
                # Create frame data for existing zone
                frame_data = {
                    'id': self.frame_counter,
                    'coordinates': coordinates,
                    'is_existing': True  # Flag to identify existing zones
                }
                self.saved_frames.append(frame_data)
                self.existing_frames.append(frame_data)
                
                # Add existing zone to video widget with orange color
                self.video_widget.add_existing_polygon(coordinates, self.frame_counter)
                
                # Create card for existing zone
                card = CoordinateCard(self.frame_counter, coordinates)
                card.card_deleted.connect(self.delete_frame)
                self.cards_layout.addWidget(card)
                
                self.frame_counter += 1
        
        # Enable submit button if there are existing zones
        if self.saved_frames:
            self.submit_btn.setEnabled(False)

    def create_menu_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Back button
        self.back_btn = DarkButton("Back")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #4a9eff;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        self.back_btn.clicked.connect(self.go_back_to_dashboard)
        layout.addWidget(self.back_btn)
        
        # Add Frame button
        self.add_frame_btn = DarkButton("Add Frame")
        self.add_frame_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #3a8eef;
            }
            QPushButton:pressed {
                background-color: #2a7edf;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
                border-color: #999999;
            }
        """)
        self.add_frame_btn.clicked.connect(self.add_frame)
        self.add_frame_btn.setEnabled(False)
        layout.addWidget(self.add_frame_btn)
        
        # Clear Points button
        self.clear_btn = DarkButton("Clear points")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QPushButton:pressed {
                background-color: #990000;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
                border-color: #999999;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_coordinates)
        self.clear_btn.setEnabled(False)
        layout.addWidget(self.clear_btn)
        
        # Clock display
        clock_frame = QFrame()
        clock_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 5px;
                min-height: 90px;
                max-height: 90px;
            }
        """)
        clock_layout = QVBoxLayout(clock_frame)
        clock_layout.setContentsMargins(5, 5, 5, 5)
        clock_layout.setSpacing(2)
        
        clock_label = QLabel("Latest frame at:")
        clock_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #ffffff;
                border: none;
                background: transparent;
                padding: 2px;
                margin: 0px;
                min-height: 16px;
            }
        """)
        clock_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        clock_layout.addWidget(clock_label)
        
        self.time_label = QLabel("--:--")
        self.time_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #4a9eff;
                border: none;
                background: transparent;
                padding: 2px;
                margin: 0px;
                min-height: 24px;
            }
        """)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        clock_layout.addWidget(self.time_label)
        
        self.date_label = QLabel("-- --- ----")
        self.date_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #ffffff;
                border: none;
                background: transparent;
                padding: 2px;
                margin: 0px;
                min-height: 16px;
            }
        """)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        clock_layout.addWidget(self.date_label)
        
        # Add stretch to push content to top
        clock_layout.addStretch()
        
        layout.addWidget(clock_frame)
        
        # Saved Frame section
        saved_frame_label = QLabel("Saved Frame")
        saved_frame_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #4a9eff;
                margin-top: 15px;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(saved_frame_label)
        
        # Scroll area for saved frames
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)  # Set minimum height for larger saved frame area
        scroll.setMaximumHeight(300)  # Set maximum height to prevent it from being too large
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: 1px solid #666666;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a9eff;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #3a8eef;
            }
        """)
        
        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setSpacing(5)
        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)
        
        # Add stretch to push buttons to bottom
        layout.addStretch()
        
        # New Shot button
        self.new_shot_btn = DarkButton("New Shot")
        self.new_shot_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #3a8eef;
            }
            QPushButton:pressed {
                background-color: #2a7edf;
            }
        """)
        self.new_shot_btn.clicked.connect(self.take_new_shot)
        layout.addWidget(self.new_shot_btn)
        
        # Submit button
        self.submit_btn = DarkButton("Submit")
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #3a8eef;
            }
            QPushButton:pressed {
                background-color: #2a7edf;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
                border-color: #999999;
            }
        """)
        self.submit_btn.clicked.connect(self.submit_all_frames)
        self.submit_btn.setEnabled(False)
        layout.addWidget(self.submit_btn)
        
        return panel
    
    def create_video_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 8px;
                border: 1px solid #666666;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Video frame widget
        self.video_widget = VideoFrameWidget()
        self.video_widget.coordinates_updated.connect(self.update_coordinates)
        layout.addWidget(self.video_widget)
        
        return panel
    
    def update_coordinates(self, coordinates):
        self.current_coordinates = coordinates
        self.add_frame_btn.setEnabled(len(coordinates) > 0)
    
    def clear_coordinates(self):
        self.video_widget.clear_coordinates()
        self.current_coordinates = []
        self.add_frame_btn.setEnabled(False)

        if self.existing_frames == self.saved_frames:
            self.submit_btn.setEnabled(False)
    
    def add_frame(self):
        if not self.current_coordinates:
            QMessageBox.warning(self, "No Coordinates", "Please add some coordinates before saving the frame.")
            return
        
        is_valid, _, message = is_valid_polygon(self.current_coordinates, min_points=3, min_area=10)
        
        if not is_valid:
            QMessageBox.warning(self, "Invalid Polygon", message)
            self.clear_coordinates()
            return

        # Save current frame
        frame_data = {
            'id': self.frame_counter,
            'coordinates': self.current_coordinates.copy()
        }
        self.saved_frames.append(frame_data)
        
        # Add new polygon to video widget with default color
        self.video_widget.add_new_polygon(self.current_coordinates.copy(), self.frame_counter)
        
        # Create card
        card = CoordinateCard(self.frame_counter, self.current_coordinates)
        card.card_deleted.connect(self.delete_frame)  # Connect delete signal
        self.cards_layout.addWidget(card)
        
        self.frame_counter += 1
        self.submit_btn.setEnabled(True)
        
        # Clear current selection
        self.clear_coordinates()
    
    def delete_frame(self, frame_id):
        """Delete a frame and its card"""
        reply = QMessageBox.question(
            self, 
            "Delete Frame", 
            f"Are you sure you want to delete Frame {frame_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove polygon from video widget
            self.video_widget.remove_polygon(frame_id)
            
            # Remove from saved_frames
            self.saved_frames = [frame for frame in self.saved_frames if frame['id'] != frame_id]
            
            # Remove card from layout
            for i in range(self.cards_layout.count()):
                item = self.cards_layout.itemAt(i)
                if item and item.widget():
                    card = item.widget()
                    if hasattr(card, 'frame_id') and card.frame_id == frame_id:
                        card.setParent(None)
                        card.deleteLater()
                        break
            
            # Update submit button state
            self.submit_btn.setEnabled(len(self.saved_frames) > 0 and (self.saved_frames != self.existing_frames))
    
    def submit_all_frames(self):
        if not self.saved_frames:
            QMessageBox.information(self, "Info", "No frames to submit!")
            return
        
        if self.current_coordinates:
            QMessageBox.warning(self, "Unsaved Coordinates", "Please save the current coordinates before submitting.")
            return

        if self.saved_frames == self.existing_frames:
            QMessageBox.information(self, "Info", "No changes detected. No need to submit.")
            return

        # Get camera details for proper validation
        camera = self.config_manager.get_camera_by_id(self.camera_id)
        if not camera:
            QMessageBox.warning(self, "Error", "Camera not found in configuration.")
            return
            
        camera_name = camera.get('camera_name')
        if not camera_name:
            QMessageBox.warning(self, "Error", "Camera name not found in configuration.")
            return

        response = self.config_manager.update_detection_zone(
            camera_id=self.camera_id, 
            camera_name=camera_name, 
            detection_zones=self.saved_frames
        )
        if response:
            QMessageBox.information(self, "Success", "Detection zone updated successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to update detection zone.")
        
        self.closeEvent()  # Clean up before switching
        self.switch_to_dashboard_page.emit("dashboard")

    def set_camera(self, camera_id):
        """Set the video path and load the first frame"""
        self.camera_id = camera_id
        
        # Reset all state when setting a new camera
        self.reset_all_state()
        
        # Only setup if camera_id is valid
        if camera_id:
            self.setup()

    def go_back_to_dashboard(self):
        """Handle back button click to return to dashboard"""
        if self.is_changed():
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                "You have unsaved changes. Do you want to save them before leaving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.submit_all_frames()
            else:
                return
        
        self.closeEvent()  # Clean up before switching
        self.switch_to_dashboard_page.emit("dashboard")
    
    def closeEvent(self):
        """Clean up resources when closing or switching away"""
        if self.cap:
            self.cap.release()
        
        # Stop the timer
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
        
        # Reset all state when closing/switching
        self.reset_all_state()
        
        self.camera_id = None
        self.video_path = None
        self.cap = None
        self.ui_initialized = False

    def is_changed(self):
        """Check if there are any changes to the saved frames"""
        return self.saved_frames != self.existing_frames or self.current_coordinates

    def reset_all_state(self):
        """Reset all state variables and clear UI elements"""
        # Clear coordinates and frames
        self.current_coordinates = []
        self.saved_frames = []
        self.frame_counter = 1
        self.last_frame_time = None
        
        # Clear video widget coordinates and polygons
        if hasattr(self, 'video_widget'):
            self.video_widget.clear_coordinates()
            self.video_widget.clear_all_polygons()
        
        # Clear all frame cards from the layout
        if hasattr(self, 'cards_layout'):
            # Remove all cards from the layout
            while self.cards_layout.count():
                item = self.cards_layout.takeAt(0)
                if item and item.widget():
                    widget = item.widget()
                    widget.setParent(None)
                    widget.deleteLater()
        
        # Reset button states
        if hasattr(self, 'add_frame_btn'):
            self.add_frame_btn.setEnabled(False)
        if hasattr(self, 'submit_btn'):
            self.submit_btn.setEnabled(False)
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setEnabled(False)
        
        # Update clock display
        if hasattr(self, 'update_clock') and hasattr(self, 'time_label') and self.time_label:
            self.update_clock()
    
    def update_clock(self):
        """Update the clock display with the latest frame time"""
        # Check if UI components exist before updating
        if not hasattr(self, 'time_label') or not self.time_label:
            return
            
        if self.last_frame_time:
            time_str = self.last_frame_time.strftime("%H:%M")
            date_str = self.last_frame_time.strftime("%d %b %Y")
            self.time_label.setText(time_str)
            self.date_label.setText(date_str)
        else:
            self.time_label.setText("--:--")
            self.date_label.setText("-- --- ----")
    
    def take_new_shot(self):
        """Take a new shot by refreshing the current image from configuration"""
        if not self.camera_id:
            QMessageBox.warning(self, "No Camera", "No camera selected for new shot.")
            return
        
        # Clear current coordinates
        self.clear_coordinates()
        
        # Simply reload the current frame from configuration
        # The camera manager updates the image_source every 5 seconds
        self.load_single_frame()
        
        QMessageBox.information(self, "New Shot", "Frame refreshed successfully!")
    
    def stop_detection(self):
        """Stop detection functionality - placeholder for future implementation"""
        QMessageBox.information(self, "Stop Detection", "Detection stopped.")
        # This is a placeholder - implement actual stop detection logic here
        pass

    def set_camera_manager(self, camera_manager):
        """Set the camera manager reference (kept for compatibility)"""
        self.camera_manager = camera_manager
        print("Camera manager reference set in segmentor")
    
    def on_frame_received(self, camera_id: str, frame):
        """Handle frame received from camera manager"""
        if camera_id == self.camera_id and frame is not None:
            self.waiting_for_frame = False
            print(f"Frame received for camera {camera_id}")
            
            if hasattr(self, 'video_widget') and self.video_widget:
                self.video_widget.set_frame(frame)
                if hasattr(self, 'clear_btn'):
                    self.clear_btn.setEnabled(True)
                self.last_frame_time = datetime.now()
                self.update_clock()
            else:
                print("Video widget not ready yet")
        else:
            print(f"Frame received for different camera: {camera_id} (expected: {self.camera_id})")
    
    def request_frame_from_camera_manager(self):
        """Request a frame from the camera manager"""
        if self.camera_manager and self.camera_id and not self.waiting_for_frame:
            print(f"Requesting frame for camera {self.camera_id}")
            self.waiting_for_frame = True
            self.camera_manager.get_latest_frame_for_config(self.camera_id)
        elif self.waiting_for_frame:
            print("Already waiting for frame")
        else:
            print("Camera manager or camera_id not set")