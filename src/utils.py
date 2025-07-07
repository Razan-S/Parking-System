from shapely.geometry import Polygon, LinearRing
from src.config.utils import CameraConfigManager
import cv2 as cv

def capture_video(camera_id):
    """
    Capture video from a camera using OpenCV.
    
    Args:
        camera_id (str): The ID of the camera to capture from.
    
    Returns:
        VideoCapture: OpenCV VideoCapture object for the camera.
    """
    camM = CameraConfigManager()
    camera = camM.get_camera_by_id(camera_id)
    if not camera:
        raise ValueError(f"Camera with ID {camera_id} not found.")
    
    video_source = camera.get("video_source", 0)  # Default to 0 if not specified
    
    cap = cv.VideoCapture(video_source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {video_source}")
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from video source")
                break
                
            cv.imshow('Camera Feed - Press q to quit', frame)
            if cv.waitKey(20) & 0xFF == ord('q'):
                break
    
    finally:
        cap.release()
        cv.destroyAllWindows()

def capture_one_frame(camera_id):
    camM = CameraConfigManager()
    camera = camM.get_camera_by_id(camera_id)
    if not camera:
        raise ValueError(f"Camera with ID {camera_id} not found.")
    
    video_source = camera.get("video_source", 0)  # Default to 0 if not specified

    cap = cv.VideoCapture(video_source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {video_source}")
    
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from video source")
        return None
        
    cv.imshow('Camera Feed - Press any key to close', frame)
    cv.waitKey(0)  # Wait for a key press
    cv.destroyAllWindows()  # Close the window
    
    return frame

def is_valid_polygon(coordinates, min_points=3, min_area=10):
    """
    Check if coordinates form a valid polygon with sufficient area using Shapely.
    
    Args:
        coordinates: List of (x, y) tuples
        min_points: Minimum number of points required
        min_area: Minimum area threshold
    
    Returns:
        tuple: (is_valid, area, message)
    """
    if len(coordinates) < min_points:
        return False, 0, f"Need at least {min_points} points for a polygon"
    
    try:
        poly = Polygon(coordinates)
        
        # Check if the polygon is valid (non-self-intersecting)
        if not poly.is_valid:
            return False, poly.area, "Polygon is invalid (e.g., self-intersecting or malformed)"
        
        # Check if the polygon is closed (optional if you're using Polygon constructor)
        ring = LinearRing(coordinates)
        if not ring.is_simple:
            return False, poly.area, "Polygon ring is not simple (e.g., self-intersecting)"
        
        if poly.area < min_area:
            return False, poly.area, f"Polygon area ({poly.area:.1f}) is too small (minimum: {min_area})"

        # Check if the polygon is degenerate (zero area, like collinear points)
        if poly.area == 0:
            return False, 0, "Polygon has zero area (likely degenerate or collinear points)"

        return True, poly.area, "Valid polygon"
    
    except Exception as e:
        return False, 0, f"Error creating polygon: {str(e)}"