from ultralytics import YOLO
import numpy as np
from shapely.geometry import Polygon, box

class DetectionModule:
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

    def detect(self, frame: np.ndarray, coordinates: list) -> bool:
        """
        Detect objects in the given frame and check if they intersect with specified regions.

        Args:
            frame (np.ndarray): The input image frame.
            coordinates (list): List of dicts like:
                [{"id": 1, "coordinates": [[x1, y1], [x2, y2], ...]}, ...]

        Returns:
            list: List of detected objects that intersect with specified regions with id.
        """
        if self.model is None:
            print("Model not loaded properly.")
            return False

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
                region_polygons.append({"id":region['id'], "coordinates":poly})

            result = []
            # Check each detection
            for det_box in detections:
                x1, y1, x2, y2 = det_box
                det_poly = box(x1, y1, x2, y2)  # Convert to shapely box (polygon)

                # Check intersection with all regions
                for region_poly in region_polygons:
                    if det_poly.intersects(region_poly["coordinates"]):
                        result.append({"id":region_poly['id'], "detect":True}) # Found an intersection
                    else:
                        result.append({"id":region_poly['id'], "detect":False})

        except Exception as e:
            print(f"Error during detection: {e}")
            return [ {"id": region["id"], "detect": False} for region in coordinates ]