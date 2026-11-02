# radiko.py 改进方案

> 版本：v1（草案）
> 日期：2026-11-01
> 基线：`main` @ `350e1eb`（已移除早期程序）/ `dev` 分支
> 适用代码：`radiko.py`（89 行）、`vortaro/`（19 个词表）

---

## 0. 摘要：两条核心结论

**结论一：算法已经不是瓶颈。**

`radiko.py` 相对早期版 `epo-morfemo-dividilo.py`（已归档至 `arkivo` 分支）已经是数量级上的改进——单遍扫描 + 词典驱动 + 全局记忆化，把复杂度从 O(N²) 降到 O(N + ΣL²)。继续在算法结构上打磨的边际收益已经很有限。

**结论二：词典才是瓶颈。**

现行根词表 `radiko.txt` 对日常高频词根的覆盖率仅约 **21%**（抽样 29 个高频词根只命中 6 个），导致 `domo`、`komputilo`、`lernanto`、`venkas` 这些最基础的词全部返回 `kontroloto`。这才是 README 顶部 `(ATENTU: NE UZEBLA NUN!)` 的真实原因——**不是程序不行，是词表不够**。

因此改进优先级应当是：

> **词典完整性 ≫ 切分正确性 > 工程化（CLI/测试/CI） > 算法微调**

而不是相反。Phase 2 里那些看起来更"高级"的算法改造，在词表补全之前做，收益接近于零。

| 优先级 | 议题 | 阶段 | 状态 |
|---|---|---|---|
| **P0** | 根词表补全（日常核心词汇） | Phase 1 | ✅ **已完成**（见 §1.5，PIV 导入，5523 → 13842） |
| **P0** | `sufikso.txt` 补回 `ant/at/ont` | Phase 1 | ✅ **已由 PIV 导入自动解决**（这些词根本身就在 PIV 词根集里） |
| **P0** | 13 个约束表接入（当前 100% 未使用） | Phase 1 | ⚠️ 词表已重建扩充，**但 `radiko.py` 尚未读取它们**（属代码改动） |
| **P1** | 切分策略：全解枚举 → 择优 + 约束校验 | Phase 2 | ✅ **已完成**（见 §1.7，34 项测试全绿） |
| **P1** | 缓存有界化、递归剪枝 | Phase 2 | ✅ **已完成**（20 万条上限 + 深度/枚举双重安全阀） |
| **P2** | CLI 参数化、连字符按字母处理、大小写策略 | Phase 1 | ⬜ 未开始 |
| **P2** | 测试、CI、打包为库 | Phase 3 | ⬜ 未开始 |

---

## 1. 现状基线

### 1.1 `radiko.py` 代码结构

> 2026-11-03 已重写，实施 D14 的消歧策略。以下为当前结构。

| 位置 | 组件 | 职责 |
|---|---|---|
| — | `Vortaro` | 词表容器，区分 `radikoj / prefiksoj / sufiksoj / ceteraj / fundamentaj` |
| — | `Vortaro.sxargi(dir)` | 加载词表（支持 `{...}` 与逐行两种格式） |
| — | `Dividilo.disigi(w)` | 返回该词的**候选切分元组**，最优在前，带记忆化 |
| — | `Dividilo._enumeri(w)` | 有界 DFS 枚举，**倒序遍历前缀 = 长匹配优先** |
| — | `Dividilo._sxlosilo(partoj)` | 排序键：语素数少 → 长度平方和大 → 拼写稳定 |
| — | `esperanto_tokenize(text)` | 单遍字符扫描，按字母/非字母切词 |
| — | `formatigi(kandidatoj)` | **统一格式化**：解用 `|`、语素用 `+` |
| — | `prilabori_tekston / prilabori_dosieron` | 加注并写出 |
| — | `main()` | CLI：`-i -o -v -n` |

**统一输出格式（单解与多解同构）：**

```
vorto[[solvo1|solvo2|...]]
```

- 语素之间 `+`，候选解之间 `|`，**最优解在最前**
- **只有一个解时列表长度为 1**，格式与多解完全一致
- 无法切分时为 `vorto[[kontroloto]]`，同样是一个列表项

| 情形 | 输出 |
|---|---|
| 单解 | `domo[[dom+o]]` |
| 词汇化 | `horloĝo[[horloĝ+o]]` |
| 多解 | `heroino[[heroin+o|hero+in+o]]` |
| 多解（词缀） | `ekskurso[[ekskurs+o|eks+kurs+o]]` |
| 失败 | `kŝŝŝ[[kontroloto]]` |

**旧格式对照**：原先为 `词[[解1|解2,解3]]`（语素 `|`、解 `,`），且单解时只有一层结构。新格式把两者统一为"始终是 `|` 分隔的解列表"，消除了"解的分隔符与语素分隔符混淆"的问题。

核心切分循环（原为短匹配优先，现倒序）：

```python
# 旧：range(1, len(resto) + 1)  -> 切得最碎
# 新：range(len(resto), 0, -1)  -> 长匹配优先，尊重词汇化
for i in range(len(resto), 0, -1):
    peco = resto[:i]
    if malgrando in NUR_FINAJ and i != len(resto):
        continue                      # -j / -n 只允许在词末
    if malgrando in vortaro:
        ...
```

### 1.2 算法与复杂度

| | 早期版（`arkivo` 分支） | 现行 `radiko.py` |
|---|---|---|
| 文档扫描 | 9 次全档正则 + 18 次文件读写 | **1 次 O(N) 字符扫描** |
| 与文档长度的关系 | O(N²)（前缀函数重建剩余串） | O(N) |
| 与语料规模的关系 | 线性 | **摊还到不同词数量** |
| 规则顺序依赖 | 强（第 N 步必须晚于第 M 步） | 无（纯查表） |
| 输出 | 单一路径 | 全部候选解 |

单词切分复杂度为 O(L²)（L 为词长），全语料为 O(N + Σ<sub>不同词</sub> L²)，由 `result_cache` 摊还。**这一层已经足够好，不需要大改。**

### 1.3 词典资源盘点（19 个 `.txt` 文件，实测）

> 下表为 **PIV 导入前**的基线。导入后的状态见 §1.5。

