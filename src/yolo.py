from ultralytics import YOLO
import numpy as np
from shapely.geometry import Polygon, box
from src.enums import ParkingStatus
import torch
import os
import sys

def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for development and PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DetectionModule:
    def __init__(self, use_gpu: bool = False):
        """
        Initialize the YOLO detection model, choosing CPU or GPU.

        Args:
            use_gpu (bool): If True, attempt to load on GPU (CUDA). If CUDA isn’t
                            available or use_gpu=False, falls back to CPU.
            allow_trt (bool): If True, try TensorRT (.engine). Disabled by default
                              for PyInstaller builds to avoid DLL errors.
        """
        # Decide which device to use
        if use_gpu and torch.cuda.is_available():
            self.device = "cuda:0"  # first CUDA GPU
            print(f"CUDA is available. Using GPU device {self.device}.")
        else:
            self.device = "cpu"
            print("Using CPU for inference.")

        # Model candidates
        if self.device == "cpu":
            model_paths = [
                "yolo12n.pt",      # PyTorch (safe for CPU)
                "yolo12n.onnx"     # ONNX (CPU compatible)
            ]
        else:
            model_paths = []
            model_paths += [
                "yolo12n.pt",      # PyTorch GPU
                "yolo12n.onnx"     # ONNX GPU
            ]

        self.model = None
        for path in model_paths:
            path = resource_path(path)
            if os.path.exists(path):
                try:
                    print(f"Loading model from '{path}'...")
                    self.model = YOLO(path, task="detect", verbose=False)
                    print(f"Successfully loaded '{path}'.")
                    break
                except Exception as e:
                    print(f"Failed to load '{path}': {e}")

        if self.model is None:
            raise RuntimeError(
                "No valid YOLO model file found. "
                "Expected one of: yolo12n.pt, yolo12n.onnx, (yolo12n.engine if TRT enabled)."
            )

        # Warm up the model with a dummy image on the desired device
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
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