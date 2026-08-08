import os
import shutil
import pandas as pd
from pathlib import Path
from backend.omr_engine.entry import entry_point
from backend.omr_engine.defaults import CONFIG_DEFAULTS

def process_omr_batch(image_paths, template_path, output_dir="results"):
    """
    Wraps OMRChecker's core functionality to process a batch of images against a single template.
    """
    # Create a temporary workspace for OMRChecker
    temp_dir = os.path.join(output_dir, "temp_omr_run")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Copy template.json to temp_dir
        shutil.copy(template_path, os.path.join(temp_dir, "template.json"))
        
        # Copy images to temp_dir
        for img_path in image_paths:
            shutil.copy(img_path, os.path.join(temp_dir, os.path.basename(img_path)))
            
        # Prepare args
        args = {
            "output_dir": os.path.join(output_dir, "omr_outputs"),
            "setLayout": False,
            "autoAlign": False,
            "debug": False,
            "input_paths": [temp_dir]
        }
        
        # Run OMRChecker
        entry_point(Path(temp_dir), args)
        
        # Read the generated CSV results
        results_csv = os.path.join(args["output_dir"], "temp_omr_run", "Results", "Results.csv")
        
        if os.path.exists(results_csv):
            df = pd.read_csv(results_csv, header=None) # OMRChecker writes without header initially
            # We'll return the raw data and let grading.py structure it
            return df.values.tolist()
        else:
            return []
            
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
