import cv2
import json
import numpy as np
from backend.omr_engine_wrapper import align_image

img = cv2.imread('uploads/Sample_converted.jpg')
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
warped_gray, warped_color = align_image(img_gray, img)
tmpl = cv2.imread('templates/template_uom_60q.png', 0)

# Find Q21 column positions by looking at the warped sample at Q21 row
# Q21=A (first answer in q21_40 block) 
# Expected y = 1648 (same as Q1, they're in the same row just different x range)
# Expected x for A in q21_40 = 1002

# Scan x around 1002 for darkness at y=1648 (Q21=A)
q21_y = 1648  # same row as Q1
print("Q21 row (y=1648), scanning x=900-1600:")
prev_mark = False
for x in range(900, 1600, 10):
    roi_s = warped_gray[q21_y:q21_y+20, x:x+60]
    if roi_s.size > 0:
        bg = np.percentile(roi_s, 90)
        darkness = float(np.sum(np.maximum(0, bg - roi_s)))
        if darkness > 5000:
            print(f"  x={x}: darkness={darkness:.0f}")

# Let's also check what the template looks like around x=1000-1600 at y=1648
print("\nTemplate at Q21 row (y=1648), scanning x=900-1600:")
for y in range(1640, 1680, 5):
    row_data = tmpl[y, 950:1700]
    dark_positions = np.where(row_data < 200)[0]
    if len(dark_positions) > 0:
        # Group contiguous positions
        gaps = np.diff(dark_positions)
        print(f"  y={y}: dark positions at x={dark_positions[:20]+950}")

# Also crop and save the Q21-40 section for visual inspection
crop = warped_color[1560:3508, 920:1680]
cv2.imwrite(r'C:\Users\user\.gemini\antigravity\brain\6754f51b-e5dc-4910-9811-0d530d887402\scratch\debug_q21_40.jpg', crop)
print("\nSaved Q21-40 crop")
