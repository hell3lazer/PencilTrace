import cv2
import fitz # PyMuPDF
import numpy as np
import json

def main():
    pdf_path = "b:/user/Antigravity/OMR/Template.pdf"
    doc = fitz.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(dpi=150) # Standard 150 DPI
    img_path = "temp_template.png"
    pix.save(img_path)

    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Thresholding
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rects = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        # We are looking for small rectangles (corner markers)
        # and boxes that might contain our bubbles.
        if 10 < area < 500:
            rects.append((x, y, w, h))
            
    # Sort and print some interesting ones
    print(f"Image dimensions: {img.shape[1]}x{img.shape[0]}")
    
    # Let's save a copy with bounding boxes for visual inspection if needed
    for (x, y, w, h) in rects:
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 1)
        
    cv2.imwrite("temp_template_boxes.png", img)
    print(f"Found {len(rects)} small components. Look at temp_template_boxes.png")

if __name__ == "__main__":
    main()
