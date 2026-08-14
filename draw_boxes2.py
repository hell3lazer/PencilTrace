import cv2
import sys

img = cv2.imread("uploads/std_sample.png.jpg")
if img is None:
    print("Could not load image")
    sys.exit(1)

bw, bh = 45, 20

def draw_block(ox, oy, bg, lg, dir, rows, cols):
    for i in range(rows):
        for j in range(cols):
            if dir == "horizontal":
                x = ox + j * bg
                y = oy + i * lg
            else:
                x = ox + i * lg
                y = oy + j * bg
            cv2.rectangle(img, (int(x), int(y)), (int(x+bw), int(y+bh)), (0, 0, 255), 2)

# index nums (6 cols, 10 rows)
draw_block(75, 920, 40, 25, "vertical", 6, 10)

# C1 (1 col, 10 rows)
draw_block(225, 920, 40, 0, "vertical", 1, 10)

# C2 (1 col, 9 rows)
draw_block(260, 920, 40, 0, "vertical", 1, 9)

# Q1-20 (20 rows, 5 cols)
draw_block(100, 1645, 62, 64, "horizontal", 20, 5)

# Q21-40
draw_block(830, 1645, 62, 64, "horizontal", 20, 5)

# Q41-60
draw_block(1620, 1645, 62, 64, "horizontal", 20, 5)

cv2.imwrite("uploads/boxes_image2.jpg", img)
print("Boxes image 2 saved.")
