# from ultralytics import YOLO
# import numpy as np
# from shapely.geometry import Polygon, box
# from src.enums import ParkingStatus
# import torch
# import os

# class DetectionModule:
#     def __init__(self):
#         try:
#             # Check if we have a GPU available and get device info
#             device_info = self._get_device_info()
#             print(f"Using device: {device_info['name']} (Type: {device_info['type']})")
            
#             # Try to load TensorRT engine first, fallback to ONNX/PT if it fails
#             model_loaded = False
            
#             # Try TensorRT engine
#             if os.path.exists("yolo12n.engine"):
#                 try:
#                     print("Loading yolo12n.engine for TensorRT inference...")
#                     self.model = YOLO("yolo12n.engine", task="detect", verbose=True)
#                     model_loaded = True
#                     print("TensorRT engine loaded successfully.")
#                 except Exception as e:
#                     print(f"TensorRT engine failed to load: {e}")
#                     print("Note: TensorRT engines are device-specific. You may need to rebuild the engine for your GPU.")
            
#             # Fallback to ONNX model
#             if not model_loaded and os.path.exists("yolo12n.onnx"):
#                 try:
#                     print("Falling back to ONNX model...")
#                     self.model = YOLO("yolo12n.onnx", task="detect", verbose=True)
#                     model_loaded = True
#                     print("ONNX model loaded successfully.")
#                 except Exception as e:
#                     print(f"ONNX model failed to load: {e}")
            
#             # Fallback to PyTorch model
#             if not model_loaded and os.path.exists("yolo12n.pt"):
#                 try:
#                     print("Falling back to PyTorch model...")
#                     self.model = YOLO("yolo12n.pt", task="detect", verbose=True)
#                     model_loaded = True
#                     print("PyTorch model loaded successfully.")
#                 except Exception as e:
#                     print(f"PyTorch model failed to load: {e}")
            
#             if not model_loaded:
#                 raise Exception("No valid model file found or all models failed to load")
            
#             # Warmup to load model
#             dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
#             self.model(dummy_image, verbose=False)

#             print("Model initialized successfully.")
            
#         except Exception as e:
#             print(f"Error initializing model: {e}")
#             self.model = None
    
#     def _get_device_info(self):
#         """Get information about the current device"""
#         if torch.cuda.is_available():
#             device_name = torch.cuda.get_device_name(0)
#             device_type = "CUDA"
#             compute_capability = torch.cuda.get_device_capability(0)
#             return {
#                 "name": device_name,
#                 "type": device_type,
#                 "compute_capability": compute_capability
#             }
#         else:
#             return {
#                 "name": "CPU",
#                 "type": "CPU",
#                 "compute_capability": None
#             }

#     def run(self, frame: np.ndarray, coordinates: list) -> str:
#         """
#         Detect objects in the given frame and check if they intersect with specified regions.

#         Args:
#             frame (np.ndarray): The input image frame.
#             coordinates (list): List of dicts like:
#                 [{"id": 1, "coordinates": [[x1, y1], [x2, y2], ...]}, ...]

#         Returns:
#             str: Parking status (AVAILABLE, OCCUPIED, UNKNOWN).
#         """
#         if self.model is None:
#             print("Model not loaded properly.")
#             return ParkingStatus.UNKNOWN.value

#         try:
#             # Use real YOLO detection
#             results = self.model(frame, verbose=False)
#             detections = results[0].boxes.xyxy.cpu().numpy()  # Detected boxes: [x1, y1, x2, y2]

#             # Build polygons for specified regions
#             region_polygons = []
#             for region in coordinates:
#                 points = [(point['x'], point['y']) for point in region["polygon_points"]]
#                 poly = Polygon(points)
                
#                 if not poly.is_valid:
#                     print(f"Warning: Invalid polygon for region ID {region['id']}")
#                     continue
#                 region_polygons.append({"id": region['zone_id'], "coordinates": poly})

#             # Check if any detection intersects with any region
#             # Check each detection against all regions
#             for det_box in detections:
#                 x1, y1, x2, y2 = det_box
#                 det_poly = box(x1, y1, x2, y2)  # Convert to shapely box (polygon)

#                 # Check intersection with all regions
#                 for region_poly in region_polygons:
#                     if det_poly.intersects(region_poly["coordinates"]):
#                         return ParkingStatus.OCCUPIED.value
                    
#             return ParkingStatus.AVAILABLE.value