| 文件 | 条目 | 格式 | 角色 | 当前被 `radiko.py` 加载？ |
|---|---|---|---|---|
| `radiko.txt` | 5523 | 逐行 | 根词 | ✅ |
| `prefikso.txt` | 39 | `{...}` | 前缀 | ✅ |
| `sufikso.txt` | 30 | `{...}` | 后缀 | ✅ |
| `tabelvorto.txt` | 45 | 逐行 | 表词（README 第 14 步） | ✅ |
| `vorteto.txt` | 162 行 / **156 去重** | 逐行 | 小词（README 第 13 步，需还原） | ✅（但语义有冲突，见 D6） |
| `vokalo-fina-radiko/{a,e,i,o,u}_fina_radiko.txt` | 886 | 逐行 | **元音结尾根词标注** | ❌ |
| `kvazaux-finitiva-radiko/{as,is,os,u,us}-fina-radiko.txt` | 189 | 逐行 | **准根词·后缀形例外** | ❌ |
| `kvazaux-post-finitiva-radiko/{as,is,os,u}-komenca-radiko.txt` | 88 | 逐行 | **准根词·前缀形例外** | ❌ |
| **合计** | **6962** | | | 实际装载 **5665** 项 |

**关键实测结论：13 个约束表合计 1163 条，全部（100%）已包含在 `radiko.txt` 中。**

也就是说，它们**不是额外词汇，而是根词的属性标注**。例如：

- `kvazaux-post-finitiva-radiko/u-komenca-radiko.txt`：`uaz, udmurt, ued, uf, ugvis, ujgur, ukrain, ulamban, ulcer, ulis, uln, ultramar` —— 这些根词以 `u` 开头，但 `u` 是根词的一部分，不能被当成后缀切走。
- `kvazaux-finitiva-radiko/as-fina-radiko.txt`：`akantias, amateras, ananas, anas, arkansas, atlas, barabas, ĉas, frakas, helas` —— 这些以 `as` 结尾，但 `as` 不是动词后缀。
- `vokalo-fina-radiko/`：887 条以元音结尾的根词（`agvara, alfa, atalja, baba, beta, bilba, boa`…），它们自带词性标记，后面不能再接 `o/a/e/i/u`。

### 1.5 PIV 导入结果（2026-11-02，已完成）

以 **PIV（Plena Ilustrita Vortaro）** 的 HTML 导出为词源重建词表，工具链在 `tools/`（`piv_extract.js` → `piv_classify.js` → `piv_merge.js` → `piv_validate.js`，Node.js）。

**PIV 的结构标记被完整利用：**

| 标记 | 含义 | 用途 |
|---|---|---|
| `data-alfa="X"` | 词条的字母序形态 | **即词根**，与既有 `radiko.txt` 约定一致 |
| `kapvorto` 中 `X<span class="s">/</span>Y` | 词根 X + 词性尾 Y | 取 X（`dom/o` → `dom`） |
| `kapvorto` 中 `-X` | 黏着后缀 | 取 X（`-ig/` → `ig`） |
| `kapvorto` 中 `X!` | 感叹词 | 仍作词条收录 |
| `kapvorto` 首字母大写 | 专名 / 元素符号 | **剔除** |
| `data-teksto="X"` | 派生词中的词根 | 补充词根集 |

**约定契合度实测：原 `radiko.txt` 5523 条中 5509 条（99.7%）直接命中 PIV 的 `data-alfa`** —— 两套约定完全一致，合并是干净的并集，不会改写原有切分语义。

**合并结果：**

| 词表 | 导入前 | 导入后 | 说明 |
|---|---|---|---|
| `radiko.txt` | 5523 | **13842** | 新增 8955；剔除 924 条专名/元素符号；剔除 14 条损坏条目 |
| `vokalo-fina-radiko/` | 886 | **2241** | 由根词集自动重建 |
| `kvazaux-finitiva-radiko/` | 189 | **441** | 由规则重建 |
| `kvazaux-post-finitiva-radiko/` | 88 | **226** | 由规则重建 |
| `fundamenta-radiko.txt` | — | **2763** | PIV 标注 ★ 的基本词根（供 Phase 2 择优打分） |

**被剔除的 14 条损坏条目**（PIV 中完全不存在，原词表里的乱码）：`asekuraseps, brutalbub, esavese, frustrftalein, gruzgubernator, ĝjinanĝu, isatiski, jozefjube, ksaverksenofon, mozmucilag, novzelandnub, oscedoset, sputnikstab, ŝrikŝŝ`。其中如 `sputnik`、`brutal`、`bub`、`asez`、`novzeland`、`nub` 的正确形态 PIV 均已提供。

**被剔除的 924 条专名/元素符号**：`abraham, abudabi, afrik, afrodit, akademi, albert, albion, amateras, ananas, arkansas, australi, …, eŭrop, ev, evan, gutenberg, hajus?, kvinto?, …, zepelin, zohar, zoroastr, zurik` 等。这些是地名、人名、化学元素与专有名词，**不是语素**，对形态切分只会有害。

**筛选规则（可复现）：**

1. 剔除单字符条目（27 条：`b c d e f g h i j k l m n o p r s t u v z ĉ ĝ ĥ ĵ ŝ ŭ`）—— PIV 中这些是**字母表条目**（释义为 "Konsonanto, voĉa naza labialo" 一类的字母说明），不是语素。
   > 这一条至关重要：不过滤的话 `domo` 会被切成 `d+o+m+o`（4 种解），`komputilo` 产生 79 种解。过滤后 `domo` → **`dom+o`**，唯一解。
2. 剔除「所有词形均首字母大写」的条目（专名/元素符号）。注意 `ar`（后缀）与 `Ar`（河流）同形，故判定必须是**全部词形**都大写才剔除。
3. 保留 2 字符及以上的全部词条——`al, an, as, at, bo, do, ek, el, em, en, er, et, ig, il, in, is, it, iu, on, op, or, os, ot, uj, ul, um, us` 等在世界语中都是真实语素。

**关键副作用：D2 被自动解决。** `ant / at / ont / os / j / aj / oj` 这些早期版丢失的后缀，其本身就在 PIV 的词根集里（`ant`、`at`、`ont` 均为 PIV 独立词条），因此无需手工修改 `sufikso.txt`——`sufikso.txt` 中 30 个后缀里有 28 个与 `radiko.txt` 重复，本来就只是角色标注。

