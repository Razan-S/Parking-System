from ultralytics import YOLO
from PyQt6.QtCore import QRunnable, pyqtSlot
import numpy as np
from shapely.geometry import Polygon, box
from src.enums import ParkingStatus

class DetectionModule(QRunnable):
    def __init__(self):
        try:
            self.model = YOLO("yolo12n.engine", task="detect", verbose=True)
            
            # Warmup to load model
            dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model(dummy_image, verbose=False)

            print("Model initialized successfully.")
        except Exception as e:
            print(f"Error initializing model: {e}")
            self.model = None

    @pyqtSlot()
    def run(self, frame: np.ndarray, coordinates: list) -> ParkingStatus:
        """
        Detect objects in the given frame and check if they intersect with specified regions.

        Args:
            frame (np.ndarray): The input image frame.
            coordinates (list): List of dicts like:
                [{"id": 1, "coordinates": [[x1, y1], [x2, y2], ...]}, ...]

        Returns:
            ParkingStatus: Enum indicating the parking status (AVAILABLE, OCCUPIED, UNKNOWN).
        """
        if self.model is None:
            print("Model not loaded properly.")
            return ParkingStatus.UNKNOWN.value

        try:
            results = self.model(frame, verbose=False)
            detections = results[0].boxes.xyxy.cpu().numpy()  # Detected boxes: [x1, y1, x2, y2]

            # Build polygons for specified regions
            region_polygons = []
            for region in coordinates:
                poly = Polygon(region["coordinates"])
                if not poly.is_valid:
                    print(f"Warning: Invalid polygon for region ID {region['id']}")
                    continue
                region_polygons.append({"id": region['id'], "coordinates": poly})

            # Check if any detection intersects with any region
            overall_status = ParkingStatus.AVAILABLE.value
            
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