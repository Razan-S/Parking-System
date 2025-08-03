from shapely.geometry import Polygon, LinearRing
from src.config.utils import CameraConfigManager
import cv2 as cv
from datetime import datetime
import os

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
    cap.set(cv.CAP_PROP_BUFFERSIZE, 3)
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
    cap.set(cv.CAP_PROP_BUFFERSIZE, 3)
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

def capture_one_frame_silent(camera_id):
    """
    Capture a single frame from a camera without displaying it.
    Used for automated processing in threads.
    
    Args:
        camera_id (str): The ID of the camera to capture from.
    
    Returns:
        np.ndarray: The captured frame, or None if capture failed.
    """
    print(f'{datetime.now()} Capturing one frame from camera: {camera_id}')
    camM = CameraConfigManager()
    camera = camM.get_camera_by_id(camera_id)
    if not camera:
        raise ValueError(f"Camera with ID {camera_id} not found.")
    
    video_source = camera.get("video_source", 0)  # Default to 0 if not specified
    
    # Handle relative paths for video files
    if isinstance(video_source, str) and not video_source.startswith(('http://', 'https://', 'rtsp://', 'rtmp://')):
        # Check if it's a relative path
        if not os.path.isabs(video_source):
            # Convert to absolute path
            ROOT_DIR = os.path.abspath(os.curdir)
            video_source = os.path.join(ROOT_DIR, video_source)

    cap = cv.VideoCapture(video_source)
    cap.set(cv.CAP_PROP_BUFFERSIZE, 3)
    
    # Set timeout for RTSP/network streams (5 seconds)
    if isinstance(video_source, str) and video_source.startswith(('rtsp://', 'rtmp://', 'http://', 'https://')):
        cap.set(cv.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
    
    if not cap.isOpened():
        print(f"Could not open video source: {video_source}")
        return None
    
    try:
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to read frame from video source for camera {camera_id}")
            return None
        
        return frame
    finally:
        cap.release()

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