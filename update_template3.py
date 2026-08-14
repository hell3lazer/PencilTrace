import json

with open('templates/template_uom_60q.json', 'r') as f:
    template = json.load(f)

# Update index blocks to capture the number as well (student marked through numbers)
template['fieldBlocks']['index_nums']['origin'] = [140, 828]
template['fieldBlocks']['index_nums']['bubbleDimensions'] = [44, 30]

template['fieldBlocks']['index_char1']['origin'] = [500, 828]
template['fieldBlocks']['index_char1']['bubbleDimensions'] = [44, 30]

template['fieldBlocks']['index_char2']['origin'] = [560, 828]
template['fieldBlocks']['index_char2']['bubbleDimensions'] = [44, 30]

with open('templates/template_uom_60q.json', 'w') as f:
    json.dump(template, f, indent=4)
