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
from src.sort import Sort

tz = pytz.timezone("Asia/Bangkok")

def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DetectionModule:
    def __init__(self, use_gpu: bool = False):
        self.email = globals.USER_EMAIL
        print(f"DetectionModule initialized with email: {self.email}")

        # History per track: {track_id: {"centroids": [...], "zone": zone_id}}
        self.track_history = {}

        # Init SORT tracker
        self.tracker = Sort(max_age=15, min_hits=3, iou_threshold=0.3)

        if use_gpu and torch.cuda.is_available():
            self.device = "cuda:0"
            print(f"CUDA available. Using GPU {self.device}")
        else:
            self.device = "cpu"
            print("Using CPU for inference.")

        # Model load
        model_paths = ["yolo12n.pt", "yolo12n.onnx"]
        self.model = None
        for path in model_paths:
            path = resource_path(path)
            if os.path.exists(path):
                try:
                    self.model = YOLO(path, task="detect", verbose=False)
                    print(f"Loaded YOLO model: {path}")
                    break
                except Exception as e:
                    print(f"Failed to load model {path}: {e}")
        if self.model is None:
            raise RuntimeError("No valid YOLO model found")

        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        _ = self.model.predict(dummy, device=self.device, verbose=False)
        print(f"Model warm-up complete on {self.device}")

    def run(self, frame: np.ndarray, coordinates: list) -> str:
        if self.model is None:
            return ParkingStatus.UNKNOWN.value

        try:
            # YOLO inference
            results = self.model.predict(frame, device=self.device, verbose=False)
            boxes = results[0].boxes.xyxy.cpu().numpy()
            scores = results[0].boxes.conf.cpu().numpy()

            # SORT requires [x1,y1,x2,y2,score]
            detections = np.hstack([boxes, scores.reshape(-1, 1)])
            tracked_objects = self.tracker.update(detections)

            frame_drawed = frame.copy()

            # Build zone polygons
            zones = []
            for region in coordinates:
                pts = [(pt["x"], pt["y"]) for pt in region["polygon_points"]]
                poly = Polygon(pts)
                if poly.is_valid:
                    zones.append((region["zone_id"], poly))

            for x1, y1, x2, y2, track_id in tracked_objects:
                det_poly = box(x1, y1, x2, y2)
                bottom_center = ((x1 + x2) / 2, y2)
                centroid = (int((x1 + x2) / 2), int((y1 + y2) / 2))

                print(f"Track ID: {track_id}, BBox: ({x1}, {y1}, {x2}, {y2}), Centroid: {centroid}")

                for zone_id, zone_poly in zones:
                    # Calculate Intersection over Object (IOO)
                    intersection_area = det_poly.intersection(zone_poly).area
                    object_area = det_poly.area
                    IOO = intersection_area / object_area if object_area > 0 else 0

                    # Condition: must pass either IOO threshold or bottom center inside
                    if IOO < 0.3 and not zone_poly.contains(Point(bottom_center)):
                        continue  # Skip if not sufficiently inside

                    # History init
                    hist = self.track_history.setdefault(track_id, {"centroids": [], "zone": zone_id})
                    hist["centroids"].append(centroid)

                    # Keep only last 10 frames
                    if len(hist["centroids"]) > 15:
                        hist["centroids"].pop(0)

                    # Check motion
                    if len(hist["centroids"]) >= 3:
                        dists = []
                        for i in range(1, len(hist["centroids"])):
                            (x_prev, y_prev) = hist["centroids"][i - 1]
                            (x_curr, y_curr) = hist["centroids"][i]
                            dists.append(np.linalg.norm([x_curr - x_prev, y_curr - y_prev]))

                        avg_movement = np.mean(dists)
                        movement_threshold = 5  # pixels

                        if avg_movement < movement_threshold:
                            print(
                                f"Track {track_id} in zone {zone_id} is stationary "
                                f"(avg movement {avg_movement:.2f}px, IOO={IOO:.2f})"
                            )
                            frame_drawed = self.draw_detections(frame, det_poly, zone_poly, avg_movement)
                            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
                            caption = (
                                f"Vehicle Detected in {zone_id}\n"
                                f"Time: {now}\n"
                                f"Parking Status: OCCUPIED\n"
                                f"Avg Movement: {avg_movement:.2f}px\n"
                                f"IOO: {IOO:.2f}\n"
                            )
                            _ = notify_telegram(
                                base64_str=self.frame_to_base64(frame_drawed),
                                caption=caption,
                                email=self.email,
                            )
                            self.track_history[track_id]["centroids"] = []
                            return ParkingStatus.OCCUPIED.value

            return ParkingStatus.AVAILABLE.value

        except Exception as e:
            print(f"Error during detection: {e}")
            return ParkingStatus.UNKNOWN.value

    def frame_to_base64(self, frame):
        if frame is not None:
            success, encoded_image = cv.imencode(".jpg", frame)
            if success:
                return base64.b64encode(encoded_image.tobytes()).decode("utf-8")
        return None

    def draw_detections(self, frame, detection_box, zone_poly, value):
        frame_copy = frame.copy()
        pts = np.array(zone_poly.exterior.coords, np.int32)
        cv.polylines(frame_copy, [pts], True, (255, 0, 0), 2)
        minx, miny, maxx, maxy = detection_box.bounds
        cv.rectangle(frame_copy, (int(minx), int(miny)), (int(maxx), int(maxy)), (0, 255, 0), 2)
        cv.putText(frame_copy, f"Stationary ({value:.2f}px)", (int(minx), int(miny) - 5),
                   cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame_copy
