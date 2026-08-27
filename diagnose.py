"""
Comprehensive OMR calibration diagnostic.
Processes all sample images and compares against results.csv.
Outputs detailed statistics to help identify systematic issues.
"""
import os, sys, json
import numpy as np
import cv2
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from omr_engine_wrapper import align_image

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'Samples')
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'eval_temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# Load template
template_path = os.path.join(os.path.dirname(__file__), 'templates', 'template_uom_60q.json')
with open(template_path) as f:
    template = json.load(f)

# Load ground truth
import pandas as pd
df = pd.read_csv(os.path.join(SAMPLES_DIR, 'results.csv'))
expected = {}
for col in df.columns[1:]:
    expected[col] = {
        'Index': str(df[col][0]),
        'responses': [str(x) if str(x) != 'nan' else '-' for x in df[col][1:]]
    }

# Row Y coordinates
row_ys = [1647, 1729, 1812, 1895, 1977, 2060, 2143, 2224, 2307, 2389,
          2473, 2555, 2638, 2721, 2803, 2886, 2969, 3050, 3133, 3216]

options = ['A', 'B', 'C', 'D', 'E']

def measure_bubble(img_gray, bx, by, box_w, box_h):
    """Return multiple metrics for a bubble ROI."""
    roi = img_gray[by:by+box_h, bx:bx+box_w]
    if roi.size == 0:
        return {'sum': 0.0, 'mean_dark': 0.0, 'dark_pixels': 0, 'median': 0.0, 'p10': 0.0, 'bg': 0.0}
    bg = np.percentile(roi, 90)
    diff = np.maximum(0, bg - roi.astype(np.float64))
    return {
        'sum': float(np.sum(diff)),
        'mean_dark': float(np.mean(diff)),
        'dark_pixels': int(np.sum(diff > 15)),
        'median': float(np.median(roi)),
        'p10': float(np.percentile(roi, 10)),
        'bg': float(bg),
    }

# Collect all data
all_data = {}
for fid_int in range(11):
    fid = str(fid_int)
    heic_path = os.path.join(SAMPLES_DIR, f"{fid}.heic")
    if not os.path.exists(heic_path):
        continue
    
    img_pil = Image.open(heic_path).convert("RGB")
    jpg_path = os.path.join(TEMP_DIR, f"{fid}.jpg")
    img_pil.save(jpg_path, "JPEG")
    
    img = cv2.imread(jpg_path, cv2.IMREAD_GRAYSCALE)
    img_color = cv2.imread(jpg_path)
    img, img_color = align_image(img, img_color)
    
    file_data = {'q': {}, 'idx': {}}
    
    # Extract question data for all 3 blocks
    for block_name in ['q1_20', 'q21_40', 'q41_60']:
        b = template['fieldBlocks'][block_name]
        q_box_w, q_box_h = b.get('bubbleDimensions', [44, 18])
        for r, field_label in enumerate(b['fieldLabels']):
            q_num = int(field_label[1:])
            orig_x = int(b['origin'][0])
            orig_y = row_ys[r]
            
            adj_x = orig_x - 5
            adj_y = orig_y - 5
            adj_w = q_box_w + 10
            adj_h = q_box_h + 10
            
            bubble_metrics = []
            for i in range(5):
                bx = int(adj_x + i * b['bubblesGap'])
                by = adj_y
                m = measure_bubble(img, bx, by, adj_w, adj_h)
                bubble_metrics.append(m)
            
            file_data['q'][q_num] = bubble_metrics
    
    # Extract index data  
    if 'index_nums' in template['fieldBlocks']:
        b = template['fieldBlocks']['index_nums']
        idx_box_w, idx_box_h = b.get('bubbleDimensions', [44, 30])
        for col in range(6):
            origin_x = b['origin'][0] + col * b['bubblesGap']
            origin_y = b['origin'][1]
            digit_metrics = []
            for digit in range(10):
                bx = int(origin_x) - 5
                by = int(origin_y + digit * b['labelsGap']) - 5
                m = measure_bubble(img, bx, by, idx_box_w + 10, idx_box_h + 10)
                digit_metrics.append(m)
            file_data['idx'][f'D{col+1}'] = digit_metrics
    
    if 'index_char1' in template['fieldBlocks']:
        b = template['fieldBlocks']['index_char1']
        idx_box_w, idx_box_h = b.get('bubbleDimensions', [44, 30])
        char_metrics = []
        for i in range(10):
            bx = int(b['origin'][0]) - 5
            by = int(b['origin'][1] + i * b['labelsGap']) - 5
            m = measure_bubble(img, bx, by, idx_box_w + 10, idx_box_h + 10)
            char_metrics.append(m)
        file_data['idx']['C1'] = char_metrics
    
    if 'index_char2' in template['fieldBlocks']:
        b = template['fieldBlocks']['index_char2']
        idx_box_w, idx_box_h = b.get('bubbleDimensions', [44, 30])
        n_choices = len(b['bubbleValues'])
        char_metrics = []
        for i in range(n_choices):
            bx = int(b['origin'][0]) - 5
            by = int(b['origin'][1] + i * b['labelsGap']) - 5
            m = measure_bubble(img, bx, by, idx_box_w + 10, idx_box_h + 10)
            char_metrics.append(m)
        file_data['idx']['C2'] = char_metrics
    
    all_data[fid] = file_data
    print(f"Processed file {fid}", flush=True)

