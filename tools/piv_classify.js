// PIV 词条精细分类 + 筛选策略评估
const fs = require('fs');
const path = require('path');
const repo = path.resolve(__dirname, '..');
const html = fs.readFileSync(process.argv[2], 'utf8');

const artStart = /<div class="art([^>]*)>/g;
const marks = [];
let m;
while ((m = artStart.exec(html)) !== null) marks.push({ attrs: m[1], bodyStart: artStart.lastIndex });

const info = new Map();   // alfa -> {cap, bound, slash, bang, n}
for (let i = 0; i < marks.length; i++) {
  const attrs = marks[i].attrs;
  const end = i + 1 < marks.length ? marks[i + 1].index : html.length;
  const body = html.slice(marks[i].bodyStart, end);
  const alfa = (attrs.match(/data-alfa="([^"]*)"/) || [])[1] || '';
  if (!alfa) continue;
  const kv = body.match(/<strong class="kapvorto"[^>]*>([\s\S]*?)<\/strong>/);
  const inner = kv ? kv[1] : '';
  const plain = inner.replace(/<[^>]+>/g, '').trim();
  const rec = {
    kap: plain,
    bound: /<span class="f">-<\/span>/.test(inner),
    slash: /<span class="s">\/<\/span>/.test(inner),
    bang: plain.endsWith('!'),
    cap: /^[A-ZĈĜĤĴŜŬ]/.test(plain),
  };
  const prev = info.get(alfa);
  if (!prev) info.set(alfa, rec);
  else {
    // 同词根多条（homono）：只有当"全部"词形都首字母大写时才算专名。
    // 例: "ar"（后缀）与 "Ar"（河）同形 -> ar 必须保留。
    prev.cap = prev.cap && rec.cap;
    prev.lower = prev.lower || !rec.cap;
    prev.bound = prev.bound || rec.bound;
    prev.slash = prev.slash || rec.slash;
    prev.bang = prev.bang && rec.bang;
  }
}
for (const [k, v] of info) if (v.lower === undefined) v.lower = !v.cap;

const all = [...info.keys()].filter(s => /^[a-zĉĝĥĵŝŭ]+$/.test(s)).sort();
console.log(`PIV 小写词根总数: ${all.length}`);

const one = all.filter(s => s.length === 1);
const capped = all.filter(s => info.get(s).cap && !info.get(s).lower);
const bang = all.filter(s => info.get(s).bang);
const bound = all.filter(s => info.get(s).bound);

console.log(`\n=== 分类统计 ===`);
console.log(`  单字符条目（字母表条目）: ${one.length}  -> ${one.join(' ')}`);
console.log(`  全部词形均大写（专名/元素/符号）: ${capped.length}  样例: ${capped.slice(0, 25).join(', ')}`);
console.log(`  感叹词（kapvorto 带 !）: ${bang.length}  样例: ${bang.slice(0, 25).join(', ')}`);
console.log(`  黏着语素（PIV 标 -X）: ${bound.length}  样例: ${bound.slice(0, 25).join(', ')}`);

console.log('\n=== 全部大写的 2 字符项（应被剔除）===');
console.log('  ' + capped.filter(s => s.length === 2).join(', '));
console.log('=== 全部大写但有同形小写词的项（应保留）===');
const rescued = all.filter(s => info.get(s).cap && info.get(s).lower);
console.log('  ' + rescued.join(', '));

// 候选筛选集
const keep = all.filter(s => s.length >= 2 && info.get(s).lower);
console.log(`\n=== 筛选后（排除单字符 + 纯专名）: ${keep.length} 条 ===`);

fs.writeFileSync(path.join(repo, '.piv-tmp', 'piv_classified.json'),
  JSON.stringify(Object.fromEntries(info), null, 0), 'utf8');
fs.writeFileSync(path.join(repo, '.piv-tmp', 'piv_keep.txt'), keep.join('\n') + '\n', 'utf8');
fs.writeFileSync(path.join(repo, '.piv-tmp', 'piv_dropped.txt'),
  all.filter(s => !keep.includes(s)).sort().join('\n') + '\n', 'utf8');
console.log('已写出 .piv-tmp/piv_classified.json / piv_keep.txt / piv_dropped.txt');
