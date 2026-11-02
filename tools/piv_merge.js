// PIV -> vortaro/ 合并器
//   node tools/piv_merge.js <piv.html> [--write]
// 依据 PIV 的 data-alfa 词根、词性结尾与派生词形，生成/更新 vortaro/ 下的词表。
const fs = require('fs');
const path = require('path');

const repo = path.resolve(__dirname, '..');
const tmp = path.join(repo, '.piv-tmp');
const rd = (p) => fs.readFileSync(p, 'utf8').split(/\r?\n/).map(s => s.trim()).filter(Boolean);
const rdSet = (p) => new Set(rd(p));
const write = process.argv.includes('--write');

const endingMap = JSON.parse(fs.readFileSync(path.join(tmp, 'piv_alfa_endings.json'), 'utf8'));
// 使用经分类筛选后的集合：排除单字符（字母表条目）与纯专名/元素符号
const pivAlfa = rdSet(path.join(tmp, 'piv_keep.txt'));
const pivTeksto = new Set([...rdSet(path.join(tmp, 'piv_teksto.txt'))].filter(s => s.length >= 2));
const pivFund = rdSet(path.join(tmp, 'piv_fundamenta.txt'));

// ---------- 1. 派生词形 -> 后缀清单 ----------
const html = fs.readFileSync(process.argv[2], 'utf8');
const derivSuffix = new Map();          // 后缀 -> 出现次数
const derivBase = new Map();            // 后缀 -> 样例词根
const dRe = /<strong class="d"[^>]*>([\s\S]*?)<\/strong>/g;
let m;
while ((m = dRe.exec(html)) !== null) {
  const inner = m[1];
  const base = (inner.match(/data-teksto="([^"]*)"/) || [])[1] || '';
  // 后缀 = 去掉全部标签后，位于词根 span 之后的文本
  const after = inner.split('</span></span>').pop() || '';
  const suf = after.replace(/<[^>]+>/g, '').trim();
  if (!suf) continue;
  derivSuffix.set(suf, (derivSuffix.get(suf) || 0) + 1);
  if (!derivBase.has(suf)) derivBase.set(suf, base);
}

// ---------- 2. 词性结尾清单 ----------
const wordEndings = new Map();
for (const a of pivAlfa) {
  const m2 = endingMap[a] || {};
  for (const e of Object.keys(m2)) {
    if (e === '(sen /)') continue;
    wordEndings.set(e, (wordEndings.get(e) || 0) + 1);
  }
}

// ---------- 3. 合并 radiko.txt ----------
const radikoOld = rd(path.join(repo, 'vortaro', 'radiko.txt'));
const pivOnly = [...pivAlfa].filter(a => !radikoOld.includes(a));
// radiko.txt 中 PIV 没有的条目 -> 判定是否为损坏条目
const pivSet = pivAlfa;
const dropped = radikoOld.filter(r => !pivSet.has(r));
const droppedGarbage = dropped.filter(r => !/^[a-zĉĝĥĵŝŭ]+$/.test(r) || dropped.includes(r) === false);
const radikoNew = [...new Set([...radikoOld.filter(r => pivSet.has(r)), ...pivAlfa, ...pivTeksto])]
  .filter(r => /^[a-zĉĝĥĵŝŭ]+$/.test(r))
  .sort();

// ---------- 4. vokalo-fina-radiko ----------
const vowelFiles = { a: [], e: [], i: [], o: [], u: [] };
for (const r of radikoNew) {
  const last = r[r.length - 1];
  if (vowelFiles[last]) vowelFiles[last].push(r);
}

// ---------- 5. kvazaux 例外表 ----------
const hasEnding = (a, s) => {
  const m2 = endingMap[a] || {};
  return Object.keys(m2).some(e => e !== '(sen /)' && e.startsWith(s));
};
const kvFina = { as: [], is: [], os: [], u: [], us: [] };
for (const s of Object.keys(kvFina)) {
  for (const a of radikoNew) {
    if (a.length > s.length && a.endsWith(s) && !hasEnding(a, s)) kvFina[s].push(a);
  }
  kvFina[s].push(s);                       // 保留裸后缀本身
  kvFina[s] = [...new Set(kvFina[s])].sort();
}
const kvKomenca = { as: [], is: [], os: [], u: [] };
for (const p of Object.keys(kvKomenca)) {
  for (const a of radikoNew) {
    if (a.length > p.length && a.startsWith(p) && !hasEnding(a, p)) kvKomenca[p].push(a);
  }
  kvKomenca[p] = [...new Set(kvKomenca[p])].sort();
}

