import cv2
import numpy as np
import json

img = cv2.imread('uploads/std_sample.png.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Crop the "A" bubble from Q3 as template (since Q1 and Q2 might have pencil marks nearby)
# Q3 is around (192, 1865)
template = gray[1850:1890, 180:230]

res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
threshold = 0.6
loc = np.where(res >= threshold)

# Cluster the points to find unique bubbles
bubbles = []
for pt in zip(*loc[::-1]):
    # Check if this point is close to an existing bubble
    found = False
    for b in bubbles:
        if abs(b[0] - pt[0]) < 20 and abs(b[1] - pt[1]) < 20:
            found = True
            break
    if not found:
        bubbles.append(pt)

print(f"Found {len(bubbles)} bubbles!")