# ========== ANALYSIS ==========

print("\n" + "="*80)
print("QUESTION ANSWER ANALYSIS")
print("="*80)

# Categorize mismatches
wrong_answer = []
false_blank = []
false_detect = []
correct = 0
total = 0

for fid in sorted(all_data.keys(), key=int):
    exp = expected[fid]['responses']
    for q in range(1, 61):
        total += 1
        metrics = all_data[fid]['q'][q]
        sums = [m['sum'] for m in metrics]
        dark_px = [m['dark_pixels'] for m in metrics]
        
        max_idx = int(np.argmax(sums))
        max_val = sums[max_idx]
        sorted_sums = sorted(sums, reverse=True)
        
        ans = '-'
        if max_val > 2000:
            if sorted_sums[1] <= max_val * 0.80:
                ans = options[max_idx]
        
        exp_ans = exp[q-1]
        
        if ans == exp_ans:
            correct += 1
        elif exp_ans == '-' and ans != '-':
            false_detect.append((fid, q, ans, sums, dark_px))
        elif exp_ans != '-' and ans == '-':
            false_blank.append((fid, q, exp_ans, sums, dark_px))
        else:
            wrong_answer.append((fid, q, exp_ans, ans, sums, dark_px))

print(f"\nTotal questions: {total}")
print(f"Correct: {correct} ({100*correct/total:.1f}%)")
print(f"Wrong answer: {len(wrong_answer)}")
print(f"False blank (should have answer): {len(false_blank)}")
print(f"False detect (should be blank): {len(false_detect)}")

print(f"\n--- FALSE BLANKS (engine says '-', ground truth has answer) ---")
for fid, q, exp_ans, sums, dpx in sorted(false_blank, key=lambda x: (int(x[0]), x[1])):
    exp_idx = options.index(exp_ans)
    max_idx = int(np.argmax(sums))
    max_val = max(sums)
    sorted_sums = sorted(sums, reverse=True)
    ratio = sorted_sums[1] / max(sorted_sums[0], 1.0) if sorted_sums[0] > 0 else 0
    exp_sum = sums[exp_idx]
    exp_rank = sorted(range(5), key=lambda i: -sums[i]).index(exp_idx) + 1
    print(f"F{fid:>2} Q{q:>2} exp={exp_ans} expSum={exp_sum:7.0f} expRank={exp_rank} maxSum={max_val:7.0f} ratio={ratio:.3f} sums={[int(s) for s in sums]}")

print(f"\n--- WRONG ANSWERS ---")
for fid, q, exp_ans, got, sums, dpx in sorted(wrong_answer, key=lambda x: (int(x[0]), x[1])):
    exp_idx = options.index(exp_ans)
    got_idx = options.index(got)
    print(f"F{fid:>2} Q{q:>2} exp={exp_ans} got={got} expSum={sums[exp_idx]:7.0f} gotSum={sums[got_idx]:7.0f} sums={[int(s) for s in sums]}")