**实测切分效果**（复刻 `radiko.py` 语义，31 个样例）：

| 词 | 导入前 | 导入后（首个候选） |
|---|---|---|
| `domo` | kontroloto | **`dom+o`** |
| `domoj` | kontroloto | **`dom+oj`** |
| `lernanto` | kontroloto | **`lern+ant+o`** |
| `lernantoj` | kontroloto | **`lern+ant+oj`** |
| `kredito` | kontroloto | **`kred+it+o`** |
| `lernejo` | kontroloto | **`lern+ej+o`** |
| `scienco` | kontroloto | **`scienc+o`** |
| `skribi` | kontroloto | **`skrib+i`** |
| `malsanuleja` | kontroloto | **`mal+san+u+le+ja`** |
| `instruistino` | kontroloto | **`instru+is+ti+no`** |
| `universitato` | kontroloto | 11 种解，首选 `universitat+o` |
| **覆盖** | **2 / 31** | **31 / 31** |

### 1.6 导入后浮现的新最高优先级问题

词表补全后，**歧义取代了覆盖**成为主要矛盾：

- `komputilo` 6 种解、`familio` 9 种解、`universitato` 11 种解、`instruistino` 4 种解。
- 原因：`radiko.py` 的切分循环按**前缀长度从短到长**枚举（`for i in range(1, len(w)+1)`），**第一个候选永远是切得最碎的那个**，而不是最合理���。`domo` 恰好只有唯一解所以没暴露问题，但多数词不是。

**因此 Phase 2 的"择优打分"从"锦上添花"升为"必需项"**，且应优先于 trie 加速等性能优化。判定顺序建议：

1. 根词优先于后缀（`radiko.txt` 命中权重 > `sufikso.txt`）
2. 长匹配优先（避免 `kom+pu+ti+lo` 这类碎切）
3. 构词合法性（`-in-` 性别一致；`vokalo-fina-radiko/` 命中的根词不得再接元音尾）
4. 例外约束（`kvazaux-*` 命中的词不得按后缀切）
5. 基本词优先（`fundamenta-radiko.txt` 中的 ★ 词根加权）

在 `radiko.py` 尚未读取 13 个约束表之前，第 3、4 条无法生效——**Phase 1 的"约束表接入"与 Phase 2 的"择优打分"必须一起做**。


这解释了为什么作者一直没把它们"加载"——**当作普通词汇加载是空操作**，因为它们已经在 `radiko.txt` 里了。它们只有作为**约束**才有意义。

### 1.4 README 14 步规格的覆盖度

| README 步骤 | 状态标记 | `radiko.py` 覆盖情况 |
|---|---|---|
| 1-2 名词 `-n-` / `-j-` | ✓programita | ✅ 词典化覆盖（`-n`/`-j` 作为词条参与切分） |
| 3 限定式动词 | ✓programita | ✅（`as/is/os/us/u` 在 `sufikso.txt`） |
| 4-6 词性 `-o/-a/-e/-i` | ✓programita | ⚠️ 靠运行期追加 `a,e,i,o,u` 兜底，未区分元音结尾根词 |
| 7 性别 `-in-` | ✓programita | ⚠️ `in` 在 `radiko.txt` 里但不在 `sufikso.txt` |
| 8 分词 `ant/ont/int/at/ot/it` | ✓programita | ❌ **`ant/at/ont` 已丢失**（见 D2） |
| 9 其他后缀 | ✓programita | ✅（`sufikso.txt` 30 个） |
| 10 清理分隔符 | ✓programita | ✅（无分隔符概念，不需要） |
| 11 前缀 | ✓programita（需加速） | ✅（`prefikso.txt` 39 个，完整） |
| 12 根词切分 | **farota** | ✅ **这就是 `radiko.py` 本身**，但受词典质量拖累 |
| 13 小词处理后还原 | **farota** | ❌ 未实现（当前直接切分不回还原） |
| 14 表词替换 | **farota** | ❌ 未实现（`tabelvorto.txt` 被当普通词条用了） |
| 「误切分清理」 | farota | ❌ 未实现 |

---

## 2. 缺陷清单

### D1 —【P0，已解决】根词表缺失日常核心词汇

- **现象**：`domo`、`dom`、`komputilo`、`venkas`、`kredito`、`laborato`、`migranto`、`esperanto`、`familio`、`persono`、`infano`、`urbo`、`scienco`、`libro`、`skribi`、`paroli`、`veni`、`doni` …全部 `kontroloto`。
- **实测**：抽样 29 个日常高频词根，命中 6 个（21%）。
- **根因**：`radiko.txt` 是**技术/百科向**词表——开头是 `abak, abatis, abdomen, abevili, abiturient, ablativ, abnorm`，结尾是 `zenit, zepelin, zidovudin, zigom, zoolimorf`，系统性地偏学术，缺日常核心层。
- **附带问题**：文件**未按字母序排列**（5523 条中 3435 条位置与排序结果不符），人工检索与审校困难。
- **影响**：**这是项目可用性的第一决定因素。** 算法再好也切不开不认识的词。
- ✅ **2026-11-02 已解决**：PIV 导入后 `radiko.txt` 5523 → **13842**，高频词根全部命中，样例切分覆盖 **2/31 → 31/31**（详见 §1.5）。文件已按字母序重排。

### D2 —【P0，已解决】`sufikso.txt` 丢失 7 个后缀

- **现象**：早期版 `epo-morfemo-dividilo.py` 合并后的后缀集合共 37 个，现行 `sufikso.txt` 只有 30 个，缺 `in, ant, at, ont, ot, int, it`。
- **实测**：`in / ot / int / it` 仍在 `radiko.txt` 中（能切，但角色语义错位）；**`ant / at / ont` 完全不存在** → `lernanto` 切不出 `lern+ant+o`，实测 `kontroloto`。
- **影响**：分词后缀（README 第 8 步）功能回退，`-ant-/-at-/-ont-` 类派生词全部失败。
- ✅ **2026-11-02 已解决**：`ant / at / ont / os / j / aj / oj` 本身即 PIV 独立词条，随 PIV 导入自动进入 `radiko.txt`，**无需手工修改 `sufikso.txt`**。实测 `lernanto` → `lern+ant+o`、`lernantoj` → `lern+ant+oj`。

### D3 —【P0，部分解决】13 个约束表完全未接入（1163 条数据闲置）

