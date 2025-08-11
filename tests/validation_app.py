"""
Validation Application
GUI application for manual validation of parking detection results.
Shows images with detection polygons and provides buttons for manual annotation.
"""

import sys
import os
# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.utils import CameraConfigManager
from src.enums import ParkingStatus

import pandas as pd
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from shapely.geometry import Polygon
from datetime import datetime

class ValidationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking Detection Validation")
        self.root.geometry("1200x800")
        
        # Data
        self.df = None
        self.current_index = 0
        self.total_images = 0
        self.detection_zones = None
        
        # UI setup
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)  # Make image area wider
        main_frame.columnconfigure(1, weight=1)  # Control panel stays same
        main_frame.rowconfigure(1, weight=1)
        
        # Top frame for file selection and progress
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)
        
        # File selection
        ttk.Label(top_frame, text="CSV File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.file_label = ttk.Label(top_frame, text="No file selected", foreground="gray")
        self.file_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(top_frame, text="Load CSV", command=self.load_csv).grid(row=0, column=2)
        
        # Progress
        ttk.Label(top_frame, text="Progress:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.progress_label = ttk.Label(top_frame, text="0/0")
        self.progress_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        
        # Left frame for image
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Image canvas with scrollbars
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        self.image_canvas = tk.Canvas(canvas_frame, bg="white")
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.image_canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.image_canvas.yview)
        
        self.image_canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        self.image_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Right frame for controls
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.grid_propagate(False)
        
        # Current image info
        info_frame = ttk.LabelFrame(right_frame, text="Current Image Info", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="Frame:").grid(row=0, column=0, sticky=tk.W)
        self.frame_label = ttk.Label(info_frame, text="-")
        self.frame_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="CPU Result:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.cpu_label = ttk.Label(info_frame, text="-")
        self.cpu_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(info_frame, text="CPU Time:").grid(row=2, column=0, sticky=tk.W)
        self.cpu_time_label = ttk.Label(info_frame, text="-")
        self.cpu_time_label.grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="GPU Result:").grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        self.gpu_label = ttk.Label(info_frame, text="-")
        self.gpu_label.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(info_frame, text="GPU Time:").grid(row=4, column=0, sticky=tk.W)
        self.gpu_time_label = ttk.Label(info_frame, text="-")
        self.gpu_time_label.grid(row=4, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Current Manual:").grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        self.manual_label = ttk.Label(info_frame, text="-")
        self.manual_label.grid(row=5, column=1, sticky=tk.W, pady=(5, 0))
        
        # Validation buttons
        validation_frame = ttk.LabelFrame(right_frame, text="Manual Validation", padding="10")
        validation_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(validation_frame, text="Available", 
                  command=lambda: self.set_validation(ParkingStatus.AVAILABLE.value),
                  style="Available.TButton").grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Button(validation_frame, text="Occupied", 
                  command=lambda: self.set_validation(ParkingStatus.OCCUPIED.value),
                  style="Occupied.TButton").grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Button(validation_frame, text="Unknown", 
                  command=lambda: self.set_validation(ParkingStatus.UNKNOWN.value),
                  style="Unknown.TButton").grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        
        validation_frame.columnconfigure(0, weight=1)
        
        # Navigation buttons
        nav_frame = ttk.Frame(right_frame)
        nav_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        nav_frame.columnconfigure((0, 1), weight=1)
        
        self.prev_button = ttk.Button(nav_frame, text="← Previous", command=self.prev_image)
        self.prev_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.next_button = ttk.Button(nav_frame, text="Next →", command=self.next_image)
        self.next_button.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Save button
        ttk.Button(right_frame, text="Save Results", command=self.save_results).grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        # Configure button styles
        style = ttk.Style()
        style.configure("Available.TButton", foreground="green")
        style.configure("Occupied.TButton", foreground="red")
        style.configure("Unknown.TButton", foreground="orange")
        
        # Disable buttons initially
        self.update_ui_state()
        
    def load_csv(self):
        """Load CSV file with image data"""
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            self.df = pd.read_csv(file_path)
            
            # Validate CSV structure
            required_columns = ['Frame', 'CPU_Result', 'GPU_Result', 
                              'CPU_prediction_time', 'CPU_box_extraction_time', 'CPU_segmentation_time', 'CPU_total_time',
                              'GPU_prediction_time', 'GPU_box_extraction_time', 'GPU_segmentation_time', 'GPU_total_time',
                              'Manual_Result', 'Image_Path', 'Timestamp']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            
            if missing_columns:
                messagebox.showerror("Error", f"CSV missing columns: {missing_columns}")
                return
            
            # Add Manual_Result column if it doesn't exist
            if 'Manual_Result' not in self.df.columns:
                self.df['Manual_Result'] = pd.Series(dtype='object')
            
            self.total_images = len(self.df)
            self.current_index = 0
            
            self.file_label.config(text=os.path.basename(file_path), foreground="black")
            
            # Load camera configuration for first image
            self.load_camera_config()
            
            # Display first image
            self.display_current_image()
            self.update_ui_state()
            
            messagebox.showinfo("Success", f"Loaded {self.total_images} images from CSV")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")
    
    def load_camera_config(self):
        """Load camera configuration to get detection zones"""
        try:
            cam_config = CameraConfigManager()
            cam = cam_config.get_camera_by_id('CAM_001')  # Assuming CAM_001 for now
            detection_zones_json = cam.get('detection_zones', [])
            
            if detection_zones_json:
                zone = detection_zones_json[0]
                polygon_points = zone.get('polygon_points', [])
                if len(polygon_points) >= 3:
                    coords = [(point['x'], point['y']) for point in polygon_points]
                    self.detection_zones = Polygon(coords)
        except Exception as e:
            print(f"Warning: Could not load detection zones: {e}")
            self.detection_zones = None
    
    def display_current_image(self):
        """Display the current image with detection zones"""
        if self.df is None or self.current_index >= len(self.df):
            return
        
        row = self.df.iloc[self.current_index]
        image_path = row['Image_Path']
        
        try:
            # Load image with OpenCV
            cv_image = cv2.imread(image_path)
            if cv_image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Draw detection zones if available
            if self.detection_zones is not None:
                pts = np.array(self.detection_zones.exterior.coords, dtype=np.int32)
                cv2.polylines(cv_image, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
                
                # Add zone label
                centroid = self.detection_zones.centroid
                cv2.putText(cv_image, "Detection Zone", 
                           (int(centroid.x), int(centroid.y)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Convert to RGB for display
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # Resize image if too large
            max_size = 1000  # Increased from 800 to make images larger
            if pil_image.width > max_size or pil_image.height > max_size:
                pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and display
            self.photo = ImageTk.PhotoImage(pil_image)
            
            self.image_canvas.delete("all")
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            # Update canvas scroll region
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            
            # Update info labels
            self.update_info_labels(row)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {e}")
    
    def update_info_labels(self, row):
        """Update information labels with current row data"""
        self.frame_label.config(text=str(row['Frame']))
        self.cpu_label.config(text=str(row['CPU_Result']))
        self.cpu_time_label.config(text=f"{row['CPU_total_time']:.3f}s")  # Fixed column name
        self.gpu_label.config(text=str(row['GPU_Result']))
        self.gpu_time_label.config(text=f"{row['GPU_total_time']:.3f}s")  # Fixed column name
        
        manual_result = row['Manual_Result']
        if pd.isna(manual_result) or manual_result is None:
            self.manual_label.config(text="Not set", foreground="red")
        else:
            self.manual_label.config(text=str(manual_result), foreground="green")
        
        self.progress_label.config(text=f"{self.current_index + 1}/{self.total_images}")
    
    def set_validation(self, result):
        """Set manual validation result for current image"""
        if self.df is None or self.current_index >= len(self.df):
            return
        
        # Convert to string to avoid dtype issues
        self.df.loc[self.current_index, 'Manual_Result'] = str(result)
        self.update_info_labels(self.df.iloc[self.current_index])
        
        # Auto-advance to next image
        self.next_image()
    
    def prev_image(self):
        """Go to previous image"""
        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_image()
            self.update_ui_state()
    
    def next_image(self):
        """Go to next image"""
        if self.current_index < self.total_images - 1:
            self.current_index += 1
            self.display_current_image()
            self.update_ui_state()
    
    def update_ui_state(self):
        """Update UI button states"""
        has_data = self.df is not None and self.total_images > 0
        
        self.prev_button.config(state="normal" if has_data and self.current_index > 0 else "disabled")
        self.next_button.config(state="normal" if has_data and self.current_index < self.total_images - 1 else "disabled")
    
    def save_results(self):
        """Save validation results to CSV"""
        if self.df is None:
            messagebox.showwarning("Warning", "No data to save")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validated_results_{timestamp}.csv"
            self.df.to_csv(filename, index=False)
            
            # Count validated images
            validated_count = self.df['Manual_Result'].notna().sum()
            
            messagebox.showinfo("Success", 
                              f"Results saved to {filename}\n"
                              f"Validated: {validated_count}/{self.total_images} images")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {e}")

def main():
    root = tk.Tk()
    app = ValidationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