print(f"\n--- FALSE DETECTS (engine picks letter, ground truth is '-') ---")
for fid, q, got, sums, dpx in sorted(false_detect, key=lambda x: (int(x[0]), x[1])):
    got_idx = options.index(got)
    sorted_sums = sorted(sums, reverse=True)
    ratio = sorted_sums[1] / max(sorted_sums[0], 1.0)
    print(f"F{fid:>2} Q{q:>2} got={got} gotSum={sums[got_idx]:7.0f} ratio={ratio:.3f} sums={[int(s) for s in sums]}")

print(f"\n--- PER-FILE BREAKDOWN ---")
for fid in sorted(all_data.keys(), key=int):
    exp = expected[fid]['responses']
    errs = 0
    for q in range(1, 61):
        metrics = all_data[fid]['q'][q]
        sums = [m['sum'] for m in metrics]
        max_idx = int(np.argmax(sums))
        max_val = sums[max_idx]
        sorted_sums = sorted(sums, reverse=True)
        ans = '-'
        if max_val > 2000:
            if sorted_sums[1] <= max_val * 0.80:
                ans = options[max_idx]
        if ans != exp[q-1]:
            errs += 1
    print(f"File {fid}: {errs}/60 mismatches")

# ========== INDEX ANALYSIS ==========
print("\n" + "="*80)
print("INDEX ANALYSIS")
print("="*80)

idx_chars_c1 = ['A','B','C','D','E','F','G','H','J','K']
idx_chars_c2 = ['L','M','N','P','R','T','U','V','X']

for fid in sorted(all_data.keys(), key=int):
    exp_idx = expected[fid]['Index']
    pred_idx = ""
    
    for d in range(6):
        key = f'D{d+1}'
        metrics = all_data[fid]['idx'][key]
        sums = [m['sum'] for m in metrics]
        max_idx = int(np.argmax(sums))
        sorted_sums = sorted(sums, reverse=True)
        ratio = sorted_sums[0] / max(sorted_sums[1], 1.0)
        pred_digit = str(max_idx) if ratio > 1.15 else '?'
        pred_idx += pred_digit
    
    if 'C1' in all_data[fid]['idx']:
        metrics = all_data[fid]['idx']['C1']
        sums = [m['sum'] for m in metrics]
        max_idx = int(np.argmax(sums))
        sorted_sums = sorted(sums, reverse=True)
        ratio = sorted_sums[0] / max(sorted_sums[1], 1.0)
        pred_char = idx_chars_c1[max_idx] if ratio > 1.15 else '?'
        pred_idx += pred_char
    
    if 'C2' in all_data[fid]['idx']:
        metrics = all_data[fid]['idx']['C2']
        sums = [m['sum'] for m in metrics]
        max_idx = int(np.argmax(sums))
        sorted_sums = sorted(sums, reverse=True)
        ratio = sorted_sums[0] / max(sorted_sums[1], 1.0)
        pred_char = idx_chars_c2[max_idx] if ratio > 1.15 else '?'
        pred_idx += pred_char
    
    pred_clean = pred_idx.replace('?', '')
    exp_clean = exp_idx.replace('-', '')
    match = 'MATCH' if pred_clean == exp_clean else 'MISMATCH'
    print(f"F{fid:>2}: pred={pred_idx:>10} exp={exp_idx:>10}  {match}")
    if match == 'MISMATCH':
        # Show details for each mismatched position
        for d in range(min(len(pred_idx), len(exp_idx))):
            if d < len(pred_idx) and d < len(exp_idx):
                if pred_idx[d] != exp_idx[d] and exp_idx[d] != '-':
                    key = f'D{d+1}' if d < 6 else ('C1' if d == 6 else 'C2')
                    if key in all_data[fid]['idx']:
                        metrics = all_data[fid]['idx'][key]
                        sums = [m['sum'] for m in metrics]
                        sorted_sums = sorted(sums, reverse=True)
                        ratio = sorted_sums[0] / max(sorted_sums[1], 1.0)
                        print(f"    pos {d}: pred={pred_idx[d]} exp={exp_idx[d]} ratio={ratio:.3f} top3={[int(s) for s in sorted_sums[:3]]}")
