import os
import sys
import cv2
import numpy as np
from PIL import Image
import pillow_heif
import json

pillow_heif.register_heif_opener()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
from omr_engine_wrapper import align_image

img = cv2.imread('eval_temp/9.jpg', cv2.IMREAD_GRAYSCALE)
img_color = cv2.imread('eval_temp/9.jpg')
warped_gray, warped_color = align_image(img, img_color)

with open('templates/template_uom_60q.json', 'r') as f:
    template = json.load(f)

box_w, box_h = template.get("bubbleDimensions", [25, 10])

def analyze_q(q_num):
    # Find the row for this Q
    q_str = f"q{q_num}"
    b = None
    r_idx = -1
    drift_x = 0
    bubblesGap = 0
    orig_x = 0
    for block_name, block in template["fieldBlocks"].items():
        if block_name.startswith("q"):
            if q_str in block["fieldLabels"]:
                b = block
                r_idx = block["fieldLabels"].index(q_str)
                drift_x = b.get("driftPerRow", 0.0)
                bubblesGap = b["bubblesGap"]
                orig_x = int(b["origin"][0] + r_idx * drift_x)
                break
                
    row_ys = [1647, 1729, 1812, 1895, 1977, 2060, 2143, 2224, 2307, 2389, 
              2473, 2555, 2638, 2721, 2803, 2886, 2969, 3050, 3133, 3216]
    orig_y = row_ys[r_idx]
    
    print(f"\n--- {q_str} ---")
    for i in range(5):
        bx = int(orig_x + i * bubblesGap)
        by = int(orig_y)
        roi = warped_gray[by:by+box_h, bx:bx+box_w]
        
        bg = np.percentile(roi, 90)
        sum_dark = float(np.sum(np.maximum(0, bg - roi)))
        p50 = np.percentile(roi, 50)
        p25 = np.percentile(roi, 25)
        p10 = np.percentile(roi, 10)
        
        dark_pixels = np.sum(roi < bg - 30)
        
        print(f"Option {i}: sum={sum_dark:.0f}, bg={bg:.0f}, p50={p50:.0f}, p25={p25:.0f}, p10={p10:.0f}, dark_px={dark_pixels}/{roi.size}")

analyze_q(4)
analyze_q(5)
analyze_q(13)
