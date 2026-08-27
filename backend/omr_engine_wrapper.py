import os
import cv2
import json
import numpy as np

def align_image(img_gray, img_color):
    """
    Detects 4 corner markers in the scanned image and warps it to match the digital Template.png exactly.
    Uses SIFT feature matching for scale and rotation invariant alignment.
    """
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "template_uom_60q.png")
    template_gray = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template_gray is None:
        print(f"Warning: Template not found at {template_path}. Proceeding without alignment.")
        return img_gray, img_color

    sift = cv2.SIFT_create(10000)
    
    # Create a mask for the TEMPLATE to hide repeating patterns (barcodes, bubbles)
    # This forces SIFT to match unique text features only.
    h, w = template_gray.shape
    mask = np.ones((h, w), dtype=np.uint8) * 255
    # Hide barcodes on the right
    mask[:, 2250:] = 0
    # Hide question bubbles
    mask[1500:3300, 100:2200] = 0
    # Hide index bubbles
    mask[750:1500, 100:1000] = 0
    
    kp1, des1 = sift.detectAndCompute(template_gray, mask)
    
    # Do NOT mask the input image, let it match features anywhere
    kp2, des2 = sift.detectAndCompute(img_gray, None)

    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    if len(good) < 50:
        print("Warning: Not enough good matches found. Proceeding without alignment.")
        return img_gray, img_color

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    M, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
    
    if M is None:
        print("Warning: Homography computation failed. Proceeding without alignment.")
        return img_gray, img_color

    h, w = template_gray.shape
    warped_gray = cv2.warpPerspective(img_gray, M, (w, h))
    warped_color = cv2.warpPerspective(img_color, M, (w, h))

    print(f"Alignment successful. Warped shape: {warped_gray.shape}")
    return warped_gray, warped_color

def read_row_darkness(img_gray, origin_x, origin_y, bubblesGap, num_choices, box_w, box_h, debug_img=None):
    """
    Read darkness at each bubble position in a row.
    Returns both sum-of-darkness and pixel-count metrics for each bubble.
    """
    sum_vals = []
    px_vals = []
    for i in range(num_choices):
        bx = int(origin_x + i * bubblesGap)
        by = int(origin_y)
        roi = img_gray[by:by+box_h, bx:bx+box_w]
            
        if roi.size > 0:
            bg = np.percentile(roi, 90)
            diff = bg - roi.astype(np.float64)
            sum_vals.append(float(np.sum(np.maximum(0, diff))))
            px_vals.append(int(np.sum(diff > 25)))  # count pixels significantly darker than bg
        else:
            sum_vals.append(0.0)
            px_vals.append(0)
                
        if debug_img is not None:
            cv2.rectangle(debug_img, (bx, by), (bx+box_w, by+box_h), (0, 255, 255), 1)
    return sum_vals, px_vals

def extract_bubbles(img_gray, origin, gap, num_bubbles, box_w, box_h, direction="horizontal", debug_img=None):
    """Legacy function kept for compatibility."""
    vals = []
    ox, oy = origin
    for i in range(num_bubbles):
        if direction == "horizontal":
            bx = int(ox + i * gap)
            by = int(oy)
        else:
            bx = int(ox)
            by = int(oy + i * gap)
        roi = img_gray[by:by+box_h, bx:bx+box_w]
        if roi.size > 0:
            bg = np.percentile(roi, 90)
            darkness = np.sum(np.maximum(0, bg - roi))
            vals.append(float(darkness))
        else:
            vals.append(0.0)
        if debug_img is not None:
            cv2.rectangle(debug_img, (bx, by), (bx+box_w, by+box_h), (0, 0, 255), 1)
    return vals

