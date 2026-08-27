"""
Comprehensive parameter optimizer for OMR calibration.
Tests multiple darkness metrics and thresholds against ground truth.
"""
import os, sys, json, re
import numpy as np
import pandas as pd

# Load ground truth
df = pd.read_csv('../Samples/results.csv')
expected = {}
for col in df.columns[1:]:
    expected[col] = {
        'Index': str(df[col][0]),
        'responses': [str(x) if str(x) != 'nan' else '-' for x in df[col][1:]]
    }

# Parse eval_out.txt to get raw darkness values
blocks = {}
current_block = {'col': {}, 'char1': None, 'char2': None, 'q': {}}

with open('eval_out.txt', 'r', encoding='utf-16le') as f:
    for line in f:
        line = line.strip()
        if line.startswith('Col '):
            m = re.match(r'Col (\d) vals: \[(.*)\]', line)
            if m:
                col_idx = int(m.group(1))
                vals = [float(x.strip()) for x in m.group(2).split(',') if x.strip()]
                current_block['col'][col_idx] = vals
        elif line.startswith('Char1 '):
            m = re.match(r'Char1 vals: \[(.*)\]', line)
            if m:
                vals = [float(x.strip()) for x in m.group(1).split(',') if x.strip()]
                current_block['char1'] = vals
        elif line.startswith('Char2 '):
            m = re.match(r'Char2 vals: \[(.*)\]', line)
            if m:
                vals = [float(x.strip()) for x in m.group(1).split(',') if x.strip()]
                current_block['char2'] = vals
        elif line.startswith('q'):
            m = re.match(r'(q\d+) vals: \[(.*)\]', line)
            if m:
                q_id = int(m.group(1)[1:])
                raw_vals = m.group(2).replace(',', ' ').split()
                vals = [float(x) for x in raw_vals]
                current_block['q'][q_id] = vals
        elif line.startswith('--- File '):
            m = re.search(r'File (\d+)\.heic', line)
            if m:
                fid = m.group(1)
                blocks[fid] = current_block
                current_block = {'col': {}, 'char1': None, 'char2': None, 'q': {}}

options = ['A', 'B', 'C', 'D', 'E']

def test_q_params_relative(min_darkness, ambiguity_ratio):
    """Test using min-subtracted relative values."""
    mismatches = 0
    for fid, data in blocks.items():
        exp = expected[fid]['responses']
        for q_id in range(1, 61):
            if q_id not in data['q']: continue
            vals = data['q'][q_id]
            min_val = min(vals)
            adj = [v - min_val for v in vals]
            max_idx = int(np.argmax(adj))
            max_val = adj[max_idx]
            sorted_adj = sorted(adj, reverse=True)
            ans = '-'
            if max_val > min_darkness:
                if sorted_adj[1] > max_val * ambiguity_ratio:
                    ans = '-'
                else:
                    ans = options[max_idx]
            if ans != exp[q_id-1]:
                mismatches += 1
    return mismatches

def test_q_params_median(min_darkness, ambiguity_ratio):
    """Test using median-subtracted values."""
    mismatches = 0
    for fid, data in blocks.items():
        exp = expected[fid]['responses']
        for q_id in range(1, 61):
            if q_id not in data['q']: continue
            vals = data['q'][q_id]
            med = np.median(vals)
            adj = [max(0, v - med) for v in vals]
            max_idx = int(np.argmax(adj))
            max_val = adj[max_idx]
            sorted_adj = sorted(adj, reverse=True)
            ans = '-'
            if max_val > min_darkness:
                if sorted_adj[1] > max_val * ambiguity_ratio:
                    ans = '-'
                else:
                    ans = options[max_idx]
            if ans != exp[q_id-1]:
                mismatches += 1
    return mismatches

