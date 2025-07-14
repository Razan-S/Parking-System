from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QScrollArea, QMessageBox
from PyQt6.QtGui import QPixmap, QFont, QImage
import cv2 as cv
import os

from src.config.utils import CameraConfigManager
from src.enums import ParkingStatus, CameraStatus
class CamCard(QWidget):
    card_clicked = pyqtSignal(str)  # Signal emitted when card is clicked
    
    def __init__(self, camera_name="Unknown", camera_id="0", location="Unknown", 
                 camera_status=CameraStatus.ERROR.value, parking_status=ParkingStatus.UNKNOWN.value, 
                 video_source=None, image_path=None, card_size=(400, 480)):
        super().__init__()        
        self.camera_name = camera_name
        self.camera_id = camera_id
        self.location = location
        self.camera_status = camera_status  # CameraStatus enum values
        self.parking_status = parking_status  # ParkingStatus enum values
        self.video_source = video_source
        self.image_path = image_path  # Path to the latest saved image
        
        self.init_ui()
        self.setFixedSize(card_size[0], card_size[1])
        # Border styling moved to container frame in init_ui()

    def init_ui(self):
        # Create main layout with proper margins for border
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(3, 3, 3, 3)  # Account for border width
        main_layout.setSpacing(0)
        
        # Create a container frame for the border (responsive to card size)
        container_frame = QFrame()
        container_frame.setObjectName("CamCardContainer")
        container_frame.setFixedSize(314, 400)  # Exact size to fit within card bounds
        # container_frame.setStyleSheet("""
        #     QFrame#CamCardContainer {
        #         border: 3px solid #D2042D;
        #         background-color: #D2042D;
        #         border-radius: 12px;
        #     }
        # """)
        
        main_layout.addWidget(container_frame)
        
        # Create content layout inside the container
        layout = QVBoxLayout(container_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Calculate available width for content within the container
        content_width = 314  # Container width
        image_height = 220
        content_height = 180
        
        # Image section (responsive height, rounded top corners)
        self.image_label = QLabel()
        self.image_label.setFixedSize(content_width, image_height)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-top-left-radius: 9px;
                border-top-right-radius: 9px;
                border: none;
            }
        """)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        
        # Load image or show placeholder
        self.load_image()
        layout.addWidget(self.image_label)
        
        # Content section (responsive height)
        content_widget = QWidget()
        content_widget.setFixedSize(content_width, content_height)
        content_widget.setStyleSheet("QWidget { border: none; background-color: #1a1a1a; }")
        content_layout = QVBoxLayout(content_widget)
        
        # Responsive margins and spacing based on card size
        margin_size = max(10, int(content_width * 0.04))  # 4% of width, minimum 10px
        spacing_size = max(8, int(content_height * 0.06))  # 6% of height, minimum 8px
        
        content_layout.setContentsMargins(margin_size, margin_size, margin_size, margin_size)
        content_layout.setSpacing(spacing_size)
        
        # Camera name and ID row
        name_id_layout = QHBoxLayout()
        name_id_layout.setContentsMargins(0, 0, 0, 0)
        
        # Responsive font sizes
        name_font_size = max(12, int(content_width * 0.035))  # 3.5% of width
        id_font_size = max(10, int(content_width * 0.03))     # 3% of width
        
        name_label = QLabel(self.camera_name)
        name_label.setFont(QFont("Arial", name_font_size, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #ffffff;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        id_label = QLabel(f"#{self.camera_id}")
        id_label.setFont(QFont("Arial", id_font_size))
        id_label.setStyleSheet("color: #cccccc; margin-left: 5px;")
        
        name_id_layout.addStretch()
        name_id_layout.addWidget(name_label)
        name_id_layout.addWidget(id_label)
        name_id_layout.addStretch()
        
        content_layout.addLayout(name_id_layout)
        
        # Location row
        location_layout = QHBoxLayout()
        location_layout.setContentsMargins(0, 0, 0, 0)
        
        location_font_size = max(9, int(content_width * 0.028))  # 2.8% of width
        
        # Location icon (using text for now, can be replaced with actual icon)
        location_icon = QLabel("📍")
        location_icon.setFont(QFont("Arial", location_font_size))
        location_icon.setFixedSize(max(16, int(content_width * 0.05)), max(16, int(content_width * 0.05)))
        
        location_label = QLabel(self.location)
        location_label.setFont(QFont("Arial", 11))
        location_label.setStyleSheet("color: #cccccc;")
        
        location_layout.addWidget(location_icon)
        location_layout.addWidget(location_label)
        location_layout.addStretch()
        
        content_layout.addLayout(location_layout)
        
        # Camera status row
        camera_status_layout = QHBoxLayout()
        camera_status_layout.setContentsMargins(0, 0, 0, 0)
        
        camera_status_label = QLabel("Camera:")
        camera_status_label.setFont(QFont("Arial", 10))
        camera_status_label.setStyleSheet("color: #cccccc;")
        
        camera_status_circle = QLabel()
        camera_status_circle.setFixedSize(12, 12)
        camera_status_circle.setStyleSheet(self.get_status_circle_style(self.camera_status))
        
        camera_status_text = QLabel(self.get_status_text(self.camera_status))
        camera_status_text.setFont(QFont("Arial", 10))
        camera_status_text.setStyleSheet("color: #ffffff; margin-left: 5px;")
        
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
        parking_status_label.setStyleSheet("color: #cccccc;")
        
        parking_status_circle = QLabel()
        parking_status_circle.setFixedSize(12, 12)
        parking_status_circle.setStyleSheet(self.get_parking_status_circle_style(self.parking_status))
        
        parking_status_text = QLabel(self.get_parking_status_text(self.parking_status))
        parking_status_text.setFont(QFont("Arial", 10))
        parking_status_text.setStyleSheet("color: #ffffff; margin-left: 5px;")
        
        parking_status_layout.addWidget(parking_status_label)
        parking_status_layout.addWidget(parking_status_circle)
        parking_status_layout.addWidget(parking_status_text)
        parking_status_layout.addStretch()
        
        content_layout.addLayout(parking_status_layout)
        
        layout.addWidget(content_widget)
        
    def load_image(self):
        """Load camera image or show placeholder"""
        # First try to load from saved image path
        if self.image_path and os.path.exists(self.image_path):
            try:
                pixmap = QPixmap(self.image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(314, 220, Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                                Qt.TransformationMode.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)
                    print(f"✓ Successfully loaded image from {self.image_path}")
                    return
                else:
                    print(f"✗ Failed to load image - pixmap is null: {self.image_path}")
            except Exception as e:
                print(f"✗ Error loading image from {self.image_path}: {e}")
        else:
            print(f"✗ Image path not valid: {self.image_path}")
        
        # Show placeholder if image loading failed
        print("Loading placeholder image...")
        self.show_placeholder()
    
    def show_placeholder(self):
        """Show placeholder when no image is available"""
        self.image_label.setText("📷\nNo Image")
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-top-left-radius: 9px;
                border-top-right-radius: 9px;
                border: none;
                color: #ffffff;
                font-size: 24px;
            }
        """)
    
    def get_status_circle_style(self, status):
        """Get CSS style for camera status circle"""
        colors = {
            CameraStatus.WORKING.value: "#00ff00",      # Green
            CameraStatus.NOT_WORKING.value: "#ff0000",  # Red
            CameraStatus.ERROR.value: "#ff9900"         # Orange
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
            ParkingStatus.AVAILABLE.value: "#00ff00",    # Green
            ParkingStatus.OCCUPIED.value: "#ff0000",     # Red
            ParkingStatus.UNKNOWN.value: "#ff9900"       # Orange
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
            CameraStatus.WORKING.value: "Working",
            CameraStatus.NOT_WORKING.value: "Not Working",
            CameraStatus.ERROR.value: "Error"
        }
        return texts.get(status, "Unknown")
    
    def get_parking_status_text(self, status):
        """Get display text for parking status"""
        texts = {
            ParkingStatus.AVAILABLE.value: "Available",
            ParkingStatus.OCCUPIED.value: "Car Parking",
            ParkingStatus.UNKNOWN.value: "Unknown"
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
    def __init__(self, cards_per_row=2, card_size=(400, 480)):
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
        self.setStyleSheet("QWidget { background-color: #1a1a1a; }")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        label = QLabel("Camera Monitor Cards")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                margin-top: 5px;
                margin-bottom: 15px;
            }
        """)

        self.main_layout.addWidget(label)
        
        # Create scroll area for camera cards
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Set proper size policy for scroll area - remove minimum height restriction
        from PyQt6.QtWidgets import QSizePolicy
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #666666;
                border-radius: 8px;
                background-color: transparent;
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
            QScrollBar:horizontal {
                background-color: #1a1a1a;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #4a9eff;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #3a8eef;
            }
        """)
        
        # Add the camera cards
        self.add_camera_cards()
        
        # Add scroll area to main layout
        self.main_layout.addWidget(self.scroll_area, 1)

    def add_camera_cards(self):
        """Add camera cards in a scrollable area with responsive centering"""
        if not self.cameras:
            QMessageBox.warning(self, "No Cameras", "No camera data available to display.")
            return
        
        # Create content widget for cards
        content_widget = QWidget()
        content_widget.setStyleSheet("QWidget { background-color: #1a1a1a; }")
        from PyQt6.QtWidgets import QSizePolicy
        content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(30)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Create rows for cards
        current_row_layout = None
        
        for i, camera_data in enumerate(self.cameras):
            # Create new row layout if needed
            if i % self.cards_per_row == 0:
                current_row_layout = QHBoxLayout()
                current_row_layout.setSpacing(30)
                content_layout.addLayout(current_row_layout)
            
            # Create camera card
            card = CamCard(
                camera_name=camera_data["camera_name"],
                camera_id=camera_data["camera_id"],
                location=camera_data["location"],
                camera_status=camera_data["camera_status"],
                parking_status=camera_data["parking_status"],
                video_source=camera_data["video_source"],
                image_path=camera_data.get("image_path", ""),  # Pass the image path
                card_size=self.card_size
            )
            
            # Connect card click signal
            card.card_clicked.connect(self.on_camera_card_clicked)
            
            # Add card to current row
            current_row_layout.addWidget(card)
        
        # Add stretch to the last row if it's not full
        if len(self.cameras) % self.cards_per_row != 0:
            current_row_layout.addStretch()

        # Don't add stretch at the bottom - let content determine its own height
        # This allows proper scrolling when content exceeds available space
        
        # Set scroll area content
        self.scroll_area.setWidget(content_widget)

    def update_camera_cards(self):
        """Update camera cards with latest data"""
        self.config_manager.load_config()
        self.cameras = self.config_manager.get_all_cameras()
        
        # Clear existing cards
        for i in reversed(range(self.scroll_area.widget().layout().count())):
            item = self.scroll_area.widget().layout().itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        # Re-add camera cards
        self.add_camera_cards()

    def on_camera_card_clicked(self, camera_id):
        """Handle camera card click events"""
        print(f"CamCardFrame: Camera card clicked: {camera_id}")
        self.card_clicked.emit(camera_id)