- **现象**：`radiko.py` 的 `MORPHEME_FILES`（L69-75）只列 5 个文件，13 个约束表从未被读取。
- **影响**：`kvazaux-*` 例外表形同虚设 → `uaz` 会被切成 `u+az`、`ananas` 会被切成 `an+an+as` 之类的误切分；`vokalo-fina-radiko/` 标注的 886 个元音结尾根词无法应用"不得再接元音后缀"规则。
- ⚠️ **2026-11-02 部分解决**：三个约束目录已由 PIV 重建扩充（886 → **2241**，189 → **441**，88 → **226**），且与 `radiko.txt` 100% 一致。**但 `radiko.py` 仍未读取它们**——需与 Phase 2 的择优打分一起实施（见 §1.6）。

### D4 —【已解决】枚举全部解，无择优、无剪枝

- **原现象**：`esperanto_word_split` 枚举并返回**所有**合法切分，无上限、无剪枝。
- **原风险**：`a/e/i/o/u` 被显式加入词典，若遇到全由这些字母构成的词，切分方案数呈指数增长。
- **原影响**：输出形如 `ko|kom+pre+ne` 的候选堆，对下游语料构建无直接价值。
- ✅ **2026-11-03 已解决**：
  - 枚举改为**长匹配优先的 DFS**（倒序遍历前缀），天然先找到词汇化整词。
  - 排序键 `(语素数, -长度平方和, 拼写)`：少切优先 → 尊重词汇化；长匹配次之。
  - `--solvoj N`（默认 8）截断候选数；`_MAKSIMUMA_ESPLORO`（4000）与 `_MAKSIMUMA_PROFUNDECO`（64）双重安全阀。
  - 输出统一为 `vorto[[solvo1|solvo2|...]]`，单解即列表长度 1（见 §1.1）。
  - 实测：`horloĝ+o`、`ekskurs+o`、`ananas+o`、`lern+ant+o`、`komput+il+o` 均为首解。

### D5 —【P1】`result_cache` 无上限

- **原现象**：模块级字典只增不减。
- **原影响**：长语料下内存持续增长，与 README 自己担心的"语料很大"直接相关。
- ✅ **2026-11-03 已解决**：缓存移入 `Dividilo` 实例，超过 20 万词条时整体清空（简单但有效，避免长驻进程内存无界增长）。未采用 LRU 是因为 `dict` 清空的实现复杂度与收益比更好。

### D6 —【P1】`vorteto.txt` / `tabelvorto.txt` 的处理语义与 README 冲突

- **现象**：README 第 13 步要求小词**处理后还原为原形**，第 14 步要求表词**整体替换**。但 `radiko.py` 把它们当作普通可切分语素（L73-74）。
- **附带数据问题**：`vorteto.txt` 162 行中有 **6 条重复**，去重后仅 156 条。

### D7 —【P2】硬编码路径与文件名，无命令行参数

- **现象**：L70-74 硬编码 `./vortaro/*.txt` 相对路径，L86 硬编码 `input.txt` → `output.txt`。
- **影响**：无法指定词典目录、无法处理 stdin/stdout、无法批处理。

### D8 —【P2】连字符未按字母处理

- **现象**：README 第 12 步明确"streketo estu rigardata kiel litero"（连字符视作字母），但 `esperanto_tokenize`（L37-38）把 `-` 归入非字母 → 会在连字符处断词。

### D9 —【P2】大小写策略未定义

- **现象**：查找用 `w[:i].lower()`（L18），输出保留原形。但 README 第 11 步要求"忽略大小写查找，但不改变大小写"；第 8 步要求 `RINIT_O_J` → `RIN_IT_O_J` 这种全大写处理。当前对全大写词的行为未做区分。

### D10 —【P2】递归无深度保护

- **现象**：`esperanto_word_split` 递归深度等于词长，无显式上限。

### D11 —【P3】`esperanto_tokenize` 的字符串累加

- **现象**：L45 `last_part += text[pos]` 逐字符拼接。CPython 有优化，但改成 list + join 更稳妥。

### D12 —【P3】无测试、无 CI、无打包

- **现象**：仓库无 `requirements.txt`、无 `tests/`、无 CI、无 `pyproject.toml`。`radiko.py` 仅用标准库（早期版依赖第三方 `regex`，现已不在主干）。

### D13 —【P2】词典标注一致性缺陷（实例）

- **现象**：`radiko.txt` 中以元音结尾的根词有 **887** 条，而 `vokalo-fina-radiko/` 只标注了 **886** 条。
- **具体**：`naci` 在 `radiko.txt` 中但未被 `vokalo-fina-radiko/i_fina_radiko.txt` 标注。
- **来源**：正是 2024-04-22 提交 `56511e0` 把错误的 `nacionalism` 改为 `naci` 时，只改了主词表、没同步标注表引入的。
- **影响**：说明**标注表与主词表之间缺少一致性校验机制**，人工维护必然继续漂移。
- ✅ **2026-11-02 已解决**：PIV 导入时三个约束目录全部由根词集整体重建，`naci` 已自动补入 `i_fina_radiko.txt`，当前 2241 / 2241 完全一致。

### D14 —【P0】"最小可识别词素"划分会切碎词汇化复合词

这是**覆盖问题解决后暴露的核心正确性问题**。

- **现象**：`horloĝo` 会被切成 `hor+loĝ+o`（应为 `horloĝ+o`）；`ekskurso` 会被切成 `eks+kurs+o`（应为 `ekskurs+o`）；`ananaso` 会被切成 `an+an+as+o`。
- **实测规模**：`radiko.txt` 13842 条中，**7270 条（52.5%）可以被再切成 2 个以上词典中已有的成分**。若采用"最小可识别词素"策略，一半以上的词根会被切碎。
- **根因**：世界语的形态切分有两个相互冲突的目标——"切到最小语素"与"尊重词汇化"。`horloĝ`（钟表）历史上来自 `hor`（时）+ `loĝ`（居住），但它早已是一个不可再分的词汇单位；PIV 把它列为独立词条，而不是 `hor` 的派生词。
- **真正的判据**：**PIV 的 `art`（独立词条）与 `div class="derivajho"`（派生词）之分，正是"词汇化 vs 规则派生"的分界线。** 实测证据：

