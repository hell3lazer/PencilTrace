"""
Extract multiple darkness metrics from all sample images and optimize.
Tests: raw sum, pixel count, mean darkness, percentile-based metrics.
"""
import os, sys, json
import numpy as np
import cv2
from PIL import Image
import pillow_heif
import pandas as pd
import pickle

pillow_heif.register_heif_opener()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from omr_engine_wrapper import align_image

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'Samples')
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'eval_temp')
os.makedirs(TEMP_DIR, exist_ok=True)

template_path = os.path.join(os.path.dirname(__file__), 'templates', 'template_uom_60q.json')
with open(template_path) as f:
    template = json.load(f)

df = pd.read_csv(os.path.join(SAMPLES_DIR, 'results.csv'))
expected = {}
for col in df.columns[1:]:
    expected[col] = {
        'Index': str(df[col][0]),
        'responses': [str(x) if str(x) != 'nan' else '-' for x in df[col][1:]]
    }

row_ys = [1647, 1729, 1812, 1895, 1977, 2060, 2143, 2224, 2307, 2389,
          2473, 2555, 2638, 2721, 2803, 2886, 2969, 3050, 3133, 3216]
options = ['A', 'B', 'C', 'D', 'E']

def extract_metrics(img_gray, bx, by, box_w, box_h):
    """Extract multiple metrics from a bubble ROI."""
    roi = img_gray[by:by+box_h, bx:bx+box_w]
    if roi.size == 0:
        return {'sum': 0, 'px15': 0, 'px20': 0, 'px25': 0, 'px30': 0,
                'mean_dark': 0, 'p10': 255, 'p25': 255, 'median': 255}
    
    bg = np.percentile(roi, 90)
    diff = bg - roi.astype(np.float64)
    pos_diff = np.maximum(0, diff)
    
    return {
        'sum': float(np.sum(pos_diff)),
        'px15': int(np.sum(diff > 15)),   # pixels > 15 darker than bg
        'px20': int(np.sum(diff > 20)),
        'px25': int(np.sum(diff > 25)),
        'px30': int(np.sum(diff > 30)),
        'mean_dark': float(np.mean(pos_diff)),
        'p10': float(np.percentile(roi, 10)),
        'p25': float(np.percentile(roi, 25)),
        'median': float(np.median(roi)),
    }

# ===== EXTRACT =====
cache_path = os.path.join(TEMP_DIR, 'multi_metrics.pkl')
if os.path.exists(cache_path):
    print("Loading cached metrics...")
    with open(cache_path, 'rb') as f:
        all_data = pickle.load(f)
else:
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
                    m = extract_metrics(img, bx, adj_y, adj_w, adj_h)
                    bubble_metrics.append(m)
                file_data['q'][q_num] = bubble_metrics
        
        # Index
        if 'index_nums' in template['fieldBlocks']:
            b = template['fieldBlocks']['index_nums']
            bw, bh = b.get('bubbleDimensions', [44, 30])
            for col in range(6):
                ox = b['origin'][0] + col * b['bubblesGap']
                oy = b['origin'][1]
                digit_metrics = []
                for digit in range(10):
                    bx = int(ox) - 5
                    by = int(oy + digit * b['labelsGap']) - 5
                    m = extract_metrics(img, bx, by, bw+10, bh+10)
                    digit_metrics.append(m)
                file_data['idx'][f'D{col+1}'] = digit_metrics
        
        if 'index_char1' in template['fieldBlocks']:
            b = template['fieldBlocks']['index_char1']
            bw, bh = b.get('bubbleDimensions', [44, 30])
            char_metrics = []
            for i in range(10):
                bx = int(b['origin'][0]) - 5
                by = int(b['origin'][1] + i * b['labelsGap']) - 5
                m = extract_metrics(img, bx, by, bw+10, bh+10)
                char_metrics.append(m)
            file_data['idx']['C1'] = char_metrics
        
        if 'index_char2' in template['fieldBlocks']:
            b = template['fieldBlocks']['index_char2']
            bw, bh = b.get('bubbleDimensions', [44, 30])
            nc = len(b['bubbleValues'])
            char_metrics = []
            for i in range(nc):
                bx = int(b['origin'][0]) - 5
                by = int(b['origin'][1] + i * b['labelsGap']) - 5
                m = extract_metrics(img, bx, by, bw+10, bh+10)
                char_metrics.append(m)
            file_data['idx']['C2'] = char_metrics
        
        all_data[fid] = file_data
        print(f"Processed file {fid}", flush=True)
    
    with open(cache_path, 'wb') as f:
        pickle.dump(all_data, f)
    print("Saved metrics cache.")

# ===== OPTIMIZE =====

def test_metric(metric_name, min_thresh, amb_ratio, use_relative=False):
    """Test a given metric with given thresholds."""
    mismatches = 0
    for fid in all_data:
        exp = expected[fid]['responses']
        for q in range(1, 61):
            metrics = all_data[fid]['q'][q]
            vals = [m[metric_name] for m in metrics]
            
            if use_relative:
                min_v = min(vals)
                vals = [v - min_v for v in vals]
            
            max_idx = int(np.argmax(vals))
            max_val = vals[max_idx]
            sv = sorted(vals, reverse=True)
            
            ans = '-'
            if max_val > min_thresh:
                if sv[1] <= max_val * amb_ratio:
                    ans = options[max_idx]
            
            if ans != exp[q-1]:
                mismatches += 1
    return mismatches

