import json
import cv2

template = {
    "templateName": "uom_60q",
    "imageSize": [2480, 3508],
    "bubbleDimensions": [30, 35],
    "emptyValue": "",
    "customLabels": {
        "index_nums": ["D1", "D2", "D3", "D4", "D5", "D6"],
        "index_char1": ["C1"],
        "index_char2": ["C2"]
    },
    "fieldBlocks": {
        "index_nums": {
            "origin": [98, 923],
            "bubblesGap": 60.0,
            "labelsGap": 40.0,
            "direction": "vertical",
            "bubbleValues": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            "fieldLabels": ["D1", "D2", "D3", "D4", "D5", "D6"]
        },
        "index_char1": {
            "origin": [478, 923],
            "bubblesGap": 60.0,
            "labelsGap": 40.0,
            "direction": "vertical",
            "bubbleValues": ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K"],
            "fieldLabels": ["C1"]
        },
        "index_char2": {
            "origin": [538, 923],
            "bubblesGap": 60.0,
            "labelsGap": 40.0,
            "direction": "vertical",
            "bubbleValues": ["L", "M", "N", "P", "R", "T", "U", "V", "X"],
            "fieldLabels": ["C2"]
        },
        "q1_20": {
            "origin": [200, 1665],
            "bubblesGap": 110.0,
            "labelsGap": 74.0,
            "direction": "horizontal",
            "bubbleDimensions": [60, 35],
            "bubbleValues": ["A", "B", "C", "D", "E"],
            "fieldLabels": [f"q{i}" for i in range(1, 21)]
        },
        "q21_40": {
            "origin": [860, 1665],
            "bubblesGap": 110.0,
            "labelsGap": 74.0,
            "direction": "horizontal",
            "bubbleDimensions": [60, 35],
            "bubbleValues": ["A", "B", "C", "D", "E"],
            "fieldLabels": [f"q{i}" for i in range(21, 41)]
        },
        "q41_60": {
            "origin": [1520, 1665],
            "bubblesGap": 110.0,
            "labelsGap": 74.0,
            "direction": "horizontal",
            "bubbleDimensions": [60, 35],
            "bubbleValues": ["A", "B", "C", "D", "E"],
            "fieldLabels": [f"q{i}" for i in range(41, 61)]
        }
    },
    "outputColumns": [
        "IndexNumber",
        *["q" + str(i) for i in range(1, 61)]
    ],
    "pageDimensions": [4080, 2296],
    "preProcessors": []
}

with open("templates/template_uom_60q.json", "w") as f:
    json.dump(template, f, indent=4)

print("Saved perfect template_uom_60q.json")

# Draw on image
img = cv2.imread("uploads/std_sample.png.jpg")
box_w, box_h = 30, 35
for b in template["fieldBlocks"].values():
    ox, oy = b["origin"]
    bgap = b["bubblesGap"]
    lgap = b["labelsGap"]
    direction = b["direction"]
    num_l = len(b["fieldLabels"])
    num_b = len(b["bubbleValues"])
    
    for i in range(num_l):
        for j in range(num_b):
            if direction == "horizontal":
                bx = int(ox + j * bgap)
                by = int(oy + i * lgap)
            else:
                bx = int(ox + i * bgap)
                by = int(oy + j * lgap)
            cv2.rectangle(img, (bx, by), (bx+box_w, by+box_h), (0, 0, 255), 2)
            
cv2.imwrite("uploads/final_test.jpg", img)
cv2.imwrite("uploads/final_test_thumb.jpg", cv2.resize(img, (600, 1000)))
