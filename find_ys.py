import cv2
import numpy as np
tmpl = cv2.imread('templates/template_uom_60q.png', 0)
bubble_patch = tmpl[1647:1665, 217:261]
col_roi = tmpl[1600:3300, 217:261]
res = cv2.matchTemplate(col_roi, bubble_patch, cv2.TM_CCOEFF_NORMED)

ys = []
loc = np.where(res >= 0.5)
pts = list(zip(*loc[::-1]))
# sort by Y
pts.sort(key=lambda pt: pt[1])

for pt in pts:
    y = pt[1] + 1600
    if not ys or y - ys[-1] > 40:
        ys.append(y)
    elif res[pt[1], pt[0]] > res[ys[-1] - 1600, 0]:
        ys[-1] = y

print(f'Found {len(ys)} bubbles:')
print(ys)
