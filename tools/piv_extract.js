// PIV (Plena Ilustrita Vortaro) -> vortaro/ 提取器
// 读取 PIV 的 HTML 导出，抽取词根与元数据，产出报告与候选词表。
// 用法: node tools/piv_extract.js <piv.html> <outdir>

const fs = require('fs');
const path = require('path');

const src = process.argv[2];
const outDir = process.argv[3] || '.';

const html = fs.readFileSync(src, 'utf8');

// Esperanto 字母（含变音符号）
const isWord = s => /^[a-zĉĝĥĵŝŭ]+$/.test(s);

// ---- 1. 词条文章: <div class="art" ... data-alfa="X" data-homo="..."> ... <strong class="kapvorto">ROOT<span class="s">/</span>ENDING</strong>
const articles = [];
const artRe = /<div class="art([^>]*)>([\s\S]*?)<\/div>\s*(?=<div class="art|$)/g;
// 上面的粗匹配对嵌套 div 不安全，改为按 data-alfa 逐条切块
const artStartRe = /<div class="art([^>]*)>/g;
const marks = [];
let m;
while ((m = artStartRe.exec(html)) !== null) {
  marks.push({ attrs: m[1], index: m.index, bodyStart: artStartRe.lastIndex });
}
for (let i = 0; i < marks.length; i++) {
  const end = i + 1 < marks.length ? marks[i + 1].index : html.length;
  const body = html.slice(marks[i].bodyStart, end);
  const attrs = marks[i].attrs;

  const alfa = (attrs.match(/data-alfa="([^"]*)"/) || [])[1] || '';
  const homo = (attrs.match(/data-homo="([^"]*)"/) || [])[1] || '';
  const cls = (attrs.match(/class="([^"]*)"/) || [])[1] || '';

  // kapvorto: 取 <strong class="kapvorto" ...>...</strong> 的文本
  const kv = body.match(/<strong class="kapvorto"[^>]*>([\s\S]*?)<\/strong>/);
  let headword = '', root = '', ending = '';
  if (kv) {
    headword = kv[1].replace(/<[^>]+>/g, '').trim();
    const parts = headword.split('/');
    if (parts.length === 2) { root = parts[0].trim(); ending = parts[1].trim(); }
    else { root = parts[0].trim(); ending = ''; }
  }
  articles.push({ alfa, homo, cls, headword, root, ending, body });
}

// ---- 2. 派生词中的词根: <span class="teksto" data-tildo="..." data-teksto="ROOT">
const teksto = new Set();
const tekRe = /data-teksto="([^"]*)"/g;
while ((m = tekRe.exec(html)) !== null) teksto.add(m[1]);

// ---- 3. 派生词形: <strong class="d" ...>ROOT<span...>ENDING</strong>
const derived = [];
const dRe = /<strong class="d"[^>]*>([\s\S]*?)<\/strong>/g;
while ((m = dRe.exec(html)) !== null) {
  const txt = m[1].replace(/<[^>]+>/g, '').trim();
  const t = (m[1].match(/data-teksto="([^"]*)"/) || [])[1] || '';
  derived.push({ form: txt, base: t });
}

// ---- 4. 标注: vokalo-fina / kvazaux 判定所需信息
//     "Fundamenta" ★ 标记出现在 art 内
const fundamental = new Set();
for (const a of articles) if (a.body.includes('Fundamenta') || a.cls.includes('F')) fundamental.add(a.alfa);

// ---- 5. 统计
const alfaList = articles.map(a => a.alfa);
const uniqueAlfa = new Set(alfaList);
const phraseAlfa = [...uniqueAlfa].filter(s => /\s/.test(s));
const cleanAlfa = [...uniqueAlfa].filter(s => isWord(s));
const nonWordAlfa = [...uniqueAlfa].filter(s => s && !/\s/.test(s) && !isWord(s));

const uniqueTeksto = [...teksto].filter(s => isWord(s));
const uniqueDerived = new Set(derived.map(d => d.form));

const endings = {};
for (const a of articles) {
  const e = a.ending || '(sen /)';
  endings[e] = (endings[e] || 0) + 1;
}

const report = {
  source: path.basename(src),
  articles: articles.length,
  uniqueAlfa: uniqueAlfa.size,
  phraseAlfa: phraseAlfa.length,
  cleanAlfa: cleanAlfa.length,
  nonWordAlfa: nonWordAlfa.length,
  nonWordAlfaSample: nonWordAlfa.slice(0, 25),
  phraseAlfaSample: phraseAlfa.slice(0, 25),
  tekstoUnique: uniqueTeksto.length,
  derivedForms: uniqueDerived.size,
  fundamental: fundamental.size,
  endings,
};

console.log(JSON.stringify(report, null, 2));

// 输出中间产物
fs.mkdirSync(outDir, { recursive: true });
const w = (name, arr) => fs.writeFileSync(path.join(outDir, name),
  arr.slice().sort().join('\n') + '\n', 'utf8');
w('piv_alfa_all.txt', [...uniqueAlfa]);
w('piv_alfa_clean.txt', cleanAlfa);
w('piv_teksto.txt', uniqueTeksto);
w('piv_fundamenta.txt', [...fundamental]);
w('piv_phrases.txt', phraseAlfa);
w('piv_derived_forms.txt', [...uniqueDerived]);

// 词条 + 词性 映射: alfa -> ending 频次
const endingMap = {};
for (const a of articles) {
  if (!a.alfa) continue;
  const e = a.ending || '(sen /)';
  endingMap[a.alfa] = endingMap[a.alfa] || {};
  endingMap[a.alfa][e] = (endingMap[a.alfa][e] || 0) + 1;
}
fs.writeFileSync(path.join(outDir, 'piv_alfa_endings.json'),
  JSON.stringify(endingMap, null, 0), 'utf8');