#         except Exception as e:
#             print(f"Error during detection: {e}")
#             return ParkingStatus.UNKNOWN.value

from ultralytics import YOLO
import numpy as np
from shapely.geometry import Polygon, box
from src.enums import ParkingStatus
import torch
import os

class DetectionModule:
    def __init__(self, use_gpu: bool = False):
        """
        Initialize the YOLO detection model, choosing CPU or GPU.

        Args:
            use_gpu (bool): If True, attempt to load on GPU (CUDA). If CUDA isn’t
                            available or use_gpu=False, falls back to CPU.
        """
        # Decide which device to use
        if use_gpu and torch.cuda.is_available():
            self.device = "cuda:0"  # first CUDA GPU
            print(f"CUDA is available. Using GPU device {self.device}.")
        else:
            self.device = "cpu"
            print("Using CPU for inference.")

        # List of (model_path, description) in preferred load order
        # For CPU mode, prioritize PyTorch model as it has fewer compatibility issues
        if self.device == "cpu":
            model_paths = [
                "yolo12n.pt",      # PyTorch (most compatible)
                "yolo12n.onnx"     # ONNX (CPU compatible but might have issues)
            ]
        else:
            model_paths = [
                "yolo12n.engine",  # TensorRT (GPU only)
                "yolo12n.pt",      # PyTorch
                "yolo12n.onnx"     # ONNX
            ]

        self.model = None
        # Try loading each model in turn
        for path in model_paths:
            if os.path.exists(path):
                try:
                    print(f"Loading model from '{path}'...")
                    # Load model without device parameter
                    self.model = YOLO(path, task="detect", verbose=False)
                    print(f"Successfully loaded '{path}'.")
                    break
                except Exception as e:
                    print(f"Failed to load '{path}': {e}")

        if self.model is None:
            raise RuntimeError(
                "No valid YOLO model file found or all loads failed. "
                "Make sure you have one of: yolo12n.engine, yolo12n.onnx, or yolo12n.pt"
            )

        # Warm up the model with a dummy image on the desired device
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        # Run inference with device specification in the predict method
        _ = self.model.predict(dummy, device=self.device, verbose=False)
        print(f"Model warm-up complete on device '{self.device}'.")

    def run(self, frame: np.ndarray, coordinates: list) -> str:
        """
        Detect objects in the frame and determine parking status.

        Args:
            frame (np.ndarray): BGR or RGB image array.
            coordinates (list of dict): Each dict should have:
                - "zone_id": unique identifier for the region
                - "polygon_points": list of {"x": x_i, "y": y_i} points

        Returns:
            str: One of ParkingStatus.AVAILABLE.value,
                 ParkingStatus.OCCUPIED.value, or
                 ParkingStatus.UNKNOWN.value
        """
        if self.model is None:
            return ParkingStatus.UNKNOWN.value

        try:
            # Run inference with device specification
            results = self.model.predict(frame, device=self.device, verbose=False)
            boxes = results[0].boxes.xyxy.cpu().numpy()  # shape: (N,4)

            # Build shapely polygons for each parking zone
            zones = []
            for region in coordinates:
                pts = [(pt['x'], pt['y']) for pt in region["polygon_points"]]
                poly = Polygon(pts)
                if not poly.is_valid:
                    print(f"Warning: invalid polygon for zone {region['zone_id']}")
                    continue
                zones.append((region['zone_id'], poly))

            # Check each detected box against each zone polygon
            for x1, y1, x2, y2 in boxes:
                det_poly = box(x1, y1, x2, y2)
                for zone_id, zone_poly in zones:
                    if det_poly.intersects(zone_poly):
                        return ParkingStatus.OCCUPIED.value

            # No intersections → available
            return ParkingStatus.AVAILABLE.value

        except Exception as e:
            print(f"Error during detection: {e}")
            return ParkingStatus.UNKNOWN.value


# if __name__ == "__main__":
#     # Example usage
#     detector_cpu = DetectionModule(use_gpu=False)
#     fake_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
#     fake_zones = [
#         {
#             "zone_id": 1,
#             "polygon_points": [
#                 {"x": 100, "y": 100},
#                 {"x": 300, "y": 100},
#                 {"x": 300, "y": 300},
#                 {"x": 100, "y": 300},
#             ]
#         },
#         # add more zones if needed...
#     ]

#     status = detector_cpu.run(fake_frame, fake_zones)
#     print(f"Parking status: {status}")