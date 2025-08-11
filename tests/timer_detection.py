from ultralytics import YOLO
import numpy as np
from shapely.geometry import Polygon, box
from src.enums import ParkingStatus
import torch
import os
import time

class TimerDetectionModule:
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
        # For GPU mode, prioritize models that work well with GPU
        if self.device == "cuda:0":
            model_paths = [
                "../yolo12n.pt",      # PyTorch (most reliable for GPU)
                "../yolo12n.onnx",    # ONNX (GPU compatible)
                "../yolo12n.engine",  # TensorRT (GPU only, might have compatibility issues)
                "yolo12n.pt",         # Local fallback
                "yolo12n.onnx",       # Local fallback  
                "yolo12n.engine"      # Local fallback
            ]
        else:
            model_paths = [
                "../yolo12n.pt",      # PyTorch (most compatible)
                "../yolo12n.onnx",    # ONNX (CPU compatible but might have issues)
                "yolo12n.pt",         # Local fallback
                "yolo12n.onnx"        # Local fallback
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
        
        # Verify the model is actually on the correct device
        if self.device == "cuda:0":
            try:
                # Test GPU memory allocation
                test_tensor = torch.randn(10, 10).to(self.device)
                print(f"✅ GPU test passed - tensor created on {test_tensor.device}")
            except Exception as e:
                print(f"⚠️ GPU test failed: {e}")
                self.device = "cpu"
                print("Falling back to CPU")

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
            return {
                "status": ParkingStatus.UNKNOWN.value,
                "processing_times": {
                    "prediction": 0,
                    "box_extraction": 0,
                    "segmentation": 0,
                    "total_time": 0
                }
            }

        try:
            # Run inference with device specification

            t0_pred = time.perf_counter()
            results = self.model.predict(frame, device=self.device, verbose=False)
            t1_pred = time.perf_counter()

            t0_boxes = time.perf_counter()
            boxes = results[0].boxes.xyxy.cpu().numpy()  # shape: (N,4)
            t1_boxes = time.perf_counter()

            # Build shapely polygons for each parking zone
            zones = []
            for region in coordinates:
                pts = [(pt['x'], pt['y']) for pt in region["polygon_points"]]
                poly = Polygon(pts)
                if not poly.is_valid:
                    print(f"Warning: invalid polygon for zone {region['zone_id']}")
                    continue
                zones.append((region['zone_id'], poly))

            t0_segmentation = time.perf_counter()
            # Check each detected box against each zone polygon
            for x1, y1, x2, y2 in boxes:
                det_poly = box(x1, y1, x2, y2)
                for zone_id, zone_poly in zones:
                    if det_poly.intersects(zone_poly):
                        t1_segmentation = time.perf_counter()
                        # Intersection found → occupied
                        return {
                            "status": ParkingStatus.OCCUPIED.value,
                            "processing_times": {
                                "prediction": t1_pred - t0_pred,
                                "box_extraction": t1_boxes - t0_boxes,
                                "segmentation": t1_segmentation - t0_segmentation,
                                "total_time": t1_segmentation - t0_pred
                            }
                        }

            t1_segmentation = time.perf_counter()  # Fixed: Define variable for available case
            # No intersections → available
            return {
                "status": ParkingStatus.AVAILABLE.value,
                "processing_times": {
                    "prediction": t1_pred - t0_pred,
                    "box_extraction": t1_boxes - t0_boxes,
                    "segmentation": t1_segmentation - t0_segmentation,
                    "total_time": t1_segmentation - t0_pred
                }
            }

        except Exception as e:
            print(f"Error during detection: {e}")
            return {
                "status": ParkingStatus.UNKNOWN.value,
                "processing_times": {
                    "prediction": 0,
                    "box_extraction": 0,
                    "segmentation": 0,
                    "total_time": 0
                }
            }