import cv2
import numpy as np
import json
import math

img = cv2.imread('uploads/std_sample.png.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Find all "A" bubbles using template matching
template = gray[1850:1890, 180:230]
res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
threshold = 0.55
loc = np.where(res >= threshold)

bubbles = []
for pt in zip(*loc[::-1]):
    found = False
    for b in bubbles:
        if abs(b[0] - pt[0]) < 20 and abs(b[1] - pt[1]) < 20:
            found = True
            break
    if not found:
        bubbles.append(pt)

# Sort bubbles by X and Y
bubbles = sorted(bubbles, key=lambda b: (b[0] // 100, b[1]))

# Filter to get only the first "A" bubble of each column
# Expected X for columns: ~192, ~917, ~1712
def find_closest(x, y):
    best = None
    min_dist = 9999
    for b in bubbles:
        dist = math.hypot(b[0] - x, b[1] - y)
        if dist < min_dist:
            min_dist = dist
            best = b
    if min_dist < 60:
        return best
    return None

expected_xs = [192, 917, 1712]
expected_ys = [1750, 2110, 2490, 2690] # Approx starting Ys for the 4 blocks

with open('templates/template_uom_60q.json', 'r') as f:
    template_json = json.load(f)

# Clear existing q blocks
new_blocks = {k: v for k, v in template_json["fieldBlocks"].items() if not k.startswith("q")}

for col_idx, x in enumerate(expected_xs):
    for block_idx, y in enumerate(expected_ys):
        start_q = col_idx * 20 + block_idx * 5 + 1
        end_q = start_q + 4
        block_name = f"q{start_q}_{end_q}"
        
        # Find exact start bubble
        start_bubble = find_closest(x, y)
        if not start_bubble:
            print(f"Warning: could not find start bubble for {block_name} near {x},{y}")
            start_bubble = (x, y)
            
        # Find exact end bubble (Q5 of this block)
        # Expected gap is roughly 57-60 initially, then 37-38 at the bottom
        expected_gap = 57 if block_idx < 2 else 38
        end_y = start_bubble[1] + 4 * expected_gap
        end_bubble = find_closest(x, end_y)
        if not end_bubble:
            print(f"Warning: could not find end bubble for {block_name} near {x},{end_y}")
            end_bubble = (start_bubble[0], int(end_y))
            
        gap = (end_bubble[1] - start_bubble[1]) / 4.0
        if gap < 20 or gap > 70:
            gap = expected_gap
        
        start_q = int(block_name.split("_")[0][1:])
        if start_q <= 20:
            x_origin = 175
        elif start_q <= 40:
            x_origin = 930
        else:
            x_origin = 1680
            
        # We need to format the block!
        new_blocks[block_name] = {
            "origin": [x_origin, int(start_bubble[1]) + 22],
            "bubblesGap": 113,
            "labelsGap": round(gap, 2),
            "direction": "horizontal",
            "bubbleValues": ["A", "B", "C", "D", "E"],
            "fieldLabels": [f"q{i}" for i in range(start_q, end_q + 1)]
        }
        print(f"Block {block_name}: Origin {start_bubble}, Gap {gap:.2f}")

# Now for index blocks!
# Now for index blocks!
new_blocks["index_nums"] = {
    "origin": [120, 945],
    "bubblesGap": 56.0,
    "labelsGap": 43.0,
    "direction": "vertical",
    "bubbleValues": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    "fieldLabels": ["D1", "D2", "D3", "D4", "D5", "D6"]
}

new_blocks["index_char1"] = {
    "origin": [120 + 6 * 56.0 + 4, 945],
    "bubblesGap": 56.0,
    "labelsGap": 43.0,
    "direction": "vertical",
    "bubbleValues": ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K"],
    "fieldLabels": ["C1"]
}

new_blocks["index_char2"] = {
    "origin": [120 + 7 * 56.0 + 4, 945],
    "bubblesGap": 56.0,
    "labelsGap": 43.0,
    "direction": "vertical",
    "bubbleValues": ["L", "M", "N", "P", "R", "T", "U", "V", "X"],
    "fieldLabels": ["C2"]
}

template_json["fieldBlocks"] = new_blocks

with open('templates/template_uom_60q_adapted.json', 'w') as f:
    json.dump(template_json, f, indent=4)
print("Saved adapted template!")
