import sys
import os
import torch
from PyQt6.QtWidgets import QApplication, QDialog
from src.gui.window import Window
from src.gui.GmailCard import GmailDialog
from dotenv import load_dotenv

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Illegal Parking Monitor")
    app.setApplicationDisplayName("Illegal Parking Monitor")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Parking System")
    app.setStyle('Fusion')

    # Check for GPU usage - can be set via command line arg or environment variable
    use_gpu = False
    if "--gpu" in sys.argv or os.environ.get("USE_GPU", "").lower() in ["true", "1", "yes"] or torch.cuda.is_available():
        use_gpu = True
        print("GPU mode enabled")
    else:
        print("CPU mode enabled (use --gpu flag or set USE_GPU=true for GPU mode)")

    gmail_dialog = GmailDialog()
    result = gmail_dialog.exec()
    
    if result == QDialog.DialogCode.Accepted:
        window = Window(use_gpu=use_gpu)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    main()