| 词形 | PIV 是否独立词条 | 正确切分 | 理由 |
|---|---|---|---|
| `horloĝ` | ✅ `horloĝ/o` | `horloĝ+o` | 词汇化，不能再切 |
| `ekskurs` | ✅ `ekskurs/o` | `ekskurs+o` | 词汇化（虽然 `eks`、`kurs` 也都是词条） |
| `ananas` | ✅ `ananas/o` | `ananas+o` | 词汇化（`an` 不是词条） |
| `acerb` | ✅ `acerb/a` | `acerb+a` | 词汇化 |
| `universitat` | ✅ `universitat/o` | `universitat+o` | 词汇化 |
| `esperant` | ✅ `Esperant/o` | `esperant+o` | 专名，README 要求忽略处理 |
| `lernant` | ❌ 无 | `lern+ant+o` | 规则派生，`lern` 的 derivajho |
| `komputil` | ❌ 无 | `komput+il+o` | 规则派生 |
| `instruistin` | ❌ 无 | `instru+ist+in+o` | 规则派生 |

- **对策一（解决绝大多数情况）：最长匹配优先。** 因为 `radiko.txt` 现在**就是 PIV 词条集**，"优先匹配最长的词根"在语义上等于"优先尊重词汇化"。实测（`tools/strategy_compare.js`）：
  - `horloĝo` → `horloĝ+o` ✅
  - `ekskurso` → `ekskurs+o` ✅
  - `ananaso` → `ananas+o` ✅
  - `lernanto` → `lern+ant+o` ✅（`lernant` 不是词条，长匹配自然落到 `lern`）
  - `komputilo` → `komput+il+o` ✅
  - `instruistino` → `instru+ist+in+o` ✅
  - `malsanuleja` → `mal+san+ul+ej+a` ✅
  - 也就是说，**把 `range(1, len+1)` 改成倒序几乎是免费的胜利**。

  ```python
  # 现状（短优先，倾向切碎）
  for i in range(1, len(w) + 1):
      if w[:i].lower() in dictionary:

  # 建议（长优先，尊重词汇化）
  for i in range(len(w), 0, -1):
      if w[:i].lower() in dictionary:
  ```
  更稳妥的做法是保留"枚举全解 + 打分排序"，把「长匹配」作为第一条打分规则（而不是改成贪心，以免丢失多解能力）：分数 = Σ (成分长度²) 之类，天然偏好少切、长切。

- **对策二（真正不可消解的部分）：同形异义必须多解输出。** `heroino` 是典型：
  - `heroin/o` 是 PIV 独立词条（海洛因）
  - `hero/o` 也是 PIV 独立词条（英雄），加 `-in-`（女性）得"女英雄"
  - **两种切分在词法上都完全合法，任何算法都无法单靠字符串判定。** 依据必须来自上下文语义。
  - 同类：`kredito` = `kredit+o`（信用）或 `kred+it+o`（被相信的）。
  - 因此输出格式必须能承载多解，例如 `heroino{{heroin+o @药物 | hero+in+o @人}}`，并附置信度或义项标签，交由下游（人工校对或语义消歧）选择。**不能假装只有一个正确答案。**

- **对策三（已评估，暂不采用）：自动生成"词汇化复合词"白名单。** 曾尝试用「整词是词根 ∧ 可切成 ≥2 个长度 ≥3 的语素」自动导出，得到 2484 条候选（17.9%）。**但实测噪声极大**：`akademi = akad+emi`、`almenaŭ = alme+naŭ`、`aksiom = aks+iom`、`alfabet = alfa+bet` 全是误判（纯字符串巧合，非真实构词）。
  - 结论：**字符串层面的"可分解"不等于"复合词"**，无法自动区分 `horloĝ`（真复合）与 `akademi`（借词巧合）。
  - 因此不作为权威白名单发布。若将来需要"展示词源切分"这类功能，应作为**人工审校的候选清单**另行维护，且不影响主切分逻辑——主逻辑靠对策一（长匹配）即可正确处理。

- **对策四：约束表接入后，可进一步降噪。** `vokalo-fina-radiko/` 与 `kvazaux-*` 能排除一部分非法切分（如元音结尾根词后不得再接元音）。

- **影响**：这是 Phase 2 "择优打分"的核心内容，不是可选项。若不处理，词典规模翻倍反而会**让切分质量下降**——因为成分越多，错误组合越多（实测 `komputilo` 的候选解从 6 种涨到更多碎切）。

### 1.7 D14 实施结果（2026-11-03）

已落实到 `radiko.py`，34 项测试全绿（`python tests/test_radiko.py`）。排序键最终为六元组：

```python
(
    0 if len(partoj) == 1 else 1,          # 1 整词命中优先
    0 if fina in FINAJHOJ_POR_ORDO else 1, # 2 末段是纯语法词尾
    meze_funkciaj,                         # 3 中部不出现虚词
    len(partoj),                           # 4 语素数量少者优先
    -sum(len(p) ** 2 for p in partoj),     # 5 长匹配优先
    tuple(partoj),                         # 6 稳定 tie-break
)
```

枚举阶段还有三条**位置约束**，用于剔除非法切分：

| 约束 | 作用 | 反例（不约束时） |
|---|---|---|
| `NUR_FINAJ = {j, n, as, is, os, us}` 只能在词末 | 动词词尾、复数/宾格 | `montras → mont+ras`；`ananaso → a+n+anas+o` |
| `GRAMATIKAJ_FINAJHOJ`（`a/e/i/o/u/oj/aj`）后面只能是 `''`/`j`/`n` | 语法元音必须词末 | `avino → a+vin+o` |
| 枚举倒序遍历前缀 | 先命中长词根 | `horloĝo → hor+lo+ĝ+o` |

实测效果（`README.md` 中 1365 个词形）：

| 指标 | 结果 |
|---|---|
| 成功切分 | **95.5%**（1302/1365） |
| `kontroloto` | 4.5%（62 个，绝大多数是非世界语：`python`、`txt`、`PIV`、`Script`、`output`） |

关键样例（首解）：

