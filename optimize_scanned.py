"""
Multi-metric optimizer for Scanned sample images.
Extracts darkness data, then grid-searches optimal parameters.
"""
import os, sys, json, pickle
import numpy as np
import cv2
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from omr_engine_wrapper import align_image

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'Samples', 'Scanned')
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'eval_temp_scanned')
RESIZED_DIR = os.path.join(TEMP_DIR, 'resized')
os.makedirs(RESIZED_DIR, exist_ok=True)

template_path = os.path.join(os.path.dirname(__file__), 'templates', 'template_uom_60q.json')
with open(template_path) as f:
    template = json.load(f)

TEMPLATE_H, TEMPLATE_W = 3508, 2481

df = pd.read_csv(os.path.join(SAMPLES_DIR, 'results.csv'))
expected = {}
for col in df.columns[1:]:
    idx_val = str(df[col].iloc[0])
    responses = [str(v) if str(v) != 'nan' else '-' for v in df[col].iloc[1:]]
    expected[col] = {'Index': idx_val, 'responses': responses}

row_ys = [1647, 1729, 1812, 1895, 1977, 2060, 2143, 2224, 2307, 2389,
          2473, 2555, 2638, 2721, 2803, 2886, 2969, 3050, 3133, 3216]
options = ['A', 'B', 'C', 'D', 'E']

def extract_metrics(img_gray, bx, by, box_w, box_h):
    roi = img_gray[by:by+box_h, bx:bx+box_w]
    if roi.size == 0:
        return {'sum': 0, 'px15': 0, 'px20': 0, 'px25': 0, 'px30': 0, 'px40': 0, 'px50': 0}
    bg = np.percentile(roi, 90)
    diff = bg - roi.astype(np.float64)
    pos_diff = np.maximum(0, diff)
    return {
        'sum': float(np.sum(pos_diff)),
        'px15': int(np.sum(diff > 15)),
        'px20': int(np.sum(diff > 20)),
        'px25': int(np.sum(diff > 25)),
        'px30': int(np.sum(diff > 30)),
        'px40': int(np.sum(diff > 40)),
        'px50': int(np.sum(diff > 50)),
    }

cache_path = os.path.join(TEMP_DIR, 'scanned_metrics.pkl')
if os.path.exists(cache_path):
    print("Loading cached metrics...")
    with open(cache_path, 'rb') as f:
        all_data = pickle.load(f)
else:
    all_data = {}
    for filename in sorted(expected.keys()):
        img_path = os.path.join(SAMPLES_DIR, filename)
        if not os.path.exists(img_path):
            continue
        
        img_color = cv2.imread(img_path)
        h, w = img_color.shape[:2]
        if h > TEMPLATE_H * 1.5 or w > TEMPLATE_W * 1.5:
            img_color = cv2.resize(img_color, (TEMPLATE_W, TEMPLATE_H), interpolation=cv2.INTER_AREA)
        img = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
        
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
        
        all_data[filename] = file_data
        print(f"Processed {filename}", flush=True)
    
    with open(cache_path, 'wb') as f:
        pickle.dump(all_data, f)
    print("Saved cache.")

# ===== OPTIMIZE QUESTIONS =====

def test_metric(metric_name, min_thresh, amb_ratio, use_relative=False):
    mismatches = 0
    for fname in all_data:
        exp = expected[fname]['responses']
        for q in range(1, 61):
            metrics = all_data[fname]['q'][q]
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

print("\n" + "="*70)
print("METRIC COMPARISON (Scanned samples)")
print("="*70)

metric_configs = {
    'sum_raw': ('sum', False, range(1000, 20000, 500), np.arange(0.30, 0.95, 0.02)),
    'sum_rel': ('sum', True, range(500, 15000, 500), np.arange(0.30, 0.95, 0.02)),
    'px25_raw': ('px25', False, range(5, 200, 5), np.arange(0.30, 0.95, 0.02)),
    'px25_rel': ('px25', True, range(2, 100, 2), np.arange(0.30, 0.95, 0.02)),
    'px30_raw': ('px30', False, range(5, 200, 5), np.arange(0.30, 0.95, 0.02)),
    'px30_rel': ('px30', True, range(2, 100, 2), np.arange(0.30, 0.95, 0.02)),
    'px40_raw': ('px40', False, range(5, 200, 5), np.arange(0.30, 0.95, 0.02)),
    'px40_rel': ('px40', True, range(2, 100, 2), np.arange(0.30, 0.95, 0.02)),
    'px50_raw': ('px50', False, range(5, 200, 5), np.arange(0.30, 0.95, 0.02)),
    'px50_rel': ('px50', True, range(2, 100, 2), np.arange(0.30, 0.95, 0.02)),
}

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

