from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
import cv2 as cv

class VideoFrameWidget(QLabel):
    coordinates_updated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.coordinates = []
        self.frame = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.show_connections = True  # Flag to toggle line display
        self.saved_polygons = {}  # Store saved polygons with their IDs and types
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QLabel {
                background-color: #404040;
                border: 2px solid #555;
                border-radius: 8px;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Load a frame to begin segmentation")
    
    def set_frame(self, frame):
        self.frame = frame.copy()
        self.coordinates = []
        self.update_display()
    
    def update_display(self):
        if self.frame is None:
            return

        # Create display frame
        display_frame = self.frame.copy()

        # Draw saved polygons first (underneath current drawing)
        import numpy as np
        for polygon in self.saved_polygons.values():
            coords = polygon['coordinates']
            color = polygon['color']
            
            if len(coords) >= 3:
                # Create semi-transparent overlay for saved polygons
                overlay = display_frame.copy()
                contour = np.array([coords], dtype=np.int32)
                cv.drawContours(overlay, contour, -1, color, thickness=cv.FILLED)
                
                # Blend with original (30% transparency)
                cv.addWeighted(overlay, 0.3, display_frame, 0.7, 0, display_frame)
                
                # Draw polygon border with darker version of the color
                border_color = tuple(int(c * 0.8) for c in color)
                cv.drawContours(display_frame, contour, -1, border_color, thickness=2)

        # Draw current polygon being drawn
        if len(self.coordinates) >= 3:
            # Create semi-transparent overlay
            overlay = display_frame.copy()
            contour = np.array([self.coordinates], dtype=np.int32)
            cv.drawContours(overlay, contour, -1, (0, 255, 0), thickness=cv.FILLED)
            
            # Blend with original (30% transparency)
            cv.addWeighted(overlay, 0.3, display_frame, 0.7, 0, display_frame)
            
            # Draw polygon border
            cv.drawContours(display_frame, contour, -1, (0, 200, 0), thickness=2)

        # Draw connecting lines for current polygon
        if self.show_connections and len(self.coordinates) > 1:
            for i in range(len(self.coordinates) - 1):
                pt1 = (int(self.coordinates[i][0]), int(self.coordinates[i][1]))
                pt2 = (int(self.coordinates[i + 1][0]), int(self.coordinates[i + 1][1]))
                cv.line(display_frame, pt1, pt2, (255, 0, 0), 2)
            
            # Close polygon
            if len(self.coordinates) >= 3:
                pt1 = (int(self.coordinates[-1][0]), int(self.coordinates[-1][1]))
                pt2 = (int(self.coordinates[0][0]), int(self.coordinates[0][1]))
                cv.line(display_frame, pt1, pt2, (255, 0, 0), 2)

        # Draw points for current polygon
        for i, (x, y) in enumerate(self.coordinates):
            center = (int(x), int(y))
            cv.circle(display_frame, center, 8, (0, 255, 0), -1)  # Green filled circle
            cv.circle(display_frame, center, 8, (255, 255, 255), 2)  # White border

        # Convert to Qt format
        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()

        # Scale to fit widget
        widget_size = self.size()
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(widget_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # Calculate scale factor and offset for coordinate mapping
        self.scale_factor = min(widget_size.width() / width, widget_size.height() / height)
        scaled_width = int(width * self.scale_factor)
        scaled_height = int(height * self.scale_factor)
        self.offset_x = (widget_size.width() - scaled_width) // 2
        self.offset_y = (widget_size.height() - scaled_height) // 2

        self.setPixmap(scaled_pixmap)

    def mousePressEvent(self, event):
        if self.frame is None:
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert widget coordinates to image coordinates
            widget_x = event.position().x() - self.offset_x
            widget_y = event.position().y() - self.offset_y
            
            if widget_x >= 0 and widget_y >= 0:
                image_x = widget_x / self.scale_factor
                image_y = widget_y / self.scale_factor
                
                # Check if click is within image bounds
                if 0 <= image_x < self.frame.shape[1] and 0 <= image_y < self.frame.shape[0]:
                    self.coordinates.append((int(image_x), int(image_y)))
                    self.coordinates_updated.emit(self.coordinates)
                    self.update_display()
    
    def clear_coordinates(self):
        self.coordinates = []
        self.coordinates_updated.emit(self.coordinates)
        self.update_display()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.frame is not None:
            self.update_display()
    
    def add_existing_polygon(self, coordinates, polygon_id):
        """Add an existing polygon (orange color) to be displayed"""
        self.saved_polygons[polygon_id] = {
            'coordinates': coordinates,
            'type': 'existing',
            'color': (255, 165, 0)  # Orange color for existing
        }
        self.update_display()
    
    def add_new_polygon(self, coordinates, polygon_id):
        """Add a new polygon (green color) to be displayed"""
        self.saved_polygons[polygon_id] = {
            'coordinates': coordinates,
            'type': 'new',
            'color': (0, 255, 0)  # Green color for new
        }
        self.update_display()
    
    def remove_polygon(self, polygon_id):
        """Remove a polygon by its ID"""
        if polygon_id in self.saved_polygons:
            del self.saved_polygons[polygon_id]
            self.update_display()
    
    def clear_all_polygons(self):
        """Clear all saved polygons"""
        self.saved_polygons = {}
        self.update_display()

class CoordinateCard(QFrame):
    card_deleted = pyqtSignal(int)
    
    def __init__(self, frame_id, coordinates):
        super().__init__()
        self.frame_id = frame_id
        self.coordinates = coordinates
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #3a3a3a;
                border: 1px solid #555;
                border-radius: 8px;
                margin: 5px;
                padding: 10px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with title and delete button
        header_layout = QHBoxLayout()
        
        # Frame title
        title = QLabel(f"Frame {self.frame_id}")
        title.setStyleSheet("""
            QLabel {
                color: #0d7377;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 5px;
            }
        """)
        header_layout.addWidget(title)
        
        # Delete button
        delete_btn = DarkButton("🗑️", danger=True)
        delete_btn.setFixedSize(30, 30)
        delete_btn.setToolTip("Delete this frame")
        delete_btn.clicked.connect(self.delete_card)
        header_layout.addWidget(delete_btn)
        
        main_layout.addLayout(header_layout)
        
        # Coordinates
        coords_text = ""
        for i, (x, y) in enumerate(self.coordinates):
            coords_text += f"Point {i+1}: ({x}, {y})\n"
        
        coords_label = QLabel(coords_text.strip())
        coords_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        main_layout.addWidget(coords_label)
    
    def delete_card(self):
        # Emit signal with frame_id to parent
        self.card_deleted.emit(self.frame_id)

class DarkButton(QPushButton):
    def __init__(self, text, primary=False, danger=False):
        super().__init__(text)
        self.primary = primary
        self.danger = danger
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
    
    def update_style(self):
        if self.danger:
            self.setStyleSheet("""
                QPushButton {
                    background: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #e85a6b;
                }
                QPushButton:pressed {
                    background: #c82333;
                }
                QPushButton:disabled {
                    background: #555;
                    color: #888;
                }
            """)
        elif self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background: #0d7377;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #14a085;
                }
                QPushButton:pressed {
                    background: #0a5d61;
                }
                QPushButton:disabled {
                    background: #555;
                    color: #888;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: #404040;
                    color: #e0e0e0;
                    border: 1px solid #555;
                    border-radius: 6px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #4a4a4a;
                    border-color: #666;
                }
                QPushButton:pressed {
                    background: #363636;
                }
            """)