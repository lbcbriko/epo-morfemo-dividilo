#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 PIV 提取感叹词清单，并从各词表中移除。

感叹词（PIV 中 kapvorto 以 "!" 结尾）不是语素，若留在词表里会切出
pu+rig+u 这类胡说。
"""

import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIV = r'C:\Users\pub\.minimax\v2\assets\2026\11\01\22-26-30-452-asset_20261101-222630-452_a221b8236183_ac0a0683-piv.html'

with io.open(PIV, encoding='utf-8') as f:
    html = f.read()

# data-alfa="X" ... <strong class="kapvorto">...</strong>
pat = re.compile(
    r'data-alfa="([^"]*)"[^>]*>\s*(?:<span[^>]*>★</span>)?\s*'
    r'<strong class="kapvorto"[^>]*>([\s\S]*?)</strong>'
)

interj = set()
for m in pat.finditer(html):
    alfa = m.group(1)
    kv = re.sub(r'<sup[\s\S]*?</sup>', '', m.group(2))
    kv = re.sub(r'<[^>]+>', '', kv).strip()
    if kv.endswith('!'):
        interj.add(alfa.strip().lower())

print('PIV 感叹词: %d 个' % len(interj))
print('  ' + ', '.join(sorted(interj)))
print()

celoj = [os.path.join(REPO, 'vortaro', 'radiko.txt')]
for n in ('a', 'e', 'i', 'o', 'u'):
    celoj.append(os.path.join(REPO, 'vortaro', 'vokalo-fina-radiko', n + '_fina_radiko.txt'))
for n in ('as', 'is', 'os', 'u', 'us'):
    celoj.append(os.path.join(REPO, 'vortaro', 'kvazaux-finitiva-radiko', n + '-fina-radiko.txt'))
for n in ('as', 'is', 'os', 'u'):
    celoj.append(os.path.join(REPO, 'vortaro', 'kvazaux-post-finitiva-radiko', n + '-komenca-radiko.txt'))

totala = 0
for p in celoj:
    if not os.path.exists(p):
        continue
    with io.open(p, encoding='utf-8') as f:
        lines = [x.rstrip('\n') for x in f]
    nova = [x for x in lines if x.strip() and x.strip().lower() not in interj]
    if len(nova) != len(lines):
        with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(nova) + '\n')
        forigita = len(lines) - len(nova)
        totala += forigita
        print('%-56s -%d' % (os.path.relpath(p, REPO), forigita))

print('\n合计移除 %d 行' % totala)