def process_omr_batch(image_paths, template_path, output_dir="results"):
    temp_dir = os.path.join(output_dir, "temp_omr_run")
    os.makedirs(temp_dir, exist_ok=True)
    
    with open(template_path, 'r') as f:
        template = json.load(f)
        
    box_w, box_h = template.get("bubbleDimensions", [25, 10])
    
    template_img_path = os.path.join(os.path.dirname(__file__), "..", "templates", "template_uom_60q.png")
    template_gray = cv2.imread(template_img_path, cv2.IMREAD_GRAYSCALE)
    
    results = []
    for img_path in image_paths:
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        img_color = cv2.imread(img_path)
        if img is None:
            continue
            
        img, img_color = align_image(img, img_color)
            
        row = [
            os.path.basename(img_path),
            img_path,
            os.path.join(temp_dir, os.path.basename(img_path)),
            "0",
            ""
        ]
        
        index_str = ""
        
        # Process index blocks - use vertical strip per digit column
        if "index_nums" in template["fieldBlocks"]:
            b = template["fieldBlocks"]["index_nums"]
            idx_box_w, idx_box_h = b.get("bubbleDimensions", [20, 20])
            for col in range(6):
                origin_x = b["origin"][0] + col * b["bubblesGap"]
                origin_y = b["origin"][1]
                vals = []
                for digit in range(10):
                    bx = int(origin_x) - 5
                    by = int(origin_y + digit * b["labelsGap"]) - 5
                    roi = img[by:by+idx_box_h+10, bx:bx+idx_box_w+10]
                    if roi.size > 0:
                        bg = np.percentile(roi, 90)
                        vals.append(float(np.sum(np.maximum(0, bg - roi))))
                    else:
                        vals.append(0.0)
                print(f"Col {col} vals: {vals}")
                # Find the darkest digit
                max_idx = int(np.argmax(vals))
                # Row darkness ratio: how much darker is the max vs the median?
                sorted_vals = sorted(vals, reverse=True)
                ratio = sorted_vals[0] / max(sorted_vals[1], 1.0)
                if ratio > 1.20:  # clearly dominant
                    index_str += str(max_idx)
                else:
                    index_str += "?"
                    
        if "index_char1" in template["fieldBlocks"]:
            b = template["fieldBlocks"]["index_char1"]
            idx_box_w, idx_box_h = b.get("bubbleDimensions", [20, 20])
            vals = []
            for i in range(10):
                bx = int(b["origin"][0]) - 5
                by = int(b["origin"][1] + i * b["labelsGap"]) - 5
                roi = img[by:by+idx_box_h+10, bx:bx+idx_box_w+10]
                if roi.size > 0:
                    bg = np.percentile(roi, 90)
                    vals.append(float(np.sum(np.maximum(0, bg - roi))))
                else:
                    vals.append(0.0)
            print(f"Char1 vals: {vals}")
            max_idx = int(np.argmax(vals))
            sorted_vals = sorted(vals, reverse=True)
            ratio = sorted_vals[0] / max(sorted_vals[1], 1.0)
            if ratio > 2.05:
                index_str += b["bubbleValues"][max_idx]
            else:
                index_str += "?"
                
        if "index_char2" in template["fieldBlocks"]:
            b = template["fieldBlocks"]["index_char2"]
            idx_box_w, idx_box_h = b.get("bubbleDimensions", [20, 20])
            vals = []
            n_choices = len(b["bubbleValues"])
            for i in range(n_choices):
                bx = int(b["origin"][0]) - 5
                by = int(b["origin"][1] + i * b["labelsGap"]) - 5
                roi = img[by:by+idx_box_h+10, bx:bx+idx_box_w+10]
                if roi.size > 0:
                    bg = np.percentile(roi, 90)
                    vals.append(float(np.sum(np.maximum(0, bg - roi))))
                else:
                    vals.append(0.0)
            print(f"Char2 vals: {vals}")
            max_idx = int(np.argmax(vals))
            sorted_vals = sorted(vals, reverse=True)
            ratio = sorted_vals[0] / max(sorted_vals[1], 1.0)
            if ratio > 2.05:
                index_str += b["bubbleValues"][max_idx]
            else:
                index_str += "?"
                
        row[4] = index_str.replace("?", "")
        
        # Process questions 1-60
        q_blocks = [k for k in template["fieldBlocks"].keys() if k.startswith("q")]
        q_blocks = sorted(q_blocks, key=lambda x: int(x.split('_')[0][1:]))
        
        q_results = {}
        # Explicit Y coordinates for the 20 rows of bubbles in the template
        row_ys = [1647, 1729, 1812, 1895, 1977, 2060, 2143, 2224, 2307, 2389, 
                  2473, 2555, 2638, 2721, 2803, 2886, 2969, 3050, 3133, 3216]
                  
        for block_name in q_blocks:
            b = template["fieldBlocks"][block_name]
            if "bubbleValues" not in b:
                continue
            q_box_w, q_box_h = b.get("bubbleDimensions", [box_w, box_h])
            drift_x = b.get("driftPerRow", 0.0)
            num_choices = len(b["bubbleValues"])
            
            for r, field_label in enumerate(b["fieldLabels"]):
                orig_x = int(b["origin"][0] + r * drift_x)
                # Use the exact Y coordinate from the template for this row
                orig_y = row_ys[r]
                
                # Increase box size by 10 pixels to tolerate minor local distortions
                adj_x = orig_x - 5
                adj_y = orig_y - 5
                adj_w = q_box_w + 10
                adj_h = q_box_h + 10
                
                # Read darkness at each bubble position in this row
                sum_vals, px_vals = read_row_darkness(img, adj_x, adj_y, b["bubblesGap"], num_choices, adj_w, adj_h, img_color)
                
                print(f"{field_label} sum_vals: {sum_vals} px_vals: {px_vals}")
                
                # Use sum-of-darkness with relative (min-subtracted) values
                # sum_rel metric: subtract per-row minimum to normalize background variation
                min_v = min(sum_vals)
                adj_vals = [v - min_v for v in sum_vals]
                
                max_idx = int(np.argmax(adj_vals))
                max_val = float(adj_vals[max_idx])
                
                ans = "-"
                if max_val > 100.0:
                    sorted_vals = sorted(adj_vals, reverse=True)
                    if sorted_vals[1] <= max_val * 0.90:
                        ans = b["bubbleValues"][max_idx]
                        
                q_results[field_label] = ans
            
        for i in range(1, 61):
            row.append(q_results.get(f"q{i}", ""))
            
        results.append(row)
        
    return results
