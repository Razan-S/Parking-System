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

    # Check for GPU usage with robust error handling
    use_gpu = False
    gpu_reason = "CPU mode (default)"
    
    try:
        if "--gpu" in sys.argv:
            if torch.cuda.is_available():
                use_gpu = True
                gpu_reason = f"GPU mode (--gpu flag, CUDA available: {torch.cuda.get_device_name(0)})"
            else:
                gpu_reason = "CPU mode (--gpu flag provided but CUDA not available)"
        elif torch.cuda.is_available():
            use_gpu = True
            gpu_reason = f"GPU mode (CUDA auto-detected: {torch.cuda.get_device_name(0)})"
        else:
            gpu_reason = "CPU mode (CUDA not available)"
    except Exception as e:
        use_gpu = False
        gpu_reason = f"CPU mode (GPU detection failed: {str(e)})"
    
    print(gpu_reason)

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