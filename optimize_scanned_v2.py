"""
Advanced optimizer: try combined metrics, adaptive thresholds, and more pixel thresholds.
"""
import os, sys, json, pickle
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

TEMP_DIR = os.path.join(os.path.dirname(__file__), 'eval_temp_scanned')
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'Samples', 'Scanned')

import pandas as pd
df = pd.read_csv(os.path.join(SAMPLES_DIR, 'results.csv'))
expected = {}
for col in df.columns[1:]:
    idx_val = str(df[col].iloc[0])
    responses = [str(v) if str(v) != 'nan' else '-' for v in df[col].iloc[1:]]
    expected[col] = {'Index': idx_val, 'responses': responses}

with open(os.path.join(TEMP_DIR, 'scanned_metrics.pkl'), 'rb') as f:
    all_data = pickle.load(f)

options = ['A', 'B', 'C', 'D', 'E']

# Strategy 1: Try sum_raw with tighter settings
# The sum metric has much larger dynamic range so may better separate faint marks
def test_sum_raw(min_thresh, amb_ratio):
    mm = 0
    for fname in all_data:
        exp = expected[fname]['responses']
        for q in range(1, 61):
            metrics = all_data[fname]['q'][q]
            vals = [m['sum'] for m in metrics]
            max_idx = int(np.argmax(vals))
            max_val = vals[max_idx]
            sv = sorted(vals, reverse=True)
            ans = '-'
            if max_val > min_thresh:
                if sv[1] <= max_val * amb_ratio:
                    ans = options[max_idx]
            if ans != exp[q-1]:
                mm += 1
    return mm

# Strategy 2: Combined sum + px metric 
# Use sum as the primary metric, but also require px count to be above a minimum
def test_combined(sum_thresh, sum_ratio, px_metric, px_min):
    mm = 0
    for fname in all_data:
        exp = expected[fname]['responses']
        for q in range(1, 61):
            metrics = all_data[fname]['q'][q]
            sums = [m['sum'] for m in metrics]
            px = [m[px_metric] for m in metrics]
            
            max_idx = int(np.argmax(sums))
            max_sum = sums[max_idx]
            sv_sum = sorted(sums, reverse=True)
            
            ans = '-'
            if max_sum > sum_thresh:
                if sv_sum[1] <= max_sum * sum_ratio:
                    # Also check pixel count is reasonable
                    if px[max_idx] >= px_min:
                        ans = options[max_idx]
            if ans != exp[q-1]:
                mm += 1
    return mm

# Strategy 3: px25_rel with different row-specific handling
# Bottom rows (16-20 in each block) may need different thresholds
def test_px_adaptive(base_thresh, base_ratio, bottom_thresh, bottom_ratio, bottom_rows=5):
    mm = 0
    for fname in all_data:
        exp = expected[fname]['responses']
        for q in range(1, 61):
            # Determine if this is a "bottom row" question
            row_in_block = (q - 1) % 20
            is_bottom = row_in_block >= (20 - bottom_rows)
            
            thresh = bottom_thresh if is_bottom else base_thresh
            ratio = bottom_ratio if is_bottom else base_ratio
            
            metrics = all_data[fname]['q'][q]
            vals = [m['px25'] for m in metrics]
            min_v = min(vals)
            adj = [v - min_v for v in vals]
            max_idx = int(np.argmax(adj))
            max_val = adj[max_idx]
            sv = sorted(adj, reverse=True)
            
            ans = '-'
            if max_val > thresh:
                if sv[1] <= max_val * ratio:
                    ans = options[max_idx]
            if ans != exp[q-1]:
                mm += 1
    return mm

# Strategy 4: Use sum_rel (relative sum)
def test_sum_rel(min_thresh, amb_ratio):
    mm = 0
    for fname in all_data:
        exp = expected[fname]['responses']
        for q in range(1, 61):
            metrics = all_data[fname]['q'][q]
            vals = [m['sum'] for m in metrics]
            min_v = min(vals)
            adj = [v - min_v for v in vals]
            max_idx = int(np.argmax(adj))
            max_val = adj[max_idx]
            sv = sorted(adj, reverse=True)
            ans = '-'
            if max_val > min_thresh:
                if sv[1] <= max_val * amb_ratio:
                    ans = options[max_idx]
            if ans != exp[q-1]:
                mm += 1
    return mm

