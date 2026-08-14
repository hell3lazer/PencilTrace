import cv2
import numpy as np
import sys

img = cv2.imread("uploads/std_sample.png.jpg")
if img is None:
    print("Could not load image")
    sys.exit(1)

h, w = img.shape[:2]

# Draw horizontal lines every 100 pixels
for y in range(0, h, 100):
    cv2.line(img, (0, y), (w, y), (0, 0, 255), 2)
    cv2.putText(img, str(y), (10, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

# Draw vertical lines every 100 pixels
for x in range(0, w, 100):
    cv2.line(img, (x, 0), (x, h), (0, 255, 0), 2)
    cv2.putText(img, str(x), (x + 5, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

cv2.imwrite("uploads/grid_image.jpg", img)
print("Grid image saved.")
