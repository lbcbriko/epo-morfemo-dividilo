#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dividas tekstojn en Esperanto laŭ morfemoj.

Uzado::

    python radiko.py -i input.txt -o output.txt
    python radiko.py -i input.txt -o output.txt --solvoj 3

Eligo (output format)::

    vorto[[solvo1|solvo2|...]]

- 语素之间用 ``+`` 分隔
- 候选解之间用 ``|`` 分隔，**最优解在最前**
- **只有一个解时同样写成列表**（列表长度为 1）——单解与多解格式完全一致
- 无法切分时写 ``kontroloto``，同样占一个列表项

示例::

    domo[[dom+o]]
    horloĝo[[horloĝ+o]]
    ekskurso[[ekskurs+o|eks+kurs+o]]
    heroino[[heroin+o|hero+in+o]]
    kŝŝŝ[[kontroloto]]

切分原则（见 PLANO.md D14）：

1. **切得越少越好**——尊重词汇化。``radiko.txt`` 就是 PIV 词条集，
   所以"少切"等价于"把已词汇化的复合词当作原子单位"。
2. **同分时长匹配优先**——避免 ``kom+pu+ti+lo`` 这类碎切。
3. 真同形异义（如 ``heroino`` = 海洛因 / 女英雄）无法由字符串判定，
   因此保留多个候选解，按上述原则排序后一并输出。
"""

import argparse
import string
import sys
from typing import Dict, List, Optional, Sequence, Tuple

# 世界语字母（含变音符号）
ESPERANTO_CHARACTERS = string.ascii_letters + 'ĈĜĤĴŜŬĉĝĥĵŝŭ'

# 词性/语法词尾：允许作为独立语素出现的单字母与短尾
GRAMATIKAJ_FINAJHOJ = ('a', 'e', 'i', 'o', 'u', 'oj', 'aj')

# 可作为"词末语法尾"的形态集合，用于排序。
# 末段落在其中者优先，避免把语法尾误吸进后缀：
#   domon 应为 dom+o+n，而非 dom+on（-on- 是后缀）
FINAJHOJ_POR_ORDO = frozenset({
    'a', 'e', 'i', 'o', 'u',
    'oj', 'aj', 'j', 'n',
    'as', 'is', 'os', 'us',
})

# 只能出现在**词末**的附加词尾。
# 若允许它们出现在词中，会产生大量噪声切分（如 ananaso -> a+n+anas+o），
# 而 -j / -n / -as / -is / -os / -us 在世界语中本就严格居于词末。
NUR_FINAJ = frozenset({'j', 'n', 'as', 'is', 'os', 'us'})

# 无法切分时的标记
KONTROLOTO = 'kontroloto'

# 单次切分的安全上限，防止病态输入导致组合爆炸
_MAKSIMUMA_ESPLORO = 4000
_MAKSIMUMA_PROFUNDECO = 64


# ---------------------------------------------------------------------------
# 词表
# ---------------------------------------------------------------------------

class Vortaro:
    """词表容器。

    区分不同角色，以便将来接入约束表；目前仅用 ``morfemoj`` 做切分。
    """

    def __init__(self) -> None:
        self.radikoj: set = set()        # 词根
        self.prefiksoj: set = set()      # 前缀
        self.sufiksoj: set = set()       # 后缀
        self.ceteraj: set = set()        # 表词、小词等
        self.fundamentaj: set = set()    # PIV 基本词根（★）

    # -- 加载 ------------------------------------------------------------
    @staticmethod
    def _legi_liston(dosiero: str) -> List[str]:
        """读取词表文件。

        支持两种格式：

        - ``{a,b,c}`` 单行花括号逗号分隔（prefikso/sufikso）
        - 逐行一个条目
        """
        with open(dosiero, 'r', encoding='utf-8') as f:
            teksto = f.read().strip()
        if not teksto:
            return []
        if teksto.startswith('{'):
            return [x.strip() for x in teksto.strip('{}').split(',') if x.strip()]
        return [x.strip() for x in teksto.split('\n') if x.strip()]

    def sxargi(self, dosierujo: str) -> 'Vortaro':
        import os

        def p(nomo: str) -> str:
            return os.path.join(dosierujo, nomo)

        self.prefiksoj = set(self._legi_liston(p('prefikso.txt')))
        self.sufiksoj = set(self._legi_liston(p('sufikso.txt')))
        self.radikoj = set(self._legi_liston(p('radiko.txt')))
        self.ceteraj = set(self._legi_liston(p('tabelvorto.txt')))
        self.ceteraj |= set(self._legi_liston(p('vorteto.txt')))

        # 可选：PIV 基本词根（供将来打分使用）
        fundamenta = p('fundamenta-radiko.txt')
        if os.path.exists(fundamenta):
            self.fundamentaj = set(self._legi_liston(fundamenta))

        return self

    def morfemoj(self) -> set:
        """用于切分的全部可识别语素（小写）。

        ``NUR_FINAJ`` 也必须入表，否则 ``domon`` 无法切成 ``dom+o+n``；
        它们的位置限制由 :meth:`Dividilo._enumeri` 保证。
        """
        ĉio = self.radikoj | self.prefiksoj | self.sufiksoj | self.ceteraj
        ĉio |= set(GRAMATIKAJ_FINAJHOJ)
        ĉio |= set(NUR_FINAJ)
        return {x.lower() for x in ĉio if x}

    def funkciaj(self) -> set:
        """"虚词集合（小词表 + 表词表），用于排序时对中部虚词降权。"""
        return {x.lower() for x in self.ceteraj if x}

