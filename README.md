
# Parking-System

An AI-powered parking management system that uses computer vision to detect parking slot occupancy, with a real-time PyQt6 GUI.

## Features

- **Real-time Parking Detection**: Computer vision for parking space analysis
- **AI-Powered Analysis**: Deep learning and ONNX/YOLO support
- **Intuitive GUI**: PyQt6-based, user-friendly interface
- **Visual Feedback**: Live status and visual indicators
- **Image Processing**: OpenCV and advanced image analysis

## Requirements

- **Python 3.10** (strictly required; newer/older versions may not work)
- pip (Python package installer)

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd Parking-System
```

### 2. Create and activate a virtual environment (Python 3.10)
On Windows:
```powershell
py -3.10 -m venv venv
venv\Scripts\activate
```
On macOS/Linux:
```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 3. Install PyTorch (CUDA 12.1, or your CUDA version)
Get the correct command from https://pytorch.org/get-started/locally/ or use:
```powershell
pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
```

### 4. Install remaining dependencies
```powershell
pip install -r requirements.txt
```

### 5. Set up environment variables
If you have a `.env.example` file:
```powershell
copy .env.example .env
# Edit .env with your configuration
```
If not, create a `.env` file as needed for your secrets/config.

## Usage

### Running the Application
```powershell
python -m src
```
This launches the GUI for real-time monitoring and analysis.

### Running Tests
```powershell
python -m tests
```

## Notes

- **Python 3.10 is required.** Other versions may cause dependency errors.
- **Do not overwrite requirements.txt with pip freeze** unless you know what you are doing.
- If you see `ModuleNotFoundError`, ensure all dependencies are installed and your virtual environment is activated.