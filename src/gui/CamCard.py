from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QScrollArea, QMessageBox
from PyQt6.QtGui import QPixmap, QFont, QImage
import cv2 as cv
import os

from src.config.utils import CameraConfigManager

class CamCard(QWidget):
    card_clicked = pyqtSignal(str)  # Signal emitted when card is clicked
    
    def __init__(self, camera_name="Unknown", camera_id="0", location="Unknown", 
                 camera_status="error", parking_status="empty", video_source=None, card_size=(300, 350)):
        super().__init__()        
        self.camera_name = camera_name
        self.camera_id = camera_id
        self.location = location
        self.camera_status = camera_status  # "working", "not_working", "error"
        self.parking_status = parking_status  # "available", "occupied", "unknown"
        self.video_source = video_source
        
        self.init_ui()
        self.setFixedSize(card_size[0], card_size[1])
        self.setStyleSheet("""
            QWidget {
                border: 2px solid #000000;  
            }
        """)


    def init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Image section (200px height, rounded top corners)
        self.image_label = QLabel()
        self.image_label.setFixedSize(300, 200)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border: none;
            }
        """)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        
        # Load image or show placeholder
        self.load_image()
        layout.addWidget(self.image_label)
          # Content section (150px height for remaining content)
        content_widget = QWidget()
        content_widget.setFixedSize(300, 150)
        content_widget.setStyleSheet("QWidget { border: none; }")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 10, 15, 10)
        content_layout.setSpacing(8)
        
        # Camera name and ID row
        name_id_layout = QHBoxLayout()
        name_id_layout.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel(self.camera_name)
        name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #333333;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        id_label = QLabel(f"#{self.camera_id}")
        id_label.setFont(QFont("Arial", 12))
        id_label.setStyleSheet("color: #666666; margin-left: 5px;")
        
        name_id_layout.addStretch()
        name_id_layout.addWidget(name_label)
        name_id_layout.addWidget(id_label)
        name_id_layout.addStretch()
        
        content_layout.addLayout(name_id_layout)
        
        # Location row
        location_layout = QHBoxLayout()
        location_layout.setContentsMargins(0, 0, 0, 0)
        
        # Location icon (using text for now, can be replaced with actual icon)
        location_icon = QLabel("📍")
        location_icon.setFont(QFont("Arial", 12))
        location_icon.setFixedSize(20, 20)
        
        location_label = QLabel(self.location)
        location_label.setFont(QFont("Arial", 11))
        location_label.setStyleSheet("color: #666666;")
        
        location_layout.addWidget(location_icon)
        location_layout.addWidget(location_label)
        location_layout.addStretch()
        
        content_layout.addLayout(location_layout)
        
        # Camera status row
        camera_status_layout = QHBoxLayout()
        camera_status_layout.setContentsMargins(0, 0, 0, 0)
        
        camera_status_label = QLabel("Camera:")
        camera_status_label.setFont(QFont("Arial", 10))
        camera_status_label.setStyleSheet("color: #666666;")
        
        camera_status_circle = QLabel()
        camera_status_circle.setFixedSize(12, 12)
        camera_status_circle.setStyleSheet(self.get_status_circle_style(self.camera_status))
        
        camera_status_text = QLabel(self.get_status_text(self.camera_status))
        camera_status_text.setFont(QFont("Arial", 10))
        camera_status_text.setStyleSheet("color: #333333; margin-left: 5px;")
        
        camera_status_layout.addWidget(camera_status_label)
        camera_status_layout.addWidget(camera_status_circle)
        camera_status_layout.addWidget(camera_status_text)
        camera_status_layout.addStretch()
        
        content_layout.addLayout(camera_status_layout)
        
        # Parking status row
        parking_status_layout = QHBoxLayout()
        parking_status_layout.setContentsMargins(0, 0, 0, 0)
        
        parking_status_label = QLabel("Parking:")
        parking_status_label.setFont(QFont("Arial", 10))
        parking_status_label.setStyleSheet("color: #666666;")
        
        parking_status_circle = QLabel()
        parking_status_circle.setFixedSize(12, 12)
        parking_status_circle.setStyleSheet(self.get_parking_status_circle_style(self.parking_status))
        
        parking_status_text = QLabel(self.get_parking_status_text(self.parking_status))
        parking_status_text.setFont(QFont("Arial", 10))
        parking_status_text.setStyleSheet("color: #333333; margin-left: 5px;")
        
        parking_status_layout.addWidget(parking_status_label)
        parking_status_layout.addWidget(parking_status_circle)
        parking_status_layout.addWidget(parking_status_text)
        parking_status_layout.addStretch()
        
        content_layout.addLayout(parking_status_layout)
        
        layout.addWidget(content_widget)
        
    def load_image(self):
        """Load camera image or show placeholder"""
        if self.video_source and os.path.exists(self.video_source):
            cap = cv.VideoCapture(self.video_source)
            if not cap.isOpened():
                QMessageBox.warning(self, "Error", f"Could not open video source: {self.video_source}")
                return
            
            ret, frame = cap.read()
            cap.release()  # Don't forget to release the capture
            
            if not ret:
                QMessageBox.warning(self, "Error", "Could not read frame from video source.")
                return
            
            # Convert BGR to RGB (OpenCV uses BGR, Qt uses RGB)
            rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            
            # Convert to QImage
            height, width, channels = rgb_frame.shape
            bytes_per_line = channels * width
            q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Convert QImage to QPixmap
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                        Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            # Show placeholder text
            self.image_label.setText("📷\nNo Image")
            self.image_label.setStyleSheet("""
                QLabel {
                    background-color: #f5f5f5;
                    border-top-left-radius: 12px;
                    border-top-right-radius: 12px;
                    border: none;
                    color: #999999;
                    font-size: 24px;
                }
            """)
    
    def get_status_circle_style(self, status):
        """Get CSS style for camera status circle"""
        colors = {
            "working": "#4CAF50",      # Green
            "not_working": "#F44336",  # Red
            "error": "#FF9800"         # Orange
        }
        color = colors.get(status, "#9E9E9E")  # Default gray
        return f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
                border: none;
            }}
        """
    
    def get_parking_status_circle_style(self, status):
        """Get CSS style for parking status circle"""
        colors = {
            "available": "#4CAF50",    # Green
            "occupied": "#F44336",     # Red
            "unknown": "#FF9800"       # Orange
        }
        color = colors.get(status, "#9E9E9E")  # Default gray
        return f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
                border: none;
            }}
        """
    
    def get_status_text(self, status):
        """Get display text for camera status"""
        texts = {
            "working": "Working",
            "not_working": "Not Working",
            "error": "Error"
        }
        return texts.get(status, "Unknown")
    
    def get_parking_status_text(self, status):
        """Get display text for parking status"""
        texts = {
            "available": "Available",
            "occupied": "Car Parking",
            "unknown": "Unknown"
        }
        return texts.get(status, "Unknown")
    
    def update_properties(self, camera_name=None, camera_id=None, location=None, 
                         camera_status=None, parking_status=None, image_path=None):
        """Update card properties and refresh display"""
        if camera_name is not None:
            self.camera_name = camera_name
        if camera_id is not None:
            self.camera_id = camera_id
        if location is not None:
            self.location = location
        if camera_status is not None:
            self.camera_status = camera_status
        if parking_status is not None:
            self.parking_status = parking_status
        if image_path is not None:
            self.image_path = image_path
            
        # Refresh the UI
        self.refresh_ui()
    
    def refresh_ui(self):
        """Refresh the UI with current properties"""
        # Clear and recreate the UI
        for i in reversed(range(self.layout().count())): 
            self.layout().itemAt(i).widget().setParent(None)
        self.init_ui()
    
    def mousePressEvent(self, event):
        """Handle mouse click events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.card_clicked.emit(self.camera_id)  # Emit signal with camera ID
        super().mousePressEvent(event)