# ---------------------------------------------------------------------------
# 切分
# ---------------------------------------------------------------------------

class Dividilo:
    """把单词切成候选语素序列，并按优劣排序。"""

    def __init__(
        self,
        vortaro: set,
        maksimumaj_solvoj: int = 8,
        funkciaj: Optional[set] = None,
    ) -> None:
        self._vortaro = vortaro
        self._maksimumo = maksimumaj_solvoj
        # 以"整个词"为键缓存最终结果（已排序），避免重复计算
        self._kaŝmemoro: Dict[str, Tuple[Tuple[str, ...], ...]] = {}
        self._kasxita_kvanto = 0  # 已缓存的词条数
        # 虚词（代词、介词、连词等），只在中部位置降权
        self._funkciaj = frozenset(funkciaj) if funkciaj else frozenset()

    # -- 打分 ------------------------------------------------------------
    def _sxlosilo(self, partoj: Sequence[str]) -> tuple:
        """排序键（越小越优）。

        1. **整词命中优先** —— 若整个词本身就是词条（如 ``kun``），不应被拆开
        2. **末段是纯语法词尾者优先** —— 否则 ``domon`` 会误判为 ``dom+on``
           （``-on-`` 是后缀），而正解是 ``dom+o+n``
        3. **中部不出现小品词** —— ``Mal+ju+nul+o`` 里的 ``ju`` 是虚词，
           用它做中段属于噪声，应让位给 ``Mal+jun+ul+o``。
           词首位置不受罚（``al+port+u``、``mi+a`` 都是合法的）
        4. 语素数量少者优先 —— 尊重词汇化（``horloĝ+o`` 优于 ``hor+loĝ+o``）
        5. 各段长度平方和大者优先 —— 长匹配优先，避免碎切
        6. 原始拼写作为稳定 tie-break
        """
        fina = partoj[-1].lower() if partoj else ''
        meze_funkciaj = 0
        for p in partoj[1:-1]:
            if p.lower() in self._funkciaj:
                meze_funkciaj += 1
        return (
            0 if len(partoj) == 1 else 1,
            0 if fina in FINAJHOJ_POR_ORDO else 1,
            meze_funkciaj,
            len(partoj),
            -sum(len(p) ** 2 for p in partoj),
            tuple(partoj),
        )

    # -- 枚举 ------------------------------------------------------------
    def _enumeri(self, vorto: str) -> List[Tuple[str, ...]]:
        rezultoj: List[Tuple[str, ...]] = []
        v = self._vortaro
        limo = _MAKSIMUMA_ESPLORO

        def sercxu(resto: str, akumulo: List[str], profundo: int) -> None:
            if len(rezultoj) >= limo:
                return
            if not resto:
                if akumulo:
                    rezultoj.append(tuple(akumulo))
                return
            if profundo <= 0:
                return
            # 倒序遍历 = 先试最长的前缀（词汇化优先）
            for i in range(len(resto), 0, -1):
                peco = resto[:i]
                malgrando = peco.lower()
                # -j / -n / -as / -is / -os / -us 只能是词末附加词尾
                if malgrando in NUR_FINAJ and i != len(resto):
                    continue
                # 语法元音（a/e/i/o/u、oj、aj）只能位于词末，
                # 其后最多再跟 -j / -n。
                # 否则会切出 avino -> a+vin+o 这类非法切分。
                if malgrando in GRAMATIKAJ_FINAJHOJ:
                    resto_resto = resto[i:]
                    if resto_resto not in ('', 'j', 'n'):
                        continue
                if malgrando in v:
                    akumulo.append(peco)
                    sercxu(resto[i:], akumulo, profundo - 1)
                    akumulo.pop()
                    if len(rezultoj) >= limo:
                        return

        sercxu(vorto, [], _MAKSIMUMA_PROFUNDECO)
        return rezultoj

    # -- 公共接口 --------------------------------------------------------
    def disigi(self, vorto: str) -> Tuple[Tuple[str, ...], ...]:
        """返回该词的候选切分，最优在前；无法切分时返回空元组。"""
        if vorto in self._kaŝmemoro:
            return self._kaŝmemoro[vorto]

        kandidatoj = self._enumeri(vorto)
        # 去重后排序，保留前 N 个
        unikaj = list(dict.fromkeys(kandidatoj))
        unikaj.sort(key=self._sxlosilo)
        rezulto = tuple(unikaj[: self._maksimumo])

        # 缓存有上限，避免长语料把内存吃光
        if self._kasxita_kvanto > 200000:
            self._kaŝmemoro.clear()
            self._kasxita_kvanto = 0
        self._kaŝmemoro[vorto] = rezulto
        self._kasxita_kvanto += 1
        return rezulto