# Strategy 5: Dual check - px25 for confident marks, sum for faint marks 
def test_dual(px_thresh, px_ratio, sum_thresh, sum_ratio):
    mm = 0
    for fname in all_data:
        exp = expected[fname]['responses']
        for q in range(1, 61):
            metrics = all_data[fname]['q'][q]
            px = [m['px25'] for m in metrics]
            sums = [m['sum'] for m in metrics]
            
            min_px = min(px)
            adj_px = [v - min_px for v in px]
            max_px_idx = int(np.argmax(adj_px))
            max_px_val = adj_px[max_px_idx]
            sv_px = sorted(adj_px, reverse=True)
            
            # Try px25 first
            ans = '-'
            if max_px_val > px_thresh:
                if sv_px[1] <= max_px_val * px_ratio:
                    ans = options[max_px_idx]
            
            # If px25 says blank, try sum as fallback
            if ans == '-':
                max_sum_idx = int(np.argmax(sums))
                max_sum_val = sums[max_sum_idx]
                sv_sum = sorted(sums, reverse=True)
                if max_sum_val > sum_thresh:
                    if sv_sum[1] <= max_sum_val * sum_ratio:
                        ans = options[max_sum_idx]
            
            if ans != exp[q-1]:
                mm += 1
    return mm

print("Strategy 1: sum_raw grid search")
best = 9999
for t in range(500, 20000, 250):
    for r in np.arange(0.30, 0.96, 0.02):
        m = test_sum_raw(t, r)
        if m < best:
            best = m
            bp = (t, r)
print(f"  Best: {best} mismatches (thresh={bp[0]}, ratio={bp[1]:.2f})")

print("\nStrategy 2: sum_raw + px25 minimum")
best2 = 9999
for st in [500, 1000, 2000, 3000, 5000]:
    for sr in np.arange(0.50, 0.96, 0.02):
        for pm in [0, 1, 2, 3, 5, 8, 10, 15]:
            m = test_combined(st, sr, 'px25', pm)
            if m < best2:
                best2 = m
                bp2 = (st, sr, pm)
print(f"  Best: {best2} mismatches (sum_thresh={bp2[0]}, sum_ratio={bp2[1]:.2f}, px_min={bp2[2]})")

print("\nStrategy 3: px25_rel adaptive (different thresholds for bottom rows)")
best3 = 9999
for bt in [2, 4, 6, 8, 10]:
    for br in np.arange(0.40, 0.96, 0.04):
        for btt in [2, 4, 6, 8, 10]:
            for btr in np.arange(0.40, 0.96, 0.04):
                m = test_px_adaptive(bt, br, btt, btr, bottom_rows=5)
                if m < best3:
                    best3 = m
                    bp3 = (bt, br, btt, btr)
print(f"  Best: {best3} mismatches (base_t={bp3[0]}, base_r={bp3[1]:.2f}, bot_t={bp3[2]}, bot_r={bp3[3]:.2f})")

print("\nStrategy 4: sum_rel grid search")
best4 = 9999
for t in range(100, 15000, 100):
    for r in np.arange(0.50, 0.96, 0.02):
        m = test_sum_rel(t, r)
        if m < best4:
            best4 = m
            bp4 = (t, r)
print(f"  Best: {best4} mismatches (thresh={bp4[0]}, ratio={bp4[1]:.2f})")

print("\nStrategy 5: Dual (px25_rel primary, sum fallback)")
best5 = 9999
for pt in [2, 4, 6, 8, 10, 15]:
    for pr in np.arange(0.50, 0.96, 0.04):
        for st in [500, 1000, 2000, 3000, 5000, 8000]:
            for sr in np.arange(0.40, 0.80, 0.04):
                m = test_dual(pt, pr, st, sr)
                if m < best5:
                    best5 = m
                    bp5 = (pt, pr, st, sr)
print(f"  Best: {best5} mismatches (px_t={bp5[0]}, px_r={bp5[1]:.2f}, sum_t={bp5[2]}, sum_r={bp5[3]:.2f})")

print("\n" + "="*60)
print("COMPARISON SUMMARY")
print(f"  Current engine (px25_rel t=5, r=0.56): 107")
print(f"  Strategy 1 (sum_raw):                  {best}")
print(f"  Strategy 2 (sum+px combined):           {best2}")
print(f"  Strategy 3 (px25_rel adaptive):         {best3}")
print(f"  Strategy 4 (sum_rel):                   {best4}")
print(f"  Strategy 5 (dual px25+sum):             {best5}")
print(f"  Previous best (px25_rel t=2,r=0.92):    86")

# Show per-file for best
print("\nBest strategy per-file:")