class CamCardFrame(QWidget):
    card_clicked = pyqtSignal(str)  # Signal emitted when a camera card is clicked

    """Custom frame to hold CamCard with rounded corners"""
    def __init__(self, cards_per_row=2, card_size=(300, 350)):
        super().__init__()
        self.ROOT_DIR = os.path.abspath(os.curdir)
        self.IMAGE_DIR = os.path.join(self.ROOT_DIR, "image")

        self.config_manager = CameraConfigManager()

        self.cameras = self.config_manager.get_all_cameras()
        self.cards_per_row = cards_per_row
        self.card_size = card_size

        self.main_layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea()

        self.init_ui()

    def init_ui(self):
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        label = QLabel("Camera Monitor Cards")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #000000;
            }
        """)

        self.main_layout.addWidget(label)
        
        # Create scroll area for camera cards
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Add the camera cards
        self.add_camera_cards()
        
        # Add scroll area to main layout
        self.main_layout.addWidget(self.scroll_area)

    def add_camera_cards(self):
        """Add camera cards in a scrollable area"""
        if not self.cameras:
            QMessageBox.warning(self, "No Cameras", "No camera data available to display.")
            return
        
        # Create content widget for cards
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create rows for cards
        current_row_layout = None
        
        for i, camera_data in enumerate(self.cameras):
            # Create new row layout if needed
            if i % self.cards_per_row == 0:
                current_row_layout = QHBoxLayout()
                current_row_layout.setSpacing(20)
                content_layout.addLayout(current_row_layout)
            
            # Create camera card
            card = CamCard(
                camera_name=camera_data["camera_name"],
                camera_id=camera_data["camera_id"],
                location=camera_data["location"],
                camera_status=camera_data["camera_status"],
                parking_status=camera_data["parking_status"],
                video_source=camera_data["video_source"],
                card_size=self.card_size
            )
            
            # Connect card click signal
            card.card_clicked.connect(self.on_camera_card_clicked)
            
            # Add card to current row
            current_row_layout.addWidget(card)
        
        # Add stretch to the last row if it's not full
        if len(self.cameras) % self.cards_per_row != 0:
            current_row_layout.addStretch()

        # Add stretch to push content to the top
        content_layout.addStretch()
        
        # Set scroll area content
        self.scroll_area.setWidget(content_widget)

    def on_camera_card_clicked(self, camera_id):
        """Handle camera card click events"""
        print(f"CamCardFrame: Camera card clicked: {camera_id}")
        self.card_clicked.emit(camera_id)