import os
import shutil
from pathlib import Path
from backend.omr_engine.entry import entry_point

# 1. create temp run dir
os.makedirs("test_layout", exist_ok=True)
shutil.copy("temp_template.png", "test_layout/temp_template.png")
shutil.copy("templates/template_uom_60q.json", "test_layout/template.json")

# 2. run setLayout
args = {
    "output_dir": "test_layout_out",
    "setLayout": True,
    "autoAlign": False,
    "debug": True,
    "input_paths": ["test_layout"]
}

entry_point(Path("test_layout"), args)
