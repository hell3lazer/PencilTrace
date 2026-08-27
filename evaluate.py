import os
import sys
import pandas as pd
from PIL import Image
import pillow_heif
import cv2
import json

pillow_heif.register_heif_opener()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
from omr_engine_wrapper import process_omr_batch
from grading import grade_results

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'Samples')
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'eval_temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# Load ground truth
df = pd.read_csv(os.path.join(SAMPLES_DIR, 'results.csv'))
expected = {}
for col in df.columns[1:]:
    file_id = col
    expected[file_id] = {
        'Index': str(df[col][0]),
        'responses': [str(x) if str(x) != 'nan' else '-' for x in df[col][1:]]
    }

template_path = os.path.join(os.path.dirname(__file__), 'templates', 'template_uom_60q.json')

results = []
for i in range(11):
    file_id = str(i)
    heic_path = os.path.join(SAMPLES_DIR, f"{file_id}.heic")
    if not os.path.exists(heic_path):
        continue
    
    img = Image.open(heic_path)
    img = img.convert("RGB")
    jpg_path = os.path.join(TEMP_DIR, f"{file_id}.jpg")
    img.save(jpg_path, "JPEG")
    
    raw = process_omr_batch([jpg_path], template_path, output_dir=TEMP_DIR)
    graded = grade_results(raw)
    
    if not graded:
        print(f"Failed to process {file_id}")
        continue
        
    res = graded[0]
    pred_idx = res['responses'][0]
    pred_ans = res['responses'][1:]
    # Replace empty with '-'
    pred_idx = pred_idx if pred_idx else '-'
    pred_ans = [x if x else '-' for x in pred_ans]
    
    exp_idx = expected[file_id]['Index']
    exp_ans = expected[file_id]['responses']
    
    print(f"--- File {file_id}.heic ---")
    if pred_idx != exp_idx:
        print(f"Index mismatch: Expected {exp_idx}, Got {pred_idx}")
    
    mismatches = 0
    for q in range(60):
        if pred_ans[q] != exp_ans[q]:
            print(f"Q{q+1} mismatch: Expected {exp_ans[q]}, Got {pred_ans[q]}")
            mismatches += 1
            
    print(f"Total mismatches for {file_id}: {mismatches}\n")
