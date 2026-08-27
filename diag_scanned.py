"""
Diagnostic: for the worst files (05, 06, 09), show exact px25_rel values per question
to understand the error patterns.
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

# Check specific files
for fname in ['Samples_Page_05.png', 'Samples_Page_06.png', 'Samples_Page_09.png']:
    exp = expected[fname]['responses']
    print(f"\n{'='*80}")
    print(f"FILE: {fname}")
    print(f"{'='*80}")
    
    for q in range(1, 61):
        metrics = all_data[fname]['q'][q]
        px25 = [m['px25'] for m in metrics]
        sum_v = [m['sum'] for m in metrics]
        
        min_v = min(px25)
        adj = [v - min_v for v in px25]
        max_idx = int(np.argmax(adj))
        max_val = adj[max_idx]
        sv = sorted(adj, reverse=True)
        
        ans = '-'
        if max_val > 2:
            if sv[1] <= max_val * 0.92:
                ans = options[max_idx]
        
        if ans != exp[q-1]:
            ratio_str = f"{sv[1]/max_val:.2f}" if max_val > 0 else "n/a"
            print(f"  Q{q:>2} WRONG: exp={exp[q-1]} got={ans}  px25={px25}  adj={adj}  ratio={ratio_str}")
