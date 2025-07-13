from ultralytics import YOLO
import numpy as np
from shapely.geometry import Polygon, box
from src.enums import ParkingStatus
import torch
import os

class DetectionModule:
    def __init__(self):
        try:
            # Check if we have a GPU available and get device info
            device_info = self._get_device_info()
            print(f"Using device: {device_info['name']} (Type: {device_info['type']})")
            
            # Try to load TensorRT engine first, fallback to ONNX/PT if it fails
            model_loaded = False
            
            # Try TensorRT engine
            if os.path.exists("yolo12n.engine"):
                try:
                    print("Loading yolo12n.engine for TensorRT inference...")
                    self.model = YOLO("yolo12n.engine", task="detect", verbose=True)
                    model_loaded = True
                    print("TensorRT engine loaded successfully.")
                except Exception as e:
                    print(f"TensorRT engine failed to load: {e}")
                    print("Note: TensorRT engines are device-specific. You may need to rebuild the engine for your GPU.")
            
            # Fallback to ONNX model
            if not model_loaded and os.path.exists("yolo12n.onnx"):
                try:
                    print("Falling back to ONNX model...")
                    self.model = YOLO("yolo12n.onnx", task="detect", verbose=True)
                    model_loaded = True
                    print("ONNX model loaded successfully.")
                except Exception as e:
                    print(f"ONNX model failed to load: {e}")
            
            # Fallback to PyTorch model
            if not model_loaded and os.path.exists("yolo12n.pt"):
                try:
                    print("Falling back to PyTorch model...")
                    self.model = YOLO("yolo12n.pt", task="detect", verbose=True)
                    model_loaded = True
                    print("PyTorch model loaded successfully.")
                except Exception as e:
                    print(f"PyTorch model failed to load: {e}")
            
            if not model_loaded:
                raise Exception("No valid model file found or all models failed to load")
            
            # Warmup to load model
            dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model(dummy_image, verbose=False)

            print("Model initialized successfully.")
            
        except Exception as e:
            print(f"Error initializing model: {e}")
            self.model = None
    
    def _get_device_info(self):
        """Get information about the current device"""
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            device_type = "CUDA"
            compute_capability = torch.cuda.get_device_capability(0)
            return {
                "name": device_name,
                "type": device_type,
                "compute_capability": compute_capability
            }
        else:
            return {
                "name": "CPU",
                "type": "CPU",
                "compute_capability": None
            }

    def run(self, frame: np.ndarray, coordinates: list) -> str:
        """
        Detect objects in the given frame and check if they intersect with specified regions.

        Args:
            frame (np.ndarray): The input image frame.
            coordinates (list): List of dicts like:
                [{"id": 1, "coordinates": [[x1, y1], [x2, y2], ...]}, ...]

        Returns:
            str: Parking status (AVAILABLE, OCCUPIED, UNKNOWN).
        """
        if self.model is None:
            print("Model not loaded properly.")
            return ParkingStatus.UNKNOWN.value

        try:
            # Use real YOLO detection
            results = self.model(frame, verbose=False)
            detections = results[0].boxes.xyxy.cpu().numpy()  # Detected boxes: [x1, y1, x2, y2]

            # Build polygons for specified regions
            region_polygons = []
            for region in coordinates:
                points = [(point['x'], point['y']) for point in region["polygon_points"]]
                poly = Polygon(points)
                
                if not poly.is_valid:
                    print(f"Warning: Invalid polygon for region ID {region['id']}")
                    continue
                region_polygons.append({"id": region['zone_id'], "coordinates": poly})

            # Check if any detection intersects with any region
            # Check each detection against all regions
            for det_box in detections:
                x1, y1, x2, y2 = det_box
                det_poly = box(x1, y1, x2, y2)  # Convert to shapely box (polygon)

                # Check intersection with all regions
                for region_poly in region_polygons:
                    if det_poly.intersects(region_poly["coordinates"]):
                        return ParkingStatus.OCCUPIED.value
                    
            return ParkingStatus.AVAILABLE.value

        except Exception as e:
            print(f"Error during detection: {e}")
            return ParkingStatus.UNKNOWN.value