import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from src.gui.segmentor import RoadSegmenterGUI
from src.gui.window import Window

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # palette = QPalette()
    # palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    # palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
    # app.setPalette(palette)
    
    # window = RoadSegmenterGUI(video_path="video/test.MP4")
    # window.show()

    cameras = [
        {"name": "Camera 1", "status": "online"},
        {"name": "Camera 2", "status": "offline"},
        {"name": "Camera 3", "status": "error"},
        # Add more cameras as needed
    ]

    window = Window(cameras=cameras)
    window.show()

    
    app.exec()
    
    # # After the application is closed, you can retrieve submitted coordinates
    # frame, coordinates = window.get_submitted_coordinates()
    # print(frame.shape) # height, width, channels (1080, 1920, 3)
    # print(coordinates) # example: [{'id': 1, 'coordinates': [(834, 681), (750, 442), (1081, 455)]}]

if __name__ == "__main__":
    main()