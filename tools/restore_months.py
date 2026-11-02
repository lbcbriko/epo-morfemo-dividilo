#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补回被"首字母大写"规则误排除的月份与星期。

PIV 把月份写作 Januar/o、Novembr/o，也把星期一写作 Lun/o，
但世界语实际使用中小写（januaro、novembro、lundo）。
它们不是专名，必须作为普通词根参与切分。
"""

import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESTARIGI = [
    'januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul',
    'aŭgust', 'septembr', 'oktobr', 'novembr', 'decembr',
    'lun', 'mard', 'merkred', 'ĵaŭd', 'vend', 'sabat', 'dimanĉ',
]


def sxargi(p):
    with io.open(p, encoding='utf-8') as f:
        return [x.rstrip('\n') for x in f if x.strip()]


def skribi(p, lines):
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')


p = os.path.join(REPO, 'vortaro', 'radiko.txt')
lines = sxargi(p)
antaux = set(lines)
aldonitaj = [w for w in RESTARIGI if w not in antaux]

if aldonitaj:
    lines = sorted(antaux | set(aldonitaj))
    skribi(p, lines)
    print('已补回 %d 个: %s' % (len(aldonitaj), ', '.join(aldonitaj)))
else:
    print('无需补回')

# 同步重建 vokalo-fina-radiko：只需把以元音结尾的新词加进对应表
for w in aldonitaj:
    if w[-1] in 'aeiou':
        fp = os.path.join(REPO, 'vortaro', 'vokalo-fina-radiko', w[-1] + '_fina_radiko.txt')
        lst = sxargi(fp)
        if w not in lst:
            skribi(fp, sorted(set(lst) | {w}))
            print('  加入 %s_fina_radiko.txt: %s' % (w[-1], w))

print('radiko.txt 现有 %d 条' % len(sxargi(p)))