results.sort(key=lambda x: x[1])
print(f"\nBest: {results[0][0]} -> {results[0][1]} mismatches  (thresh={results[0][2][0]:.1f}, ratio={results[0][2][1]:.2f})")

# Show per-file breakdown for the best
best_name, best_mm, best_params = results[0]
metric_name = best_name.rsplit('_', 1)[0]
use_rel = best_name.endswith('_rel')
min_t, amb_r = best_params

print(f"\nPER-FILE BREAKDOWN ({best_name}):")
for fname in sorted(all_data.keys()):
    exp = expected[fname]['responses']
    errs = fb = wa = fd = 0
    for q in range(1, 61):
        metrics = all_data[fname]['q'][q]
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
    print(f"  {fname}: {errs:>2}/60  (blank={fb}, wrong={wa}, false_det={fd})")

# ===== OPTIMIZE INDEX =====
print("\n" + "="*70)
print("INDEX OPTIMIZATION")
print("="*70)

idx_chars_c1 = ['A','B','C','D','E','F','G','H','J','K']
idx_chars_c2 = ['L','M','N','P','R','T','U','V','X']

def test_idx(digit_ratio, char_ratio):
    errs = 0
    for fname, data in all_data.items():
        exp_idx = expected[fname]['Index']
        pred = ""
        for i in range(6):
            key = f'D{i+1}'
            vals = [m['sum'] for m in data['idx'][key]]
            max_idx = int(np.argmax(vals))
            sv = sorted(vals, reverse=True)
            ratio = sv[0] / max(sv[1], 1.0)
            pred += str(max_idx) if ratio > digit_ratio else '?'
        if 'C1' in data['idx']:
            vals = [m['sum'] for m in data['idx']['C1']]
            max_idx = int(np.argmax(vals))
            sv = sorted(vals, reverse=True)
            ratio = sv[0] / max(sv[1], 1.0)
            pred += idx_chars_c1[max_idx] if ratio > char_ratio else '?'
        if 'C2' in data['idx']:
            vals = [m['sum'] for m in data['idx']['C2']]
            max_idx = int(np.argmax(vals))
            sv = sorted(vals, reverse=True)
            ratio = sv[0] / max(sv[1], 1.0)
            pred += idx_chars_c2[max_idx] if ratio > char_ratio else '?'
        
        pred_clean = pred.replace('?', '')
        exp_clean = exp_idx.replace('-', '')
        if pred_clean != exp_clean:
            errs += 1
    return errs

best_idx = 9999
best_idx_params = None
for dr in np.arange(1.05, 3.0, 0.05):
    for cr in np.arange(1.05, 5.0, 0.1):
        m = test_idx(dr, cr)
        if m < best_idx:
            best_idx = m
            best_idx_params = (dr, cr)

print(f"Best idx: digit_ratio={best_idx_params[0]:.2f}, char_ratio={best_idx_params[1]:.2f} -> {best_idx} mismatches")

# Show details
dr, cr = best_idx_params
for fname in sorted(all_data.keys()):
    data = all_data[fname]
    exp_idx = expected[fname]['Index']
    pred = ""
    for i in range(6):
        key = f'D{i+1}'
        vals = [m['sum'] for m in data['idx'][key]]
        max_idx = int(np.argmax(vals))
        sv = sorted(vals, reverse=True)
        ratio = sv[0] / max(sv[1], 1.0)
        pred += str(max_idx) if ratio > dr else '?'
    if 'C1' in data['idx']:
        vals = [m['sum'] for m in data['idx']['C1']]
        max_idx = int(np.argmax(vals))
        sv = sorted(vals, reverse=True)
        ratio = sv[0] / max(sv[1], 1.0)
        pred += idx_chars_c1[max_idx] if ratio > cr else '?'
    if 'C2' in data['idx']:
        vals = [m['sum'] for m in data['idx']['C2']]
        max_idx = int(np.argmax(vals))
        sv = sorted(vals, reverse=True)
        ratio = sv[0] / max(sv[1], 1.0)
        pred += idx_chars_c2[max_idx] if ratio > cr else '?'
    
    pred_clean = pred.replace('?', '')
    exp_clean = exp_idx.replace('-', '')
    match = 'OK' if pred_clean == exp_clean else 'FAIL'
    print(f"  {fname}: pred={pred:>12} -> {pred_clean:>10}  exp={exp_idx:>10} -> {exp_clean:>10}  {match}")