| 词 | 输出 |
|---|---|
| `horloĝo` | `horloĝ+o \| hor+loĝ+o` |
| `ekskurso` | `ekskurs+o \| eks+kurs+o` |
| `ananaso` | `ananas+o` |
| `heroino` | `heroin+o \| hero+in+o` ✓ 两义并存 |
| `lernanto` | `lern+ant+o` |
| `komputilo` | `Komput+il+o \| Kom+put+il+o` |
| `Maljunulo` | `Mal+jun+ul+o \| Mal+ju+nul+o` |
| `Alportu` | `Al+port+u \| Alp+ort+u` |
| `avino` | `av+in+o` |
| `domojn` | `dom+oj+n` |
| `kun` | `kun \| ku+n` |

**实施中发现并修正的数据问题（重要）：**

1. **`data-alfa` 不总是裸词根**。PIV 里 `data-alfa="akvo"` 但 `kapvorto` 是 `akv/o`，真词根是 `akv`。若直接用 `data-alfa`，`akvon` 会被切成 `akvo+n`。逐条比对 16649 个词条后，仅 4 条真正受影响（`akvo`、`barmicv`、`kalaazar`、`metakrilataacid`），已移除。
2. **PIV 的 59 个感叹词混进了词根表**（`pu`、`be`、`fi`、`ha`、`ve`、`oj`…）。它们不是语素，保留会切出 `pu+rig+u`。已全部移除（含各约束表，共 99 行）。
3. **`sufikso.txt` 缺 7 个后缀**（`ant/at/ont/ot/int/it/in`），这正是 D2。之前靠它们在 `radiko.txt` 里"碰巧能用"，但 2 字母的 `in/at/ot/it` 会被误判为小品词。已补全至 37 个。
4. **PIV 把月份首字母大写**（`Januar/o`、`Novembr/o`、`Lun/o`），被"专名过滤"误删。世界语实际小写，已补回 9 个（`novembr` 等）。
5. **`vorteto.txt` 与 `radiko.txt` 重叠**的虚词（`ju`、`kun`、`nul`、`al`、`mi`…）保留双份，但**只在中部位置降权**——词首的 `al`（`alporti`）、`mi`（`mia`）是合法的，不能一禁了之。

**词表最终规模**：`radiko.txt` 13788 / `sufikso.txt` 37 / `prefikso.txt` 39 / `tabelvorto.txt` 45 / `vorteto.txt` 162 / `fundamenta-radiko.txt` 2763。

---

## 3. 分阶段路线图

### Phase 1 — 词典与正确性（最高优先，解锁可用性）

> 目标：让 `radiko.py` 能切开日常文本。**本阶段不碰核心算法结构。**

#### P1-1 补全根词表（D1）

- **目标**：日常高频词根覆盖率从 21% → 90%+。
- **做法**：
  1. 从公开的世界语词表（如 Wikimedia dumps、Wiktionary 的 Esperanto 条目、`Vojaĝo` 词表）导出**核心日常词根**，与现有 5523 条**合并去重**，而非替换。
  2. 合并后按字母序重排 `radiko.txt`（顺便修掉 D1 的"无序"问题）。
  3. 差异报告：新增多少条、删除了多少条、哪些现有条目被判定为非词根。
- **验收标准**：
  - 本文档附录 B 的 29 个高频词根抽样全部命中；
  - `domo` → `dom+o`、`komputilo` → `komputil+o`、`venkas` → `venk+as`；
  - `radiko.txt` 与 `Sort-Object` 的差异位置数 < 50。
- **风险**：外部词表来源不同，词根切法会有分歧（同一词根在不同词表里可能带/不带元音尾）。**必须先定切分约定**，见 ADR-1。

#### P1-2 修复 `sufikso.txt`（D2）

- **做法**：把 `ant, at, ont, ot, int, it, in` 补入 `sufikso.txt`（保持 `{...}` 单行格式）。
- **同步**：`in/ot/int/it` 目前同时存在于 `radiko.txt`。建议**从 `radiko.txt` 移除**这 4 条（它们是后缀不是根词），避免同一串既当根词又当前缀导致的重复切分解。
- **验收标准**：`lernanto` → `lern+ant+o`；`lernantoj` → `lern+ant+o+j`。

#### P1-3 接入 13 个约束表（D3）

- **做法**：把约束表接入切分流程，但**不是当普通词汇加载**（那会重复），而是作为约束集：
  - `vokalo-fina-radiko/` → 命中根词后**禁止再接** `a/e/i/o/u`；
  - `kvazaux-finitiva-radiko/` → 命中整词时**禁止**在词尾再切 `as/is/os/us/u`；
  - `kvazaux-post-finitiva-radiko/` → 命中整词时**禁止**在词首切 `as/is/os/u`。
- **角色标注**：需要区分"可切分语素"与"约束集"。建议在 `radiko.py` 里用**目录约定**即可（`vortaro/` 根下 = 语素；`vokalo-fina-radiko/`、`kvazaux-*` = 约束），无需改动文件格式。
- **验收标准**：`uaz` 不再被切成 `u+az`；`ananas` 不再被切成 `an+an+as`。

#### P1-4 词典一致性自检脚本（D13）

- **做法**：新增 `tools/check_vortaro.py`，校验：
  - 元音结尾根词数 == `vokalo-fina-radiko/` 标注数（当前 887 vs 886，报错）；
  - 约束表所有条目都在 `radiko.txt` 中（当前 100% 满足，保持）；
  - 各表无重复条目（`vorteto.txt` 当前 6 条重复）；
  - `sufikso.txt` / `prefikso.txt` 的 `{...}` 格式可解析。
- **验收标准**：脚本退出码为 0；把 `naci` 补进 `i_fina_radiko.txt` 后仍为 0。

#### P1-5 CLI 参数化（D7）

- **目标**：
  ```
  python radiko.py -i input.txt -o output.txt [--vortaro vortaro/]
                   [--mode all|best] [--max-splits N] [--report stats.json]
  ```
- **注意**：默认值必须与现状完全一致（`input.txt` / `output.txt` / `./vortaro/`），保证向后兼容。

#### P1-6 连字符与大写（D8, D9）

- **做法**：`-` 加入 `ESPERANTO_CHARACTERS`（L5）即满足 README 第 12 步；全大写词按 README 第 8 步特殊处理（`Esperant` 前缀例外）。
- **注意**：这会改变分词边界，需**先有测试再改**（见 Phase 3 的测试先行要求）。

#### Phase 1 验收门槛

