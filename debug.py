import sys
import os
import shutil

# Add project root
sys.path.insert(0, os.path.dirname(__file__))

from backend.omr_engine_wrapper import process_omr_batch
from backend.grading import grade_results

image_path = "uploads/std_sample.jpg"
template_path = "templates/template_uom_60q.json"
output_dir = "debug_out"
os.makedirs(output_dir, exist_ok=True)

print(f"Testing OMR on {image_path} with template {template_path}")
try:
    raw_data = process_omr_batch([image_path], template_path, output_dir=output_dir)
    print("Raw Data:", raw_data)
    if raw_data:
        graded = grade_results(raw_data)
        print("Graded:", graded)
    else:
        print("No raw data returned! Checking omr_outputs directory...")
        
        # Check omr_outputs folder to see what failed
        omr_outputs = os.path.join(output_dir, "omr_outputs", "temp_omr_run")
        if os.path.exists(omr_outputs):
            for root, dirs, files in os.walk(omr_outputs):
                for f in files:
                    print("Found file:", os.path.join(root, f))
except Exception as e:
    import traceback
    traceback.print_exc()
