import sys
from PyQt6.QtWidgets import QApplication
from src.gui.window import Window

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Create window - will load from JSON configuration by default
    window = Window()
    window.show()
    app.exec()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()