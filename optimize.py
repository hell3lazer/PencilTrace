import re
import pandas as pd
import numpy as np
import itertools

df = pd.read_csv('../Samples/results.csv')
expected = {}
for col in df.columns[1:]:
    expected[col] = {
        'Index': str(df[col][0]),
        'responses': [str(x) if str(x) != 'nan' else '-' for x in df[col][1:]]
    }

blocks = {}
current_block = {'col': {}, 'char1': None, 'char2': None, 'q': {}}
file_id = None

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
                # NumPy print format: might have multiple spaces, no commas
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

def test_q_params(min_darkness, ambiguity_ratio):
    mismatches = 0
    for fid, data in blocks.items():
        exp = expected[fid]['responses']
        for q_id in range(1, 61):
            if q_id not in data['q']: continue
            vals = data['q'][q_id]
            max_idx = np.argmax(vals)
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

def test_idx_params(ambiguity_ratio):
    mismatches = 0
    for fid, data in blocks.items():
        exp_idx = expected[fid]['Index']
        idx_str = ""
        for i in range(6):
            if i in data['col']:
                vals = data['col'][i]
                max_idx = np.argmax(vals)
                sorted_vals = sorted(vals, reverse=True)
                ratio = sorted_vals[0] / max(sorted_vals[1], 1.0)
                if ratio > ambiguity_ratio:
                    idx_str += str(max_idx)
        if data['char1']:
            vals = data['char1']
            max_idx = np.argmax(vals)
            sorted_vals = sorted(vals, reverse=True)
            ratio = sorted_vals[0] / max(sorted_vals[1], 1.0)
            if ratio > ambiguity_ratio:
                chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K']
                idx_str += chars[max_idx] if max_idx < len(chars) else '?'
        if data['char2']:
            vals = data['char2']
            max_idx = np.argmax(vals)
            sorted_vals = sorted(vals, reverse=True)
            ratio = sorted_vals[0] / max(sorted_vals[1], 1.0)
            if ratio > ambiguity_ratio:
                chars = ['L', 'M', 'N', 'P', 'R', 'T', 'U', 'V', 'X']
                idx_str += chars[max_idx] if max_idx < len(chars) else '?'
        
        idx_str = idx_str.replace('?', '')
        if idx_str != exp_idx:
            mismatches += 1
    return mismatches

print("Optimizing Q params...")
best_q_mismatches = 9999
best_q_params = None
for min_dark in range(2000, 15000, 500):
    for amb_rat in np.arange(0.5, 0.95, 0.05):
        m = test_q_params(min_dark, amb_rat)
        if m < best_q_mismatches:
            best_q_mismatches = m
            best_q_params = (min_dark, amb_rat)

print(f"Best Q params: min_darkness={best_q_params[0]}, ambiguity_ratio={best_q_params[1]:.2f} -> Mismatches: {best_q_mismatches}")

print("Optimizing Idx params...")
best_idx_mismatches = 9999
best_idx_params = None
for amb_rat in np.arange(1.1, 2.5, 0.05):
    m = test_idx_params(amb_rat)
    if m < best_idx_mismatches:
        best_idx_mismatches = m
        best_idx_params = amb_rat

print(f"Best Idx params: ambiguity_ratio={best_idx_params:.2f} -> Mismatches: {best_idx_mismatches}")