# Test all metrics
metric_configs = {
    'sum_raw': ('sum', False, range(1000, 8000, 250), np.arange(0.50, 0.96, 0.02)),
    'sum_rel': ('sum', True, range(500, 5000, 250), np.arange(0.30, 0.90, 0.02)),
    'px15_raw': ('px15', False, range(20, 300, 10), np.arange(0.30, 0.90, 0.02)),
    'px15_rel': ('px15', True, range(10, 200, 10), np.arange(0.30, 0.90, 0.02)),
    'px20_raw': ('px20', False, range(10, 200, 10), np.arange(0.30, 0.90, 0.02)),
    'px20_rel': ('px20', True, range(5, 150, 5), np.arange(0.30, 0.90, 0.02)),
    'px25_raw': ('px25', False, range(5, 150, 5), np.arange(0.30, 0.90, 0.02)),
    'px25_rel': ('px25', True, range(5, 100, 5), np.arange(0.30, 0.90, 0.02)),
    'px30_raw': ('px30', False, range(5, 100, 5), np.arange(0.30, 0.90, 0.02)),
    'px30_rel': ('px30', True, range(5, 80, 5), np.arange(0.30, 0.90, 0.02)),
    'mean_dark_raw': ('mean_dark', False, np.arange(0.5, 5.0, 0.25), np.arange(0.30, 0.90, 0.02)),
    'mean_dark_rel': ('mean_dark', True, np.arange(0.5, 5.0, 0.25), np.arange(0.30, 0.90, 0.02)),
}

print("\n" + "="*70)
print("METRIC COMPARISON")
print("="*70)

results = []
for config_name, (metric, use_rel, min_range, amb_range) in metric_configs.items():
    best = 9999
    best_p = None
    for mt in min_range:
        for ar in amb_range:
            m = test_metric(metric, mt, ar, use_rel)
            if m < best:
                best = m
                best_p = (float(mt), float(ar))
    results.append((config_name, best, best_p))
    print(f"{config_name:>16}: {best:>3} mismatches  (thresh={best_p[0]:.1f}, ratio={best_p[1]:.2f})")

# Find the overall best
results.sort(key=lambda x: x[1])
print(f"\nBest metric: {results[0][0]} with {results[0][1]} mismatches")
print(f"  Params: thresh={results[0][2][0]:.1f}, ratio={results[0][2][1]:.2f}")

# Show per-file breakdown for the best metric
best_name, best_mm, best_params = results[0]
metric_name = best_name.rsplit('_', 1)[0]
use_rel = best_name.endswith('_rel')
min_t, amb_r = best_params

print(f"\nPER-FILE BREAKDOWN ({best_name}):")
total_fb = 0
total_wa = 0
total_fd = 0
for fid in sorted(all_data.keys(), key=int):
    exp = expected[fid]['responses']
    errs = fb = wa = fd = 0
    for q in range(1, 61):
        metrics = all_data[fid]['q'][q]
        vals = [m[metric_name] for m in metrics]
        if use_rel:
            min_v = min(vals)
            vals = [v - min_v for v in vals]
        max_idx = int(np.argmax(vals))
        max_val = vals[max_idx]
        sv = sorted(vals, reverse=True)
        ans = '-'
        if max_val > min_t:
            if sv[1] <= max_val * amb_r:
                ans = options[max_idx]
        if ans != exp[q-1]:
            errs += 1
            if exp[q-1] == '-': fd += 1
            elif ans == '-': fb += 1
            else: wa += 1
    total_fb += fb; total_wa += wa; total_fd += fd
    print(f"  File {fid}: {errs:>2}/60  (blank={fb}, wrong={wa}, false_det={fd})")
print(f"  TOTAL: blank={total_fb}, wrong={total_wa}, false_det={total_fd}")

# ===== Also test combined metrics =====
print("\n" + "="*70)
print("TESTING COMBINED METRICS (sum + pixel count)")
print("="*70)

def test_combined(sum_weight, px_weight, px_metric, min_thresh, amb_ratio, use_rel):
    mismatches = 0
    for fid in all_data:
        exp = expected[fid]['responses']
        for q in range(1, 61):
            metrics = all_data[fid]['q'][q]
            vals = []
            for m in metrics:
                v = sum_weight * m['sum'] + px_weight * m[px_metric]
                vals.append(v)
            
            if use_rel:
                min_v = min(vals)
                vals = [v - min_v for v in vals]
            
            max_idx = int(np.argmax(vals))
            max_val = vals[max_idx]
            sv = sorted(vals, reverse=True)
            
            ans = '-'
            if max_val > min_thresh:
                if sv[1] <= max_val * amb_ratio:
                    ans = options[max_idx]
            if ans != exp[q-1]:
                mismatches += 1
    return mismatches

# Test a few combinations
best_combo = 9999
best_combo_params = None
for sw, pw in [(1, 0), (1, 10), (1, 20), (1, 50), (1, 100), (0, 1)]:
    for pm in ['px20', 'px25', 'px30']:
        for use_rel in [True, False]:
            for mt in np.arange(500, 10000, 500) if sw > 0 else range(10, 200, 10):
                for ar in np.arange(0.40, 0.90, 0.05):
                    m = test_combined(sw, pw, pm, mt, ar, use_rel)
                    if m < best_combo:
                        best_combo = m
                        best_combo_params = (sw, pw, pm, mt, ar, use_rel)

print(f"Best combined: {best_combo} mismatches")
print(f"  sum_weight={best_combo_params[0]}, px_weight={best_combo_params[1]}, px_metric={best_combo_params[2]}")
print(f"  thresh={best_combo_params[3]:.1f}, ratio={best_combo_params[4]:.2f}, relative={best_combo_params[5]}")