def test_q_params_raw(min_darkness, ambiguity_ratio):
    """Test raw values (current approach)."""
    mismatches = 0
    for fid, data in blocks.items():
        exp = expected[fid]['responses']
        for q_id in range(1, 61):
            if q_id not in data['q']: continue
            vals = data['q'][q_id]
            max_idx = int(np.argmax(vals))
            max_val = vals[max_idx]
            sorted_vals = sorted(vals, reverse=True)
            ans = '-'
            if max_val > min_darkness:
                if sorted_vals[1] > max_val * ambiguity_ratio:
                    ans = '-'
                else:
                    ans = options[max_idx]
            if ans != exp[q_id-1]:
                mismatches += 1
    return mismatches

def test_q_hybrid(rel_min, rel_ratio, abs_min, abs_ratio):
    """
    Hybrid: use relative (min-subtracted) for primary decision,
    but also accept raw absolute values above a high threshold.
    """
    mismatches = 0
    for fid, data in blocks.items():
        exp = expected[fid]['responses']
        for q_id in range(1, 61):
            if q_id not in data['q']: continue
            vals = data['q'][q_id]
            
            # Relative metric
            min_val = min(vals)
            adj = [v - min_val for v in vals]
            max_idx_rel = int(np.argmax(adj))
            max_val_rel = adj[max_idx_rel]
            sorted_adj = sorted(adj, reverse=True)
            
            ans = '-'
            if max_val_rel > rel_min:
                if sorted_adj[1] <= max_val_rel * rel_ratio:
                    ans = options[max_idx_rel]
            
            if ans != exp[q_id-1]:
                mismatches += 1
    return mismatches

# ======================== OPTIMIZE ========================

print("="*60)
print("TESTING RAW VALUES (current approach)")
print("="*60)
best = 9999
best_params = None
for min_dark in range(1000, 8000, 250):
    for amb in np.arange(0.50, 0.98, 0.02):
        m = test_q_params_raw(min_dark, amb)
        if m < best:
            best = m
            best_params = (min_dark, amb)
print(f"Best raw: min_darkness={best_params[0]}, ratio={best_params[1]:.2f} -> {best} mismatches")

print("\n" + "="*60)
print("TESTING MIN-SUBTRACTED VALUES")
print("="*60)
best_rel = 9999
best_rel_params = None
for min_dark in range(200, 5000, 100):
    for amb in np.arange(0.30, 0.90, 0.02):
        m = test_q_params_relative(min_dark, amb)
        if m < best_rel:
            best_rel = m
            best_rel_params = (min_dark, amb)
print(f"Best min-sub: min_darkness={best_rel_params[0]}, ratio={best_rel_params[1]:.2f} -> {best_rel} mismatches")

print("\n" + "="*60)
print("TESTING MEDIAN-SUBTRACTED VALUES")
print("="*60)
best_med = 9999
best_med_params = None
for min_dark in range(200, 5000, 100):
    for amb in np.arange(0.30, 0.90, 0.02):
        m = test_q_params_median(min_dark, amb)
        if m < best_med:
            best_med = m
            best_med_params = (min_dark, amb)
print(f"Best median-sub: min_darkness={best_med_params[0]}, ratio={best_med_params[1]:.2f} -> {best_med} mismatches")

# Show detailed breakdown for best relative approach
print("\n" + "="*60)
print(f"DETAILED BREAKDOWN (min-sub, darkness={best_rel_params[0]}, ratio={best_rel_params[1]:.2f})")
print("="*60)

min_d, amb_r = best_rel_params
false_blank = 0
false_detect = 0
wrong_ans = 0

for fid in sorted(blocks.keys(), key=int):
    data = blocks[fid]
    exp = expected[fid]['responses']
    errs = 0
    for q_id in range(1, 61):
        if q_id not in data['q']: continue
        vals = data['q'][q_id]
        min_val = min(vals)
        adj = [v - min_val for v in vals]
        max_idx = int(np.argmax(adj))
        max_val = adj[max_idx]
        sorted_adj = sorted(adj, reverse=True)
        ans = '-'
        if max_val > min_d:
            if sorted_adj[1] <= max_val * amb_r:
                ans = options[max_idx]
        if ans != exp[q_id-1]:
            errs += 1
            if exp[q_id-1] == '-':
                false_detect += 1
            elif ans == '-':
                false_blank += 1
            else:
                wrong_ans += 1
    print(f"File {fid}: {errs}/60 mismatches")

