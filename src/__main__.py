import sys
import os
from PyQt6.QtWidgets import QApplication
from src.gui.window import Window

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Check for GPU usage - can be set via command line arg or environment variable
    use_gpu = False
    if "--gpu" in sys.argv or os.environ.get("USE_GPU", "").lower() in ["true", "1", "yes"]:
        use_gpu = True
        print("GPU mode enabled")
    else:
        print("CPU mode enabled (use --gpu flag or set USE_GPU=true for GPU mode)")

    # Create window - will load from JSON configuration by default
    window = Window(use_gpu=use_gpu)
    window.show()
    app.exec()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()