import optimize
import numpy as np

min_darkness = 2000
ambiguity_ratio = 0.65
mismatches = 0
for fid, data in optimize.blocks.items():
    exp = optimize.expected[fid]['responses']
    for q_id in range(1, 61):
        if q_id not in data['q']: continue
        vals = data['q'][q_id]
        min_val = min(vals)
        adj_vals = [v - min_val for v in vals]
        max_idx = np.argmax(adj_vals)
        max_val = adj_vals[max_idx]
        sorted_vals = sorted(adj_vals, reverse=True)
        ans = '-'
        if max_val > min_darkness:
            ans = optimize.options[max_idx]
        if ans != exp[q_id-1]:
            print(f"F{fid} Q{q_id}: Exp {exp[q_id-1]} != Pred {ans} (Max: {max_val:.0f}, Max2: {sorted_vals[1]:.0f}, Vals: {[int(x) for x in vals]})")
            mismatches += 1
print("Total:", mismatches)
