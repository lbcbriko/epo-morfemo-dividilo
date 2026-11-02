// 合并后校验：一致性 + 切分覆盖率实测（复刻 radiko.py 语义）
const fs = require('fs');
const path = require('path');
const repo = path.resolve(__dirname, '..');
const rd = (p) => fs.readFileSync(p, 'utf8').split(/\r?\n/).map(s => s.trim()).filter(Boolean);
const rdSet = (p) => new Set(rd(p));

const radiko = rdSet(path.join(repo, 'vortaro', 'radiko.txt'));
const prefikso = rdSet(path.join(repo, 'vortaro', 'prefikso.txt'));
const sufikso = rdSet(path.join(repo, 'vortaro', 'sufikso.txt'));
const tabelvorto = rdSet(path.join(repo, 'vortaro', 'tabelvorto.txt'));
const vorteto = rdSet(path.join(repo, 'vortaro', 'vorteto.txt'));

console.log('=== 一致性校验 ===');
const vowelFiles = {};
for (const v of ['a', 'e', 'i', 'o', 'u']) {
  vowelFiles[v] = rdSet(path.join(repo, 'vortaro', 'vokalo-fina-radiko', `${v}_fina_radiko.txt`));
}
const vowelAnn = new Set([...vowelFiles.a, ...vowelFiles.e, ...vowelFiles.i, ...vowelFiles.o, ...vowelFiles.u]);
const vowelInRad = [...radiko].filter(r => /[aeiou]$/.test(r));
const unannotated = vowelInRad.filter(r => !vowelAnn.has(r));
const annotatedNotInRad = [...vowelAnn].filter(r => !radiko.has(r));
console.log(`  radiko.txt 元音结尾根词: ${vowelInRad.length}`);
console.log(`  vokalo-fina-radiko 标注: ${vowelAnn.size}`);
console.log(`  未标注的元音结尾根词: ${unannotated.length} ${unannotated.length ? '<-- 不一致' : '(通过)'}`);
console.log(`  标注了但不在 radiko.txt 的: ${annotatedNotInRad.length} ${annotatedNotInRad.length ? '<-- 不一致' : '(通过)'}`);
for (const v of ['a', 'e', 'i', 'o', 'u']) {
  const bad = [...vowelFiles[v]].filter(x => !x.endsWith(v));
  const inRad = [...vowelFiles[v]].filter(x => radiko.has(x)).length;
  console.log(`    ${v}_fina: ${vowelFiles[v].size} 条, 不以 ${v} 结尾: ${bad.length}, 在 radiko.txt 中: ${inRad}`);
}
const dupInRad = rd(path.join(repo, 'vortaro', 'radiko.txt'));
console.log(`  radiko.txt 重复条目: ${dupInRad.length - radiko.size}`);
for (const [name, set] of [['prefikso', prefikso], ['sufikso', sufikso]]) {
  const list = rd(path.join(repo, 'vortaro', `${name}.txt`));
  console.log(`  ${name}.txt 重复条目: ${list.length - set.size}`);
}

// kvazaux 例外表一致性
console.log('\n=== kvazaux 例外表一致性 ===');
for (const s of ['as', 'is', 'os', 'u', 'us']) {
  const set = rdSet(path.join(repo, 'vortaro', 'kvazaux-finitiva-radiko', `${s}-fina-radiko.txt`));
  const notInRad = [...set].filter(x => !radiko.has(x) && x !== s);
  console.log(`  ${s}-fina: ${set.size} 条, 不在 radiko.txt 中: ${notInRad.length}`);
}
for (const p of ['as', 'is', 'os', 'u']) {
  const set = rdSet(path.join(repo, 'vortaro', 'kvazaux-post-finitiva-radiko', `${p}-komenca-radiko.txt`));
  const notInRad = [...set].filter(x => !radiko.has(x));
  console.log(`  ${p}-komenca: ${set.size} 条, 不在 radiko.txt 中: ${notInRad.length}`);
}

// ---- 切分模拟 ----
const dict = new Set([...radiko, ...prefikso, ...sufikso, ...tabelvorto, ...vorteto,
  'a', 'e', 'i', 'o', 'u']);
const cache = new Map();
function splits(w) {
  if (w === '') return [];
  if (cache.has(w)) return cache.get(w);
  const res = [];
  for (let i = 1; i <= w.length; i++) {
    const p = w.slice(0, i), rest = w.slice(i);
    if (dict.has(p.toLowerCase())) {
      if (rest === '') res.push([p]);
      else for (const t of splits(rest)) res.push([p, ...t]);
    }
  }
  cache.set(w, res);
  return res;
}
const show = (w) => {
  const r = splits(w);
  if (!r.length) return 'kontroloto';
  return r.slice(0, 2).map(s => s.join('+')).join('  |  ') + (r.length > 2 ? `  [${r.length} 种解]` : '');
};

console.log('\n=== 切分实测（合并后词典）===');
const cases = ['domo', 'domoj', 'komputilo', 'venkas', 'lernanto', 'lernantoj', 'kredito',
  'esperanto', 'familio', 'persono', 'infano', 'urbo', 'scienco', 'libro', 'skribi',
  'paroli', 'veni', 'laboro', 'malsanuleja', 'instruistino', 'alfabetumo', 'universitato',
  'lernejo', 'oplako', 'mesaĝo', 'manĝo', 'vektoro', 'linio', 'negativa', 'uazo', 'ananaso'];
for (const c of cases) console.log(`  ${c.padEnd(16)} -> ${show(c)}`);

console.log('\n=== 旧词典对照（基线取自 git HEAD）===');
const { execSync } = require('child_process');
let oldRad = new Set();
try {
  const base = execSync('git show HEAD:vortaro/radiko.txt', { cwd: repo, encoding: 'utf8' });
  oldRad = new Set(base.split(/\r?\n/).map(s => s.trim()).filter(Boolean));
} catch (e) {
  console.log('  (无法从 git 取基线，跳过对照)');
}
const oldDict = new Set([...oldRad, ...prefikso, ...sufikso, ...tabelvorto, ...vorteto,
  'a', 'e', 'i', 'o', 'u']);
const oldCache = new Map();
function oldSplits(w) {
  if (w === '') return [];
  if (oldCache.has(w)) return oldCache.get(w);
  const res = [];
  for (let i = 1; i <= w.length; i++) {
    const p = w.slice(0, i), rest = w.slice(i);
    if (oldDict.has(p.toLowerCase())) {
      if (rest === '') res.push([p]);
      else for (const t of oldSplits(rest)) res.push([p, ...t]);
    }
  }
  oldCache.set(w, res);
  return res;
}
let oldOk = 0, newOk = 0;
for (const c of cases) {
  const o = oldSplits(c).length > 0, n = splits(c).length > 0;
  if (o) oldOk++; if (n) newOk++;
  console.log(`  ${c.padEnd(16)} 旧:${o ? '可切' : 'kontroloto'}  新:${n ? '可切' : 'kontroloto'}`);
}
console.log(`\n  覆盖: 旧 ${oldOk}/${cases.length}  ->  新 ${newOk}/${cases.length}`);
