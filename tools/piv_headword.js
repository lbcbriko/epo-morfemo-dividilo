// 快速：只抽 data-alfa + kapvorto，判断指定词是否为 PIV 独立词条
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const want = new Set(process.argv.slice(3));

const re = /data-alfa="([^"]*)"[^>]*>\s*(?:<span[^>]*>★<\/span>)?\s*<strong class="kapvorto"[^>]*>([\s\S]*?)<\/strong>/g;
const found = new Map();
let m;
while ((m = re.exec(html)) !== null) {
  const alfa = m[1];
  if (!want.has(alfa)) continue;
  const plain = m[2].replace(/<[^>]+>/g, '').trim();
  if (!found.has(alfa)) found.set(alfa, []);
  found.get(alfa).push(plain);
}
for (const w of want) {
  console.log(`  ${w.padEnd(10)} ${found.has(w) ? 'PIV 词条: ' + found.get(w).join(' || ') : '—— 无独立词条'}`);
}
