#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Konstrolaj testoj por radiko.py.

Ruligu / 运行::

    python tests/test_radiko.py

不使用 pytest，直接用断言，便于在任何 Python 3 环境下运行。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import radiko  # noqa: E402

VORTARO_DOSIERUJO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'vortaro'
)

# 全局初始化一次
_VORTARO = radiko.Vortaro().sxargi(VORTARO_DOSIERUJO)
_MORFEMOJ = _VORTARO.morfemoj()
_FUNKCIAJ = _VORTARO.funkciaj()
_DIVIDILO = radiko.Dividilo(_MORFEMOJ, maksimumaj_solvoj=8, funkciaj=_FUNKCIAJ)

# 允许的失败项（记录而非中断）
_malsukcesoj = []


def kontroli(nomo, kondicxo, detaloj=''):
    if kondicxo:
        print(f'  [PASS] {nomo}')
    else:
        print(f'  [FAIL] {nomo}  {detaloj}')
        _malsukcesoj.append(nomo)


def solvoj(vorto):
    return _DIVIDILO.disigi(vorto)


def unua(vorto):
    s = solvoj(vorto)
    return '+'.join(s[0]) if s else radiko.KONTROLOTO


def cxu_havas(vorto, partoj):
    """该词是否含有指定切分（按语素列表比较）。"""
    celo = tuple(partoj.split('+'))
    return celo in solvoj(vorto)


def main():
    print('=== 1. 词汇化复合词：应整词切分（长匹配优先）===')
    kontroli('horloĝo -> horloĝ+o', unua('horloĝo') == 'horloĝ+o', unua('horloĝo'))
    kontroli('ekskurso -> ekskurs+o', unua('ekskurso') == 'ekskurs+o', unua('ekskurso'))
    kontroli('ananaso -> ananas+o', unua('ananaso') == 'ananas+o', unua('ananaso'))
    kontroli('universitato -> universitat+o', unua('universitato') == 'universitat+o', unua('universitato'))
    kontroli('scienco -> scienc+o', unua('scienco') == 'scienc+o', unua('scienco'))

    print('\n=== 2. 规则派生词：应切出词根+词缀 ===')
    kontroli('lernanto -> lern+ant+o', unua('lernanto') == 'lern+ant+o', unua('lernanto'))
    kontroli('komputilo -> komput+il+o', unua('komputilo') == 'komput+il+o', unua('komputilo'))
    kontroli('domo -> dom+o', unua('domo') == 'dom+o', unua('domo'))
    kontroli('lernejo -> lern+ej+o', unua('lernejo') == 'lern+ej+o', unua('lernejo'))
    kontroli('malsanuleja -> mal+san+ul+ej+a',
             unua('malsanuleja') == 'mal+san+ul+ej+a', unua('malsanuleja'))

    print('\n=== 3. 语法词尾 -j / -n ===')
    kontroli('domoj -> dom+oj', unua('domoj') == 'dom+oj', unua('domoj'))
    kontroli('domon -> dom+o+n', unua('domon') == 'dom+o+n', unua('domon'))
    kontroli('domojn -> dom+oj+n', unua('domojn') == 'dom+oj+n', unua('domojn'))
    # -n 不得出现在词中（噪声防护）
    kontroli('ananaso 不含 a+n+anas+o',
             not cxu_havas('ananaso', 'a+n+anas+o'))

    print('\n=== 4. 真同形异义：必须保留多个解 ===')
    hero = solvoj('heroino')
    kontroli('heroino 首解为 heroin+o', hero and '+'.join(hero[0]) == 'heroin+o',
             hero[:1])
    kontroli('heroino 同时保留 hero+in+o', cxu_havas('heroino', 'hero+in+o'),
             list(map(lambda t: '+'.join(t), hero)))
    kontroli('heroino 至少 2 个解', len(hero) >= 2, len(hero))

    print('\n=== 5. 统一输出格式 ===')
    for vorto, atendata in [
        ('domo', 'domo[[dom+o]]'),
        ('kŝŝŝ', 'kŝŝŝ[[kontroloto]]'),
    ]:
        rezulto = radiko.prilabori_tekston(vorto, _DIVIDILO)
        kontroli(f'{vorto} -> {atendata}', rezulto == atendata, rezulto)

    # 多解格式：仍是同一对 [[ ]] 内，用 | 分隔解，用 + 分隔语素
    rezulto = radiko.prilabori_tekston('heroino', _DIVIDILO)
    kontroli('多解只在单对 [[ ]] 内',
             rezulto.count('[[') == 1 and rezulto.count(']]') == 1, rezulto)
    kontroli('多解用 | 分隔', '|' in rezulto, rezulto)
    kontroli('语素用 + 分隔', '+' in rezulto, rezulto)

    print('\n=== 6. 单解/多解同构：solvoj=1 与 solvoj=8 格式一致 ===')
    sola = radiko.Dividilo(_MORFEMOJ, maksimumaj_solvoj=1, funkciaj=_FUNKCIAJ)
    r1 = radiko.prilabori_tekston('heroino', sola)
    kontroli('solvoj=1 仍为 [[...]] 结构',
             r1 == 'heroino[[heroin+o]]', r1)

    print('\n=== 7. 分词与管道连续性 ===')
    frazo = 'Al la knabino. Ho, kompreneble!'
    eligo = radiko.prilabori_tekston(frazo, _DIVIDILO)
    kontroli('首词后紧跟标注', eligo.startswith('Al[['), eligo[:40])
    kontroli('逗号+空格原样保留', ', ' in eligo, eligo)
    kontroli('结尾感叹号原样保留', eligo.endswith('!'), eligo[-20:])
    kontroli('5 个字母词各有一个标注',
             len(re.findall(r'\[\[', eligo)) == 5, len(re.findall(r'\[\[', eligo)))
    kontroli('标点未被标注', '.[[' not in eligo and ',[[' not in eligo and '![[' not in eligo, eligo)
    kontroli('空格未被标注', ' [[' not in eligo, eligo)

    print('\n=== 8. 健壮性 ===')
    kontroli('空串不崩溃', radiko.prilabori_tekston('', _DIVIDILO) == '')
    kontroli('纯标点不崩溃', radiko.prilabori_tekston('…— ,.!?', _DIVIDILO) == '…— ,.!?')
    kontroli('单字母有结果', len(solvoj('o')) >= 1, solvoj('o'))
    kontroli('超长词不崩溃', isinstance(radiko.prilabori_tekston('a' * 60, _DIVIDILO), str))

    print('\n' + '=' * 50)
    if _malsukcesoj:
        print(f'失败 {len(_malsukcesoj)} 项:')
        for n in _malsukcesoj:
            print(f'  - {n}')
        return 1
    print('全部通过 (ALL PASS)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