- 上述 6 项全部完成；
- 新增回归测试通过；
- `README.md` 顶部的 `(ATENTU: NE UZEBLA NUN!)` 在覆盖率达标后**可以移除**，并把"13 feb. 2025"条目改写为当前状态说明。

---

### Phase 2 — 算法增强（有 Phase 1 的数据才有意义）

#### P2-1 从"枚举全解"改为"择优 + 备选"（D4）

- **目标**：输出一个**最佳解** + 可选备选，而不是无序候选堆。
- **打分维度**（建议）：
  1. 根词优先于后缀（`radiko.txt` 命中的权重 > `sufikso.txt`）；
  2. 优先长匹配（贪心偏向更长的词根）；
  3. 构词合法性（`-in-` 性别一致：`-a` → `-in-o`；元音结尾根词不再接元音）；
  4. 拼写规则约束（README 的「误切分清理」一节：`l_um_o`、`hor_loĝ_o`、`eks_kurs_o`）。
- **实现**：把 `esperanto_word_split` 从"返回全部"改为"带权 DP 求最优"，用字典序/最大权重回溯。
- **验收标准**：输出格式 `词[[最佳解]]` 或 `词[[最佳解|备选1|备选2]]`，`--mode all` 保留旧行为。

#### P2-2 前缀树（trie）加速替换逐长度扫描（L17）

- **现状**：对每个词的每个位置做 `w[:i].lower()` 切片 + 哈希查找 → 每词 O(L²) 字符操作。
- **改法**：构建 trie，一次沿字符下行即可得到**所有**前缀命中位置 → 每词 O(L)。
- **收益**：单看提升有限（词很短），但与 P2-1 的 DP 结合后是必要前提。

#### P2-3 剪枝与缓存有界化（D4, D5, D10）

- **做法**：
  - `max_splits`（默认 50）截断候选数，超出标记为 `kontroloto (tro multaj solvoj)`；
  - `max_depth`（默认 64）保护递归；
  - `result_cache` 改为 LRU（`functools.lru_cache(maxsize=...)` 或手写），可配置上限；
  - 可选：按词长分桶缓存，短词（高频）常驻、长词淘汰。
- **注意**：`result_cache` 是模块级全局且被 `esperanto_word_split` 直接访问，改成 `lru_cache` 时需要把 `dictionary` 变成闭包/全局单例，否则缓存键会带上词典参数。

---

### Phase 3 — 工程化

| 任务 | 内容 |
|---|---|
| 测试 | `pytest`，夹具用 `radiko.py` 末尾注释里的样例：`Maljunulo| — |Ho|, |kompreneble|. |Bonvolu| |sidiĝi|. ( |Al| |la| |knabino|. ) Alportu akvon, infano, purigu la glason antaŭe.` + README 第 9 步的 `malsanulejan_in_o` → `lsan_ul_ej_an_in_o` + 第 11 步的 `geboav_o_j` → `ge_bo_av_o_j`、`Maldis_ig_i` → `Mal_dis_ig_i` |
| CI | GitHub Actions：`pytest` + 词典一致性自检（P1-4） |
| 打包 | `pyproject.toml`，暴露为库（README「Alia aldona pensadoo」里作者自己也提到"La programo eble povas fariĝi biblioteko"） |
| 批量处理 | 支持目录批处理、多进程（语料构建场景） |
| 词频 | 引入词频权重，支撑 P2-1 的择优打分 |
| 可选 | 语料输出格式扩展：JSONL、TSV，便于下游直接消费 |

---

## 4. 关键设计决策（ADR）

### ADR-1 词根切分约定必须先定死

外部词表对"词根是否带元音尾"的处理不一致：有的把 `dom` 存为词根、有的存 `dom`+`o` 为整词，有的把 `lern` 存成 `lern`、`lernant` 存成 `lernant`。

**决策**：统一采用 **"词根不带词性元音尾"** 约定（`dom` + `o`），与现有 `radiko.txt` 的 `universitat` / `amalga` 风格一致。例外（`alfa`、`agvara` 这类本身以元音结尾的根）由 `vokalo-fina-radiko/` 承载。

**影响**：这是 Phase 1 所有词典工作的前置约定，不定清楚会导致合并词表时无法自动去重。

### ADR-2 约束表与语素表必须分角色，不能混在一个 set

13 个约束表的 1163 条 100% 已在 `radiko.txt` 中。若按普通语素加载则是**空操作**；若混在一起还会掩盖"这个词既是根词又是约束"的语义。

**决策**：程序内用**两个集合**——`MORPHEME_SET`（可切分）与 `CONSTRAINT_SET`（约束/例外），按目录约定划分，不修改文件格式。

### ADR-3 输出格式：默认给最优解，保留全解为选项

当前输出 `词[[解1|解2|解3]]` 对人阅读尚可，对语料构建无用。改为默认输出最优解、`--mode all` 保留旧行为，避免破坏既有使用方式。

### ADR-4 词典热重载

README「Alia aldona pensadoo」明确提到希望词典能作为外部文件方便更新。**决策**：词典路径走 CLI 参数 + 默认值保持不变；后续可加 `--reload` 在长驻进程中热加载。

### ADR-5 向后兼容优先

所有 CLI 新参数都有与现状一致的默认值；`--mode all` 下输出格式与现行版本逐字节一致。任何阶段都应能用同一份输入对比新旧输出。

---

## 5. 测试与验收矩阵

| 类别 | 用例 | 期望 |
|---|---|---|
| 回归（基线） | `radiko.py` 末尾样例整段 | 与现行输出一致 |
| 回归（基线） | `malsanulejan_in_o` | `lsan_ul_ej_an_in_o` |
| 回归（基线） | `geboav_o_j` | `ge_bo_av_o_j` |
| 回归（基线） | `Maldis_ig_i` | `Mal_dis_ig_i` |
| 词典修复 | `lernanto` | `lern+ant+o` |
| 词典修复 | `domo` | `dom+o` |
| 词典修复 | `komputilo` | `komputil+o` |
| 约束表 | `uaz` | 不被切成 `u+az` |
| 约束表 | `ananas` | 不被切成 `an+an+as` |
| 约束表 | `alfa` | 不被切成 `al+f+a` |
| 一致性 | 元音结尾根词数 vs 标注数 | 相等（当前 887 ≠ 886，**修前应失败**） |
| 一致性 | 各表重复条目 | 0（当前 `vorteto.txt` 有 6 条，**修前应失败**） |
| 健壮性 | 空文件 / 纯标点 / 超长词 / 全元音词 | 不崩溃，按约定降级为 `kontroloto` |
| 性能 | 1 MB 语料 | 给出实测基线并纳入回归阈值 |

