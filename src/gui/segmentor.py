from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QFrame,
                            QMessageBox, QSplitter, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from src.gui.components import VideoFrameWidget, DarkButton, CoordinateCard
from src.config.utils import CameraConfigManager
from ..utils import is_valid_polygon
import cv2 as cv

class RoadSegmenterGUI(QMainWindow):
    switch_to_dashboard_page = pyqtSignal(str)

    def __init__(self, camera_id=None):
        super().__init__()
        self.config_manager = CameraConfigManager()
        self.camera_id = camera_id

        if not self.camera_id:
            self.video_path = None
            self.current_coordinates = []
            self.frame_counter = 1
            self.saved_frames = []
            self.cap = None
        else:
            self.setup()
        
    def init_ui(self):
        self.setWindowTitle("Road Segmenter")
        self.setGeometry(0, 0, 1400, 800)
        
        central_widget = QWidget()
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
        
        splitter.setSizes([350, 1050])

    def setup(self):
        """Set up the video path and load the first frame"""
        if self.camera_id:
            camera = self.config_manager.get_camera_by_id(self.camera_id)
        else:
            QMessageBox.warning(self, "No Camera ID", "Please set a camera ID before proceeding.")
            return
        
        self.video_path = camera.get('video_source', None)
        existing_zones = camera.get('detection_zones', [])

        self.init_ui()
        self.load_single_frame()
        self.load_existing_detection_zones(existing_zones)

    def load_single_frame(self):
        """Load only the first frame from the video"""
        try:
            self.cap = cv.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                print(f"Error: Could not open video file: {self.video_path}")
                return
            
            # Read only the first frame
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.video_widget.set_frame(frame)
                self.clear_btn.setEnabled(True)
            else:
                print("Could not read first frame")
            
            # Close video capture to free resources
            self.cap.release()
            self.cap = None
                
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
            self.submit_btn.setEnabled(True)

    def create_menu_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #333;
                border-radius: 8px;
                border: 1px solid #555;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🛣️ Road Segmenter")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #0d7377;
                padding: 10px 0;
            }        """)
        layout.addWidget(title)

        self.back_btn = DarkButton("🔙 Main page")
        self.back_btn.setEnabled(True)
        self.back_btn.clicked.connect(self.go_back_to_dashboard)
        layout.addWidget(self.back_btn)
        
        # Clear coordinates button
        self.clear_btn = DarkButton("🗑️ Clear Points")
        self.clear_btn.clicked.connect(self.clear_coordinates)
        self.clear_btn.setEnabled(False)
        layout.addWidget(self.clear_btn)
        
        # Add Frame button
        self.add_frame_btn = DarkButton("➕ Add Frame")
        self.add_frame_btn.clicked.connect(self.add_frame)
        self.add_frame_btn.setEnabled(False)
        layout.addWidget(self.add_frame_btn)
        
        # Coordinates cards
        coords_label = QLabel("📍 Saved Frames:")
        coords_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #0d7377;
                margin-top: 10px;
            }
        """)
        layout.addWidget(coords_label)
        
        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: #2b2b2b;
                border: none;
            }
        """)
        
        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)
        
        # Submit button
        self.submit_btn = DarkButton("✅ Submit All", primary=True)
        self.submit_btn.clicked.connect(self.submit_all_frames)
        self.submit_btn.setEnabled(False)
        layout.addWidget(self.submit_btn)
        
        return panel
    
    def create_video_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #333;
                border-radius: 8px;
                border: 1px solid #555;
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
            self.submit_btn.setEnabled(len(self.saved_frames) > 0)
    
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

        response = self.config_manager.update_detection_zone(camera_id=self.camera_id, detection_zones=self.saved_frames)
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
        
        # Reset all state when closing/switching
        self.reset_all_state()
        
        self.camera_id = None
        self.video_path = None
        self.cap = None

    def is_changed(self):
        """Check if there are any changes to the saved frames"""
        return self.saved_frames != self.existing_frames or self.current_coordinates

    def reset_all_state(self):
        """Reset all state variables and clear UI elements"""
        # Clear coordinates and frames
        self.current_coordinates = []
        self.saved_frames = []
        self.frame_counter = 1
        
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