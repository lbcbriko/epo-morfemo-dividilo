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

| 优先级 | 议题 | 阶段 | 预期收益 |
|---|---|---|---|
| **P0** | 根词表补全（日常核心词汇） | Phase 1 | 决定项目能否真正可用 |
| **P0** | `sufikso.txt` 补回 `ant/at/ont` | Phase 1 | 修复分词后缀功能回退 |
| **P0** | 13 个约束表接入（当前 100% 未使用） | Phase 1 | 解锁 README 第 12 步 |
| **P1** | 切分策略：全解枚举 → 择优 + 约束校验 | Phase 2 | 输出可用结果而非候选堆 |
| **P1** | 缓存有界化、递归剪枝 | Phase 2 | 防止长语料内存爆炸 |
| **P2** | CLI 参数化、连字符按字母处理、大小写策略 | Phase 1 | 可用性与正确性 |
| **P2** | 测试、CI、打包为库 | Phase 3 | 可维护性 |

---

## 1. 现状基线

### 1.1 `radiko.py` 代码结构

| 行号 | 函数 | 职责 |
|---|---|---|
| 8 | `result_cache` | 模块级全局缓存，以"剩余串"为键 |
| 11-26 | `esperanto_word_split(w, dictionary)` | 记忆化递归，枚举**全部**合法切分 |
| 29-46 | `esperanto_tokenize(text)` | 单遍字符扫描，按字母/非字母切词 |
| 48-66 | `esperanto_tokenize_and_analyze_file()` | 逐 token 切分并写出 `词[[切分1|切分2]]` |
| 69-86 | `__main__` | 加载 5 个词表 → 调 `input.txt` → `output.txt` |

核心切分逻辑（L17-18）：

```python
for i in range(1, len(w) + 1):
    if w[:i].lower() in dictionary:
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

### D1 —【P0】根词表缺失日常核心词汇

- **现象**：`domo`、`dom`、`komputilo`、`venkas`、`kredito`、`laborato`、`migranto`、`esperanto`、`familio`、`persono`、`infano`、`urbo`、`scienco`、`libro`、`skribi`、`paroli`、`veni`、`doni` …全部 `kontroloto`。
- **实测**：抽样 29 个日常高频词根，命中 6 个（21%）。
- **根因**：`radiko.txt` 是**技术/百科向**词表——开头是 `abak, abatis, abdomen, abevili, abiturient, ablativ, abnorm`，结尾是 `zenit, zepelin, zidovudin, zigom, zoolimorf`，系统性地偏学术，缺日常核心层。
- **附带问题**：文件**未按字母序排列**（5523 条中 3435 条位置与排序结果不符），人工检索与审校困难。
- **影响**：**这是项目可用性的第一决定因素。** 算法再好也切不开不认识的词。

### D2 —【P0】`sufikso.txt` 丢失 7 个后缀

- **现象**：早期版 `epo-morfemo-dividilo.py` 合并后的后缀集合共 37 个，现行 `sufikso.txt` 只有 30 个，缺 `in, ant, at, ont, ot, int, it`。
- **实测**：`in / ot / int / it` 仍在 `radiko.txt` 中（能切，但角色语义错位）；**`ant / at / ont` 完全不存在** → `lernanto` 切不出 `lern+ant+o`，实测 `kontroloto`。
- **影响**：分词后缀（README 第 8 步）功能回退，`-ant-/-at-/-ont-` 类派生词全部失败。

### D3 —【P0】13 个约束表完全未接入（1163 条数据闲置）

- **现象**：`radiko.py` 的 `MORPHEME_FILES`（L69-75）只列 5 个文件，13 个约束表从未被读取。
- **影响**：`kvazaux-*` 例外表形同虚设 → `uaz` 会被切成 `u+az`、`ananas` 会被切成 `an+an+as` 之类的误切分；`vokalo-fina-radiko/` 标注的 886 个元音结尾根词无法应用"不得再接元音后缀"规则。

### D4 —【P1】枚举全部解，无择优、无剪枝

- **现象**：`esperanto_word_split` 枚举并返回**所有**合法切分（L19-23），无上限、无剪枝。
- **风险**：`a/e/i/o/u` 被显式加入词典（L86），若遇到全由这些字母构成的词，切分方案数呈指数增长。
- **影响**：输出形如 `ko|kom+pre+ne` 的候选堆，对下游语料构建无直接价值。

### D5 —【P1】`result_cache` 无上限

- **现象**：L8 的模块级字典只增不减。
- **影响**：长语料下内存持续增长，与 README 自己担心的"语料很大"直接相关。

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
| M1 | P1-4 词典自检脚本（先建网，先看清） | 0.5 天 | — |
| M2 | ADR-1 切分约定落定 + 外部词表来源选定 | 0.5 天 | — |
| M3 | P1-1 根词表合并（最大块，含差异审校） | 3-5 天 | M2 |
| M4 | P1-2 `sufikso.txt` 修复 | 0.5 天 | — |
| M5 | P1-3 约束表接入 | 1-2 天 | M4 |
| M6 | P1-5 CLI 参数化 | 0.5 天 | — |
| M7 | P1-6 连字符/大写 | 1 天 | P1-5 |
| M8 | 回归测试套件（测试先行补上） | 1-2 天 | M3-M5 |
| M9 | P2-1 择优打分 | 3-5 天 | M3-M5 |
| M10 | P2-2 trie + P2-3 剪枝 | 1-2 天 | M9 |
| M11 | CI + 打包 + 批处理 | 2-3 天 | M8 |

**建议顺序：M1 → M2 → M4 → M5 → M8 → M3 → M6 → M7 → M9 → M10 → M11**
（先建网再补词，先有测试再动算法。）

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

抽样 29 个日常高频词根，现行词典命中 6 个（21%）：

- ✅ 命中（6）：`man, am, land, vid, aŭd, don`
- ❌ 缺失（23）：`dom, famili, person, infan, urb, lernej, oplac, labor, komerc, scienc, mensaj, manĝaj, remaj, vektoro, linio, libro, skrib, parol, ir, ven, iri, pren, doni`

补充：`al / mal / fili / lern` 经 `radiko.txt` 命中，但 `dom / venk / kred / labor / komputil / esperant / migr / univers / san` 等同样基础的词根**完全不在任何词表中**——缺的不是总量，而是日常核心那一层。

**Phase 1 完成时，❌ 清单应全部转为命中。**
