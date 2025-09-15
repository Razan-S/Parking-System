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
    camConfig = CameraConfigManager(config_file_path=r'./src/config/cameras-configuration.json')

    if detection_module.model is None:
        print("Failed to initialize detection module.")
        return

    cam_details = camConfig.get_camera_by_id('CAM_001')
    zone = cam_details.get('detection_zones', [])

    for img in os.listdir(r'./image/latest'):
        frame = cv.imread(os.path.join('./image/latest', img))

        status = detection_module.run(frame, zone)
        # print(f"Parking status for CAM_001: {status}")

        if status == "occupied":
            print(f"Parking status for CAM_001: {status}")

main()