// ---------- 报告 ----------
console.log('=== radiko.txt ===');
console.log(`  原有 ${radikoOld.length}  ->  新 ${radikoNew.length}  (+${radikoNew.length - radikoOld.length})`);
console.log(`  PIV 独有新增: ${pivOnly.length}`);
console.log(`  剔除(PIV 中不存在，判定为损坏条目): ${dropped.length}`);
console.log(`    ${dropped.join(', ')}`);
// 分类被剔除的原有条目
const classified = JSON.parse(fs.readFileSync(path.join(tmp, 'piv_classified.json'), 'utf8'));
const droppedProper = dropped.filter(r => classified[r] && classified[r].lower === false);
const droppedSingle = dropped.filter(r => r.length === 1);
const droppedOther = dropped.filter(r => !droppedProper.includes(r) && !droppedSingle.includes(r));
console.log(`  剔除明细: 专名/元素符号 ${droppedProper.length} 条, 单字符 ${droppedSingle.length} 条, 其余(PIV 无) ${droppedOther.length} 条`);
console.log(`    专名样例: ${droppedProper.slice(0, 20).join(', ')}`);
console.log(`    其余: ${droppedOther.join(', ')}`);

console.log('\n=== 派生词形中出现的后缀 (PIV derivajho) ===');
const sufList = [...derivSuffix.entries()].sort((a, b) => b[1] - a[1]);
const dictNow = new Set(radikoNew);
console.log('  出现次数最多的 30 个后缀，以及其是否已在词典中:');
for (const [s, n] of sufList.slice(0, 30)) {
  const inDict = dictNow.has(s);
  const inSuf = s.length <= 3;
  console.log(`    ${s.padEnd(8)} x${String(n).padStart(5)}   词典中:${inDict ? '有' : '无'}`);
}

console.log('\n=== 词性结尾 ===');
for (const [e, n] of [...wordEndings.entries()].sort((a, b) => b[1] - a[1])) {
  console.log(`    ${e.padEnd(6)} ${n}`);
}

console.log('\n=== vokalo-fina-radiko 重建 ===');
for (const v of ['a', 'e', 'i', 'o', 'u']) {
  const oldN = rd(path.join(repo, 'vortaro', 'vokalo-fina-radiko', `${v}_fina_radiko.txt`)).length;
  console.log(`    ${v}_fina: ${oldN} -> ${vowelFiles[v].length}`);
}

console.log('\n=== kvazaux 例外表重建 ===');
for (const s of ['as', 'is', 'os', 'u', 'us']) {
  const oldN = rd(path.join(repo, 'vortaro', 'kvazaux-finitiva-radiko', `${s}-fina-radiko.txt`)).length;
  console.log(`    ${s}-fina: ${oldN} -> ${kvFina[s].length}`);
}
for (const p of ['as', 'is', 'os', 'u']) {
  const oldN = rd(path.join(repo, 'vortaro', 'kvazaux-post-finitiva-radiko', `${p}-komenca-radiko.txt`)).length;
  console.log(`    ${p}-komenca: ${oldN} -> ${kvKomenca[p].length}`);
}

console.log('\n=== 关键日常词根覆盖 ===');
const dict = dictNow;
for (const w of ['dom', 'famili', 'person', 'infan', 'urb', 'lerne', 'oplak', 'labor', 'komerc',
  'scienc', 'mesaĝ', 'manĝ', 'rem', 'vektor', 'lini', 'libr', 'skrib', 'parol', 'ir', 'ven',
  'don', 'komputil', 'lern', 'kred', 'esperant', 'mem', 'manĝi', 'pensi', 'paroli', 'lerni']) {
  console.log(`    ${w.padEnd(10)} ${dict.has(w) ? '有' : '*** 缺 ***'}`);
}

// ---------- 写盘 ----------
if (!write) { console.log('\n(仅报告，未写盘；加 --write 落盘)'); process.exit(0); }

const w = (p, arr) => fs.writeFileSync(p, arr.join('\n') + '\n', 'utf8');
w(path.join(repo, 'vortaro', 'radiko.txt'), radikoNew);
for (const v of ['a', 'e', 'i', 'o', 'u']) {
  w(path.join(repo, 'vortaro', 'vokalo-fina-radiko', `${v}_fina_radiko.txt`), vowelFiles[v]);
}
for (const s of ['as', 'is', 'os', 'u', 'us']) {
  w(path.join(repo, 'vortaro', 'kvazaux-finitiva-radiko', `${s}-fina-radiko.txt`), kvFina[s]);
}
for (const p of ['as', 'is', 'os', 'u']) {
  w(path.join(repo, 'vortaro', 'kvazaux-post-finitiva-radiko', `${p}-komenca-radiko.txt`), kvKomenca[p]);
}
// 附：PIV 标注为"基本词"(★) 的根词子集，供 Phase 2 择优打分参考
w(path.join(repo, 'vortaro', 'fundamenta-radiko.txt'), [...pivFund].sort());
console.log('\n已写盘。');
