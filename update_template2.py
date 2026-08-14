import json

with open('templates/template_uom_60q.json', 'r') as f:
    template = json.load(f)

# Update index_nums
template['fieldBlocks']['index_nums']['origin'] = [140, 843]
template['fieldBlocks']['index_nums']['bubblesGap'] = 60
template['fieldBlocks']['index_nums']['labelsGap'] = 47.222
template['fieldBlocks']['index_nums']['bubbleDimensions'] = [44, 18]

# Update index_char1
template['fieldBlocks']['index_char1']['origin'] = [500, 843]
template['fieldBlocks']['index_char1']['labelsGap'] = 47.222
template['fieldBlocks']['index_char1']['bubbleDimensions'] = [44, 18]

# Update index_char2
template['fieldBlocks']['index_char2']['origin'] = [560, 843]
template['fieldBlocks']['index_char2']['labelsGap'] = 47.222
template['fieldBlocks']['index_char2']['bubbleDimensions'] = [44, 18]

# Update questions
template['fieldBlocks']['q1_20']['origin'] = [217, 1647]
template['fieldBlocks']['q1_20']['bubblesGap'] = 120
template['fieldBlocks']['q1_20']['labelsGap'] = 83.736
template['fieldBlocks']['q1_20']['bubbleDimensions'] = [44, 18]

template['fieldBlocks']['q21_40']['origin'] = [956, 1647]
template['fieldBlocks']['q21_40']['bubblesGap'] = 120
template['fieldBlocks']['q21_40']['labelsGap'] = 83.736
template['fieldBlocks']['q21_40']['bubbleDimensions'] = [44, 18]

template['fieldBlocks']['q41_60']['origin'] = [1696, 1647]
template['fieldBlocks']['q41_60']['bubblesGap'] = 120
template['fieldBlocks']['q41_60']['labelsGap'] = 83.736
template['fieldBlocks']['q41_60']['bubbleDimensions'] = [44, 18]

with open('templates/template_uom_60q.json', 'w') as f:
    json.dump(template, f, indent=4)
