from shapely.geometry import Polygon, LinearRing

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