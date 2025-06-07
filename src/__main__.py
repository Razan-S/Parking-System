import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from src.gui.segmentor import RoadSegmenterGUI

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
    app.setPalette(palette)
    
    window = RoadSegmenterGUI(video_path="video/south_1-out.avi")
    window.show()
    
    app.exec()
    
    # After the application is closed, you can retrieve submitted coordinates
    coordinates = window.get_submitted_coordinates()
    print("Submitted coordinates:", coordinates)

if __name__ == "__main__":
    main()