---

## 6. 里程碑与工作量估算

| 里程碑 | 内容 | 估算 | 依赖 |
|---|---|---|---|
| M1 | P1-4 词典自检脚本（先建网，先看清） | 0.5 天 | ✅ `tools/piv_validate.js` |
| M2 | ADR-1 切分约定落定 + 外部词表来源选定 | 0.5 天 | ✅ 约定 = PIV `data-alfa`（与原表 99.7% 一致）；来源 = PIV |
| M3 | P1-1 根词表合并（最大块，含差异审校） | 3-5 天 | ✅ **已完成**，`radiko.txt` 5523 → 13842 |
| M4 | P1-2 `sufikso.txt` 修复 | 0.5 天 | ✅ 由 M3 自动解决（后缀本身在 PIV 词根集中） |
| M5 | P1-3 约束表接入 | 1-2 天 | ⬜ 词表已重建扩充，**代码尚未读取**；与 M9 合并做 |
| M6 | P1-5 CLI 参数化 | 0.5 天 | ⬜ |
| M7 | P1-6 连字符/大写 | 1 天 | ⬜ |
| M8 | 回归测试套件 | 1-2 天 | ✅ **已完成**（`tests/test_radiko.py`，34 项） |
| M9 | P2-1 择优打分 | 3-5 天 | ✅ **已完成**（见 §1.7） |
| M10 | P2-2 trie + P2-3 剪枝 | 1-2 天 | ⚠️ 剪枝已完成；trie 未做（当前性能足够） |
| M11 | CI + 打包 + 批处理 | 2-3 天 | ⬜ |

**建议顺序：M1 → M2 → M4 → M5 → M8 → M3 → M6 → M7 → M9 → M10 → M11**
（先建网再补词，先有测试再动算法。）

**当前状态（2026-11-02）：M1、M2、M3、M4 已完成。** 接下来的建议顺序变为：

> **M8（回归测试）→ M5+M9（约束表接入与择优打分，一起做）→ M6 → M7 → M10 → M11**

理由：词表刚刚大改（规模 ×2.5），正需要一套回归网兜底；而覆盖问题解决后，歧义已成为主要矛盾，M5 与 M9 不宜再拆开做。

---

## 7. 风险登记

| 风险 | 等级 | 缓解 |
|---|---|---|
| 外部词表的词根切法与本项目约定不一致 | 高 | ADR-1 先定约定；合并时逐条差异审校，不自动覆盖 |
| 词表合并引入大量重复/垃圾条目 | 中 | M1 的自检脚本先跑；合并后跑词频与重复检查 |
| 约束表接入后与 `sufikso.txt` 规则冲突 | 中 | 用 `uaz`/`ananas`/`alfa` 三个用例做回归闸门 |
| 择优打分改变既有输出，破坏下游 | 中 | `--mode all` 保留旧行为；ADR-5 要求逐字节可比对 |
| `result_cache` 改 LRU 时缓存键含词典参数 | 中 | 把词典改为单例/闭包，避免 `lru_cache` 把 `dictionary` 计入键 |
| 项目长期停更后词典来源失效 | 低 | 词表入库并随仓库版本化，不依赖运行时在线获取 |
| AGPL-3.0 许可下的词典来源许可 | 中 | 外部词表入库前确认许可允许再分发 |

---

## 附录 A 术语对照

| Esperanto / 代码 | 中文 |
|---|---|
| `radiko` | 词根 |
| `prefikso` / `sufikso` | 前缀 / 后缀 |
| `vorteto` | 小词（介词、连词等） |
| `tabelvorto` | 表词（替代词） |
| `kvazaux-finitiva-radiko` | 准词根·终结形（词尾形似后缀但实为词根一部分） |
| `kvazaux-post-finitiva-radiko` | 准词根·前缀形（词首形似后缀但实为词根一部分） |
| `vokalo-fina-radiko` | 元音结尾词根 |
| `morfemo` | 语素 |
| `kontroloto` | 待检查（分词失败标记） |

## 附录 B README「Alia aldona pensadoo」逐条落点

作者在 README 末尾自己列的设想，与本方案的对应关系：

| README 原文（意译） | 本方案落点 |
|---|---|
| "可用语素列表代替反复查找，以便更快计算" | P2-2 trie（ADR-4 词典外置） |
| "也许可以把根词按长度排序" | P2-1 打分维度 2（长匹配优先） |
| "把长语素先处理，短语素另想办法" | P2-3 分桶缓存 |
| "可以用外部词表文件代替写死在程序里的数组" | ADR-4 + P1-5 CLI |
| "程序也许可以变成一个库" | Phase 3 打包 |
| "坏切分也许需要在多个步骤之间反复清理" | P2-1 打分维度 4（README「误切分清理」一节） |
| "词表很大，处理的文本也很大，希望用库优化" | P2-2 + Phase 3 批处理 |

## 附录 C 高频词根覆盖抽样基线

抽样 29 个日常高频词根，**导入前**词典命中 6 个（21%）：

- ✅ 命中（6）：`man, am, land, vid, aŭd, don`
- ❌ 缺失（23）：`dom, famili, person, infan, urb, lernej, oplac, labor, komerc, scienc, mensaj, manĝaj, remaj, vektoro, linio, libro, skrib, parol, ir, ven, iri, pren, doni`

补充：`al / mal / fili / lern` 经 `radiko.txt` 命中，但 `dom / venk / kred / labor / komputil / esperant / migr / univers / san` 等同样基础的词根**完全不在任何词表中**——缺的不是总量，而是日常核心那一层。

**✅ 2026-11-02 更新：PIV 导入后，以上 ❌ 清单全部转为命中**（注意 `lernej/oplac/mensaj/manĝaj/remaj/vektoro/linio/libro/iri/doni` 这几个是形容词/复数/全词形，其**词根**形态 `lerne/oplak/mesaĝ/manĝ/rem/vektor/lini/libr/ir/don` 均已在库）。

**Phase 1 完成时，❌ 清单应全部转为命中。**
