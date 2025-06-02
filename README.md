# Parking-System

An AI-powered parking management system that uses computer vision to detect whether parking slots are occupied or vacant. The system provides real-time monitoring through a user-friendly graphical interface built with PyQt6.

## Features

- **Real-time Parking Detection**: Uses computer vision algorithms to analyze parking spaces
- **AI-Powered Analysis**: Employs artificial intelligence to accurately determine slot occupancy
- **Intuitive GUI**: Clean and responsive interface built with PyQt6
- **Visual Feedback**: Real-time display of parking lot status with visual indicators
- **Image Processing**: Advanced image analysis using OpenCV and related libraries

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Parking-System
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your specific configuration
   ```

## Usage

### Running the Application

To start the parking system with the GUI:

```bash
python -m src
```

This will launch the main application with the graphical interface where you can:
- Monitor parking spaces in real-time
- View occupancy status
- Analyze parking patterns

### Running Tests

To run the test suite:

```bash
python -m tests
```