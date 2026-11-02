// 找出 radiko.txt 中"alf﻿a 带词性尾"的异常条目（应从 alfa 改为 kapvorto 的斜杠前部分）
// 判据：kapvorto 含 <span class="s">/</span>，且其前半部分 ≠ data-alfa
const fs = require('fs');
const path = require('path');
const repo = path.resolve(__dirname, '..');
const html = fs.readFileSync(process.argv[2], 'utf8');

const artStart = /<div class="art([^>]*)>/g;
const marks = [];
let m;
while ((m = artStart.exec(html)) !== null) marks.push({ attrs: m[1], bodyStart: artStart.lastIndex });

const anomalies = [];
for (let i = 0; i < marks.length; i++) {
  const end = i + 1 < marks.length ? marks[i + 1].index : html.length;
  const body = html.slice(marks[i].bodyStart, end);
  const alfa = (marks[i].attrs.match(/data-alfa="([^"]*)"/) || [])[1] || '';
  if (!alfa) continue;
  const kv = body.match(/<strong class="kapvorto"[^>]*>([\s\S]*?)<\/strong>/);
  if (!kv) continue;
  const rawKv = kv[1];
  const hasSlash = /<span class="s">\s*\/\s*<\/span>/.test(rawKv);
  if (!hasSlash) continue;
  const plain = rawKv.replace(/<sup[\s\S]*?<\/sup>/g, '').replace(/<[^>]+>/g, '').trim();
  let root = plain.split('/')[0].trim();
  const bound = root.startsWith('-');
  root = root.replace(/^-/, '').trim();
  if (root && root.toLowerCase() !== alfa.toLowerCase()) {
    anomalies.push({ alfa, kv: plain, root, bound });
  }
}

console.log(`含斜杠且词根与 alfa 不一致的条目: ${anomalies.length}\n`);
console.log('=== 完整清单 ===');
for (const a of anomalies) {
  console.log(`  alfa="${a.alfa}"  kapvorto="${a.kv}"  真词根="${a.root}"${a.bound ? ' [黏着]' : ''}`);
}

// 与当前 radiko.txt 对照：这些 alfa 是否在其中
const radiko = new Set(
  fs.readFileSync(path.join(repo, 'vortaro', 'radiko.txt'), 'utf8')
    .split(/\r?\n/).map(s => s.trim()).filter(Boolean)
);
const affect = anomalies.filter(a => radiko.has(a.alfa));
console.log(`\n其中确实存在于当前 radiko.txt 的: ${affect.length}`);
for (const a of affect) console.log(`  ${a.alfa}  ->  应为 ${a.root}`);

fs.writeFileSync(path.join(repo, '.anomalies.json'), JSON.stringify(affect, null, 0), 'utf8');
console.log('\n已写出 .anomalies.json');
