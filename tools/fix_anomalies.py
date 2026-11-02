#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性数据修正：清除 PIV 提取中 4 条异常条目。

这 4 条的 data-alfa 与其 kapvorto 词根不一致：
  akvo -> akv/o (真词根 akv)
  barmicv / kalaazar / metakrilataacid -> 原形带连字符的专名组合
"""

import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD = {'akvo', 'barmicv', 'kalaazar', 'metakrilataacid'}


def sxargi(p):
    with io.open(p, encoding='utf-8') as f:
        return [x.rstrip('\n') for x in f]


def skribi(p, lines):
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')


def filtrigi(p):
    if not os.path.exists(p):
        return None
    malnova = sxargi(p)
    nova = [x for x in malnova if x.strip() and x.strip() not in BAD]
    if len(nova) != len(malnova):
        skribi(p, nova)
    return len(malnova), len(nova)


celoj = [os.path.join(REPO, 'vortaro', 'radiko.txt')]
for n in ('a', 'e', 'i', 'o', 'u'):
    celoj.append(os.path.join(REPO, 'vortaro', 'vokalo-fina-radiko', n + '_fina_radiko.txt'))
for n in ('as', 'is', 'os', 'u', 'us'):
    celoj.append(os.path.join(REPO, 'vortaro', 'kvazaux-finitiva-radiko', n + '-fina-radiko.txt'))
for n in ('as', 'is', 'os', 'u'):
    celoj.append(os.path.join(REPO, 'vortaro', 'kvazaux-post-finitiva-radiko', n + '-komenca-radiko.txt'))

for p in celoj:
    r = filtrigi(p)
    if r is None:
        continue
    antaux, post = r
    marko = '  <-- sxangxigxis' if antaux != post else ''
    print('%-58s %5d -> %5d%s' % (os.path.relpath(p, REPO), antaux, post, marko))
