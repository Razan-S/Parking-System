from ultralytics import YOLO
import numpy as np
from shapely.geometry import Polygon, box, Point
from src.enums import ParkingStatus
import torch
import os
import sys
import base64
import cv2 as cv
from src import globals
from datetime import datetime
import pytz 
from src.utils import *

tz = pytz.timezone("Asia/Bangkok")

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
        self.email = globals.USER_EMAIL
        print(f"DetectionModule initialized with email: {self.email}")

        self.zone_history = {}

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
        self.prev_detections = {}

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

    def calculate_density(self, road: np.ndarray, road_car: np.ndarray) -> float:
        hist_road = cv.calcHist([road], [0], None, [256], [1, 255]).flatten()
        hist_road_car = cv.calcHist([road_car], [0], None, [256], [1, 255]).flatten()
        hist_diff = np.maximum(hist_road - hist_road_car, 0)
        density = np.sum(hist_diff) / np.sum(hist_road)
        return float(f"{density:.2f}")

    def run(self, frame: np.ndarray, coordinates: list) -> str:
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

            frame_drawed = frame.copy()

            for x1, y1, x2, y2 in boxes:
                det_poly = box(x1, y1, x2, y2)
                bottom_center = ((x1 + x2) / 2, y2)
                for zone_id, zone_poly in zones:
                    intersection_area = det_poly.intersection(zone_poly).area
                    object_area = det_poly.area
                    IOO = intersection_area / object_area if object_area > 0 else 0
                    bottom_inside = zone_poly.contains(Point(bottom_center))

                    if IOO >= 0.2 and bottom_inside:
                        # Crop the zone area from the frame
                        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                        pts = np.array(zone_poly.exterior.coords, np.int32)
                        cv.fillPoly(mask, [pts], 255)
                        zone_img = cv.bitwise_and(frame, frame, mask=mask)

                         # Initialize or update zone history
                        hist = self.zone_history.setdefault(zone_id, {"frames": [], "count": 0})

                        if hist["count"] == 0:
                            hist["frames"] = [zone_img]
                            hist["count"] = 1
                            # Compare histograms
                            
                        elif hist["count"] < 3:
                            hist["frames"].append(zone_img)
                            hist["count"] += 1
                            if hist["count"] == 3:
                                # Compare histograms
                                density1 = self.calculate_density(hist["frames"][0], hist["frames"][1])
                                density2 = self.calculate_density(hist["frames"][0], hist["frames"][2])
                                avg_density = (density1 + density2) / 2
                                threshold = 0.15  # Set your threshold here

                                if avg_density < threshold:
                                    # Car is stationary, send notification
                                    frame_drawed = self.draw_detections(frame, det_poly, zone_poly, IOO)
                                    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
                                    caption = (
                                        f"Vehicle Detected in {zone_id}\n"
                                        f"Time: {now}\n"
                                        f"Parking Status: OCCUPIED\n"
                                        f"Density: {avg_density:.2f}\n"
                                        f"hist_count: {hist['count']}\n"
                                    )

                                    _ = notify_telegram(
                                        base64_str=self.frame_to_base64(frame_drawed),
                                        caption=caption,
                                        email=self.email
                                    )
                                    # Reset history for this zone
                                    self.zone_history[zone_id] = {"frames": [], "count": 0}
                                    return ParkingStatus.OCCUPIED.value
                                else:
                                    # Not stationary, reset and wait for next detection
                                    self.zone_history[zone_id] = {"frames": [], "count": 0}
                                    return ParkingStatus.AVAILABLE.value
                        else:
                            return ParkingStatus.AVAILABLE.value
                    
            for zone_id in self.zone_history:
                self.zone_history[zone_id] = {"frames": [], "count": 0}
            return ParkingStatus.AVAILABLE.value

        except Exception as e:
            print(f"Error during detection: {e}")
            return ParkingStatus.UNKNOWN.value
        
    def frame_to_base64(self, frame):
        if frame is not None:
            success, encoded_image = cv.imencode('.jpg', frame)
            if success:
                base64_string = base64.b64encode(encoded_image.tobytes()).decode('utf-8')
                return base64_string
            else:
                print("Failed to encode image to base64.")
                return None
        else:
            print("No frame to encode.")
            return None

    def draw_detections(self, frame, detection_box, zone_poly, value):
        frame_copy = frame.copy() if frame is not None else None

        # Draw the zone polygon
        if zone_poly is not None and frame_copy is not None:
            # Get the exterior coordinates of the polygon
            pts = np.array(zone_poly.exterior.coords, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv.polylines(frame_copy, [pts], isClosed=True, color=(255, 0, 0), thickness=2)

        # Draw the detection box
        if detection_box is not None and frame_copy is not None:
            # Get bounding box coordinates from Shapely box
            minx, miny, maxx, maxy = detection_box.bounds
            x1, y1, x2, y2 = int(minx), int(miny), int(maxx), int(maxy)
            cv.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv.putText(frame_copy, "Vehicle", (x1, y1 - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv.putText(frame_copy, f"IOO: {value:.2f}", (x1, y2 + 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return frame_copy if frame_copy is not None else frame