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