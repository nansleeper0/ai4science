#!/usr/bin/env python3
"""Generate ontology/<Класс>.md notes from ontology.yaml."""
import yaml, os

with open('ontology.yaml') as f:
    ont = yaml.safe_load(f)
classes = ont['classes']
props = ont['properties']
attrs = ont['attributes']
os.makedirs('ontology', exist_ok=True)
for name, c in classes.items():
    rels = [p for p, spec in props.items() if name in spec['domain']]
    ats = [a for a, spec in attrs.items() if name in spec['domain']]
    parent = c.get('parent')
    lines = ['---', 'kind: класс', '---', f'# {name}', '', c['definition'], '',
             f'Отношения от этого класса: {", ".join(rels) if rels else "—"}.', '']
    if ats:
        vals = [f'{a} ({", ".join(attrs[a]["values"])})' for a in ats]
        lines.append(f'Атрибуты: {"; ".join(vals)}.')
    else:
        lines.append('Атрибуты: —.')
    lines += ['', '## Связи']
    if parent:
        lines.append(f'- подклассОт: [[{parent}]]')
    with open(f'ontology/{name}.md', 'w') as f:
        f.write('\n'.join(lines) + '\n')
print('created', len(classes), 'class notes')