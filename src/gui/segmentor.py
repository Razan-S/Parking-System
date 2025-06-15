from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QFrame,
                            QMessageBox, QSplitter, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from src.gui.components import VideoFrameWidget, DarkButton, CoordinateCard
from ..utils import is_valid_polygon
import cv2 as cv

class RoadSegmenterGUI(QMainWindow):
    coordinates_submitted = pyqtSignal(list)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.current_coordinates = []
        self.frame_counter = 1
        self.saved_frames = []
        self.cap = None
        self.submitted_coordinates = None

        self.init_ui()
        self.load_single_frame()
        
    def init_ui(self):
        self.setWindowTitle("Road Segmenter")
        self.setGeometry(100, 100, 1400, 800)
        
        # Dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
            }
            QSpinBox {
                padding: 8px;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 13px;
                background: #404040;
                color: #e0e0e0;
            }
            QSpinBox:focus {
                border-color: #0d7377;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left sidebar
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel (segmentation area)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([350, 1050])
    
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
        
    def create_left_panel(self):
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
            }
        """)
        layout.addWidget(title)

        self.back_btn = DarkButton("🔙 Main page")
        self.back_btn.setEnabled(True)
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
    
    def create_right_panel(self):
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
        
        result_text = f"Successfully submitted {len(self.saved_frames)} frames:\n\n"
        for frame in self.saved_frames:
            result_text += f"Frame {frame['id']}: {len(frame['coordinates'])} points\n"
        
        msg = QMessageBox()
        msg.setWindowTitle("Frames Submitted")
        msg.setText("✅ All frames submitted successfully!")
        msg.setDetailedText(result_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        
        # Store coordinates for later retrieval
        self.submitted_coordinates = self.saved_frames.copy()
        
        # Method 1: Emit signal
        self.coordinates_submitted.emit(self.saved_frames)

    def get_submitted_coordinates(self):
        """Get the last submitted coordinates"""
        return self.video_widget.frame, self.submitted_coordinates
    
    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        event.accept()