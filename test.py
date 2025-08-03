from src.utils import capture_video, capture_one_frame, capture_one_frame_silent
from src.yolo import DetectionModule
from src.config.utils import CameraConfigManager
import cv2 as cv
import numpy as np
import os

# capture_video('CAM_001')
# capture_one_frame('CAM_001')

def main():
    # Initialize detection module
    detection_module = DetectionModule()
    camConfig = CameraConfigManager(config_file_path='src/config/mock-cameras-configuration.json')

    if detection_module.model is None:
        print("Failed to initialize detection module.")
        return

    cam_details = camConfig.get_camera_by_id('CAM_001')
    image_path = cam_details.get('image_path', 'default_image.jpg')
    zone = cam_details.get('detection_zones', [])

    if not zone:
        print("No detection zones configured for this camera.")
        return
    else: 
        print(f"Using detection zones: {zone}")

    if not os.path.exists(image_path):
        print(f"Image path does not exist: {image_path}")
        return
    
    # Load image
    frame = cv.imread(image_path)
    if frame is None:
        print(f"Failed to read image from path: {image_path}")
        return
    
    status = detection_module.run(frame, zone)
    print(f"Parking status for CAM_001: {status}")

main()