"""
Evaluate PencilTrace against the Scanned sample images.
Pre-resizes large scanned PNGs to template dimensions for fast SIFT alignment.
"""
import os, sys, json
import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from omr_engine_wrapper import process_omr_batch
from grading import grade_results

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'Samples', 'Scanned')
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'eval_temp_scanned')
RESIZED_DIR = os.path.join(TEMP_DIR, 'resized')
os.makedirs(RESIZED_DIR, exist_ok=True)

template_path = os.path.join(os.path.dirname(__file__), 'templates', 'template_uom_60q.json')

# Template target dimensions
TEMPLATE_H, TEMPLATE_W = 3508, 2481

# Load ground truth
df = pd.read_csv(os.path.join(SAMPLES_DIR, 'results.csv'))
expected = {}
for col in df.columns[1:]:
    idx_val = str(df[col].iloc[0])
    responses = []
    for v in df[col].iloc[1:]:
        s = str(v) if str(v) != 'nan' else '-'
        responses.append(s)
    expected[col] = {'Index': idx_val, 'responses': responses}

total_q_mismatches = 0
total_idx_mismatches = 0
total_questions = 0

for filename in sorted(expected.keys()):
    img_path = os.path.join(SAMPLES_DIR, filename)
    if not os.path.exists(img_path):
        print(f"Image not found: {img_path}")
        continue
    
    # Pre-resize to template dimensions for fast alignment
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to read {filename}")
        continue
    
    h, w = img.shape[:2]
    if h > TEMPLATE_H * 1.5 or w > TEMPLATE_W * 1.5:
        resized = cv2.resize(img, (TEMPLATE_W, TEMPLATE_H), interpolation=cv2.INTER_AREA)
        resized_path = os.path.join(RESIZED_DIR, filename)
        cv2.imwrite(resized_path, resized)
        process_path = resized_path
        print(f"Resized {filename}: {w}x{h} -> {TEMPLATE_W}x{TEMPLATE_H}")
    else:
        process_path = img_path
    
    raw = process_omr_batch([process_path], template_path, output_dir=TEMP_DIR)
    graded = grade_results(raw)
    
    if not graded:
        print(f"Failed to process {filename}")
        continue
    
    res = graded[0]
    pred_idx = res['responses'][0] if res['responses'][0] else '-'
    pred_ans = [x if x else '-' for x in res['responses'][1:]]
    
    exp_idx = expected[filename]['Index']
    exp_ans = expected[filename]['responses']
    
    print(f"--- {filename} ---")
    
    # Index check
    exp_idx_clean = exp_idx.replace('-', '')
    if pred_idx != exp_idx_clean:
        print(f"  INDEX MISMATCH: Expected '{exp_idx}' (clean: '{exp_idx_clean}'), Got '{pred_idx}'")
        total_idx_mismatches += 1
    else:
        print(f"  Index OK: {pred_idx}")
    
    # Question check
    mismatches = 0
    for q in range(min(60, len(pred_ans), len(exp_ans))):
        total_questions += 1
        if pred_ans[q] != exp_ans[q]:
            print(f"  Q{q+1} mismatch: Expected {exp_ans[q]}, Got {pred_ans[q]}")
            mismatches += 1
    
    total_q_mismatches += mismatches
    print(f"  Total: {mismatches}/60 question mismatches\n")

print("=" * 60)
print(f"SUMMARY")
print(f"  Total question mismatches: {total_q_mismatches}/{total_questions}")
print(f"  Total index mismatches: {total_idx_mismatches}/{len(expected)}")
print(f"  Question accuracy: {100*(total_questions-total_q_mismatches)/total_questions:.1f}%")