# ---------------------------------------------------------------------------
# 分词
# ---------------------------------------------------------------------------

def esperanto_tokenize(text: str) -> List[str]:
    """按"字母/非字母"边界把文本切成词与非词片段。"""
    rezulto: List[str] = []
    last_part = ''
    for pos in range(len(text) + 1):
        if (
            pos == len(text) or (
                len(last_part) > 0 and
                (
                    (last_part[-1] in ESPERANTO_CHARACTERS and text[pos] not in ESPERANTO_CHARACTERS) or
                    (last_part[-1] not in ESPERANTO_CHARACTERS and text[pos] in ESPERANTO_CHARACTERS)
                )
            )
        ):
            rezulto.append(last_part)
            last_part = ''
        if pos != len(text):
            last_part += text[pos]
    return rezulto


def formatigi(kandidatoj: Sequence[Sequence[str]]) -> str:
    """把候选切分格式化为统一的标注内容。

    单解与多解使用同一格式：永远是"用 ``|`` 分隔的列表"，
    每个解内部用 ``+`` 分隔语素。
    """
    if not kandidatoj:
        return KONTROLOTO
    return '|'.join('+'.join(partoj) for partoj in kandidatoj)


def prilabori_tekston(teksto: str, dividilo: Dividilo) -> str:
    """对整段文本加注，返回带 ``[[...]]`` 标注的字符串。"""
    eroj = esperanto_tokenize(teksto)
    eligo: List[str] = []
    for ero in eroj:
        if not ero:
            continue
        # 非字母开头的片段（标点、空格、数字）原样输出
        if ero[0] not in ESPERANTO_CHARACTERS:
            eligo.append(ero)
            continue
        kandidatoj = dividilo.disigi(ero)
        eligo.append(ero + '[[' + formatigi(kandidatoj) + ']]')
    return ''.join(eligo)


def prilabori_dosieron(enigo: str, eligo: str, dividilo: Dividilo) -> None:
    with open(enigo, 'r', encoding='utf-8') as f:
        teksto = f.read()
    rezulto = prilabori_tekston(teksto, dividilo)
    with open(eligo, 'w', encoding='utf-8') as f:
        f.write(rezulto)


# ---------------------------------------------------------------------------
# 命令行
# ---------------------------------------------------------------------------

def _argumentoj(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Dividas tekstojn en Esperanto laŭ morfemoj.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Elformato / 输出格式:\n'
            '  vorto[[solvo1|solvo2|...]]\n'
            '  语素用 "+" 分隔，候选解用 "|" 分隔且最优在前；\n'
            '  单解即列表长度为 1，与多解格式一致；无法切分为 kontroloto。\n'
        ),
    )
    p.add_argument('-i', '--enigo', default='input.txt', help='输入文件（默认 input.txt）')
    p.add_argument('-o', '--eligo', default='output.txt', help='输出文件（默认 output.txt）')
    p.add_argument('-v', '--vortaro', default='./vortaro', help='词表目录（默认 ./vortaro）')
    p.add_argument(
        '-n', '--solvoj', type=int, default=8,
        help='每个词最多输出多少个候选解（默认 8；1 = 仅最优解）',
    )
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ag = _argumentoj(sys.argv[1:] if argv is None else argv)
    if ag.solvoj < 1:
        print('eraro: --solvoj devas esti >= 1', file=sys.stderr)
        return 2

    vortaro = Vortaro().sxargi(ag.vortaro)
    dividilo = Dividilo(vortaro.morfemoj(), maksimumaj_solvoj=ag.solvoj, funkciaj=vortaro.funkciaj())
    prilabori_dosieron(ag.enigo, ag.eligo, dividilo)
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Maljunulo| — |Ho|, |kompreneble|. |Bonvolu| |sidiĝi|. ( |Al| |la| |knabino|. ) Alportu akvon, infano, purigu la glason antaŭe.
