import cv2
import json

img = cv2.imread("uploads/std_sample.png.jpg")
with open("templates/template_uom_60q.json", "r") as f:
    template = json.load(f)

bw, bh = template["bubbleDimensions"]

for block_name, block in template["fieldBlocks"].items():
    ox, oy = block["origin"]
    bg = block["bubblesGap"]
    lg = block["labelsGap"]
    dir = block["direction"]
    b_vals = block["bubbleValues"]
    f_lbls = block["fieldLabels"]
    
    for i, label in enumerate(f_lbls):
        for j, val in enumerate(b_vals):
            if dir == "horizontal":
                x = ox + j * bg
                y = oy + i * lg
            else:
                x = ox + i * lg
                y = oy + j * bg
            
            cv2.rectangle(img, (int(x), int(y)), (int(x+bw), int(y+bh)), (255, 0, 0), 2)

cv2.imwrite("uploads/boxes_image.jpg", img)
print("Boxes image saved.")
