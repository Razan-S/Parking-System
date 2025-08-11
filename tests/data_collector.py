"""
Data Collection Script
Automatically captures frames from CCTV, runs CPU/GPU detection, and saves results to CSV.
"""

import sys
import os
# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from timer_detection import TimerDetectionModule
from src.config.utils import CameraConfigManager
from src.enums import ParkingStatus, CameraStatus
from src.utils import capture_one_frame_silent
import torch
import pandas as pd
import cv2
import numpy as np
import time
from datetime import datetime
from shapely.geometry import Polygon


class DataCollector:
    def __init__(self, camera_id='CAM_001'):
        self.camera_id = camera_id
        self.detector_cpu = TimerDetectionModule(use_gpu=False)
        
        # Try to initialize GPU detector
        self.detector_gpu = None
        if torch.cuda.is_available():
            try:
                self.detector_gpu = TimerDetectionModule(use_gpu=True)
                print(f"✅ GPU detector initialized on {self.detector_gpu.device}")
            except Exception as e:
                print(f"⚠️ Failed to initialize GPU detector: {e}")
                self.detector_gpu = None
        else:
            print("❌ CUDA not available, GPU detector not initialized")
        
        # Load camera configuration
        self.cam_config = CameraConfigManager()
        self.cam = self.cam_config.get_camera_by_id(camera_id)
        if not self.cam:
            raise ValueError(f"Camera {camera_id} not found in configuration")
        
        self.detection_zones_json = self.cam.get('detection_zones', None)
        
        # Create images directory inside tests folder
        self.images_dir = os.path.join('tests', f'collected_images_{datetime.now().strftime("%Y%m%d")}')
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Create results directory for CSV files
        self.results_dir = os.path.join('tests', 'results')
        os.makedirs(self.results_dir, exist_ok=True)
        
        print(f"Data Collector initialized for camera: {camera_id}")
        print(f"Images will be saved to: {self.images_dir}")
        print(f"CSV results will be saved to: {self.results_dir}")

    def detection_with_cpu(self, frame):
        """Perform detection using CPU"""
        return self.detector_cpu.run(frame, self.detection_zones_json)

    def detection_with_gpu(self, frame):
        """Perform detection using GPU"""
        if self.detector_gpu is None:
            return {
                "status": "unknown",
                "processing_times": {
                    "prediction": 0,
                    "box_extraction": 0,
                    "segmentation": 0,
                    "total_time": 0
                }
            }
        return self.detector_gpu.run(frame, self.detection_zones_json)

    def save_frame(self, frame, frame_num):
        """Save frame as JPEG image"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"frame_{frame_num:04d}_{timestamp}.jpg"
        filepath = os.path.join(self.images_dir, filename)
        
        cv2.imwrite(filepath, frame)
        return filepath

    def collect_data(self, num_frames=100, delay_between_frames=1.0):
        """
        Collect data by capturing frames and running detections
        
        Args:
            num_frames (int): Number of frames to collect
            delay_between_frames (float): Delay in seconds between frame captures
        """
        print(f"Starting data collection for {num_frames} frames...")
        print(f"Delay between frames: {delay_between_frames} seconds")
        
        # Initialize DataFrame
        df = pd.DataFrame(columns=[
            'Frame', 'CPU_Result', 'GPU_Result', 
            'CPU_prediction_time', 'CPU_box_extraction_time', 'CPU_segmentation_time', 'CPU_total_time', 'CPU_FPS',
            'GPU_prediction_time', 'GPU_box_extraction_time', 'GPU_segmentation_time', 'GPU_total_time', 'GPU_FPS',
            'Manual_Result', 'Image_Path', 'Timestamp'
        ])
        
        successful_frames = 0
        
        for i in range(num_frames):
            print(f"\nProcessing frame {i+1}/{num_frames}")
            
            try:
                # Capture frame
                frame = capture_one_frame_silent(self.camera_id)
                
                if frame is None:
                    print(f"Failed to capture frame {i+1}")
                    continue
                
                # Save frame
                image_path = self.save_frame(frame, i+1)
                print(f"Frame saved to: {image_path}")
                
                # Run CPU detection
                print("Running CPU detection...")
                cpu_result = self.detection_with_cpu(frame)
                cpu_processing_result = cpu_result.get('processing_times', {})

                gpu_result = {'status': 'N/A', 'processing_times': {}}
                gpu_processing_result = {}

                if self.detector_gpu is None:
                    print("GPU detector not available, skipping GPU detection.")
                else:
                    # Run GPU detection
                    print("Running GPU detection...")
                    gpu_result = self.detection_with_gpu(frame)
                    gpu_processing_result = gpu_result.get('processing_times', {})

                # Add to DataFrame
                new_row = pd.DataFrame({
                    'Frame': [i+1],
                    'CPU_Result': [cpu_result.get('status', 'unknown')],
                    'GPU_Result': [gpu_result.get('status', 'unknown')],
                    'CPU_prediction_time': [cpu_processing_result.get('prediction', 0)],
                    'CPU_box_extraction_time': [cpu_processing_result.get('box_extraction', 0)],
                    'CPU_segmentation_time': [cpu_processing_result.get('segmentation', 0)],
                    'CPU_total_time': [cpu_processing_result.get('total_time', 0)],
                    'CPU_FPS': [1 / cpu_processing_result.get('total_time', 1) if cpu_processing_result.get('total_time', 0) > 0 else 0],
                    'GPU_prediction_time': [gpu_processing_result.get('prediction', 0)],
                    'GPU_box_extraction_time': [gpu_processing_result.get('box_extraction', 0)],
                    'GPU_segmentation_time': [gpu_processing_result.get('segmentation', 0)],
                    'GPU_total_time': [gpu_processing_result.get('total_time', 0)],
                    'GPU_FPS': [1 / gpu_processing_result.get('total_time', 1) if gpu_processing_result.get('total_time', 0) > 0 else 0],
                    'Manual_Result': [None],  # To be filled by validation app
                    'Image_Path': [image_path],
                    'Timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                })
                
                df = pd.concat([df, new_row], ignore_index=True)
                successful_frames += 1
                
                print(f"Frame {i+1} processed successfully!")
                
                # Delay between frames (except for the last frame)
                if i < num_frames - 1:
                    time.sleep(delay_between_frames)
                    
            except Exception as e:
                print(f"Error processing frame {i+1}: {e}")
                continue
        
        # Save results to the results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f'data_collection_{timestamp}.csv'
        csv_filepath = os.path.join(self.results_dir, csv_filename)
        df.to_csv(csv_filepath, index=False)
        
        print(f"\nData collection completed!")
        print(f"Successfully processed: {successful_frames}/{num_frames} frames")
        print(f"Results saved to: {csv_filepath}")
        
        return df, csv_filepath

def main():
    print("=== Parking System Data Collector ===")
    
    try:
        # Get user input
        camera_id = input("Enter camera ID (default: CAM_001): ").strip() or 'CAM_001'
        
        num_frames_input = input("Enter number of frames to collect (default: 100): ").strip()
        num_frames = int(num_frames_input) if num_frames_input else 100
        
        delay_input = input("Enter delay between frames in seconds (default: 1.0): ").strip()
        delay = float(delay_input) if delay_input else 1.0
        
        # Initialize collector
        collector = DataCollector(camera_id)
        
        # Start collection
        df, csv_filename = collector.collect_data(num_frames, delay)
        
        print(f"\nDataFrame Preview:")
        print(df.head())
        
    except KeyboardInterrupt:
        print("\nData collection interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
