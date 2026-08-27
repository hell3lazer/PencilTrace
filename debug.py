import optimize
fid = '9'
data = optimize.blocks[fid]
exp = optimize.expected[fid]['responses']
print(f"File {fid} Q1-Q10:")
for q_id in range(1, 11):
    vals = data['q'][q_id]
    max_idx = optimize.np.argmax(vals)
    max_val = vals[max_idx]
    sorted_vals = sorted(vals, reverse=True)
    ans = '-'
    if max_val > 10000:
        if sorted_vals[1] > max_val * 0.75:
            ans = '-'
        else:
            ans = optimize.options[max_idx]
    
    print(f"Q{q_id}: Exp={exp[q_id-1]}, Pred={ans}, Vals={vals}, Max={max_val}")
