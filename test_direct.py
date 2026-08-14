import sys
import os

project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.omr_engine_wrapper import process_omr_batch
from backend.grading import grade_results

image_path = "uploads/sample_converted.png"
template_path = "templates/template_uom_60q.json"

raw = process_omr_batch([image_path], template_path, output_dir="uploads")
print("RAW:")
for r in raw:
    print(r)

graded = grade_results(raw)
print("GRADED:")
import json
print(json.dumps(graded, indent=2))