print(f"\nFalse blanks: {false_blank}")
print(f"Wrong answer: {wrong_ans}")
print(f"False detect: {false_detect}")

# ======================== INDEX OPTIMIZATION ========================
print("\n" + "="*60)
print("INDEX OPTIMIZATION")
print("="*60)

idx_chars_c1 = ['A','B','C','D','E','F','G','H','J','K']
idx_chars_c2 = ['L','M','N','P','R','T','U','V','X']

def test_idx(digit_ratio, char_ratio):
    """Test index with separate thresholds for digits and chars."""
    total_char_errs = 0
    for fid, data in blocks.items():
        exp_idx = expected[fid]['Index']
        pred = ""
        
        for i in range(6):
            if i in data['col']:
                vals = data['col'][i]
                max_idx = int(np.argmax(vals))
                sv = sorted(vals, reverse=True)
                ratio = sv[0] / max(sv[1], 1.0)
                if ratio > digit_ratio:
                    pred += str(max_idx)
                else:
                    pred += '?'
            else:
                pred += '?'
        
        if data['char1']:
            vals = data['char1']
            max_idx = int(np.argmax(vals))
            sv = sorted(vals, reverse=True)
            ratio = sv[0] / max(sv[1], 1.0)
            if ratio > char_ratio:
                pred += idx_chars_c1[max_idx]
            else:
                pred += '?'
        
        if data['char2']:
            vals = data['char2']
            max_idx = int(np.argmax(vals))
            sv = sorted(vals, reverse=True)
            ratio = sv[0] / max(sv[1], 1.0)
            if ratio > char_ratio:
                pred += idx_chars_c2[max_idx]
            else:
                pred += '?'
        
        pred_clean = pred.replace('?', '')
        exp_clean = exp_idx.replace('-', '')
        if pred_clean != exp_clean:
            total_char_errs += 1
    
    return total_char_errs

best_idx = 9999
best_idx_params = None
for dr in np.arange(1.05, 2.0, 0.05):
    for cr in np.arange(1.05, 2.5, 0.05):
        m = test_idx(dr, cr)
        if m < best_idx:
            best_idx = m
            best_idx_params = (dr, cr)

print(f"Best idx params: digit_ratio={best_idx_params[0]:.2f}, char_ratio={best_idx_params[1]:.2f} -> {best_idx} mismatches")

# Show index details for best params
dr, cr = best_idx_params
for fid in sorted(blocks.keys(), key=int):
    data = blocks[fid]
    exp_idx = expected[fid]['Index']
    pred = ""
    
    for i in range(6):
        if i in data['col']:
            vals = data['col'][i]
            max_idx = int(np.argmax(vals))
            sv = sorted(vals, reverse=True)
            ratio = sv[0] / max(sv[1], 1.0)
            if ratio > dr:
                pred += str(max_idx)
            else:
                pred += '?'
    
    if data['char1']:
        vals = data['char1']
        max_idx = int(np.argmax(vals))
        sv = sorted(vals, reverse=True)
        ratio = sv[0] / max(sv[1], 1.0)
        if ratio > cr:
            pred += idx_chars_c1[max_idx]
        else:
            pred += '?'
    
    if data['char2']:
        vals = data['char2']
        max_idx = int(np.argmax(vals))
        sv = sorted(vals, reverse=True)
        ratio = sv[0] / max(sv[1], 1.0)
        if ratio > cr:
            pred += idx_chars_c2[max_idx]
        else:
            pred += '?'
    
    pred_clean = pred.replace('?', '')
    exp_clean = exp_idx.replace('-', '')
    match = 'OK' if pred_clean == exp_clean else 'FAIL'
    print(f"  F{fid:>2}: pred={pred:>10} -> {pred_clean:>10}  exp={exp_idx:>10} -> {exp_clean:>10}  {match}")
