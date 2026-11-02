// 对比三种切分策略在歧义词上的表现
const fs = require('fs');
const path = require('path');
const repo = path.resolve(__dirname, '..');
const rd = (p) => fs.readFileSync(p, 'utf8').split(/\r?\n/).map(s => s.trim()).filter(Boolean);
const load = (f) => {
  const raw = fs.readFileSync(path.join(repo, 'vortaro', `${f}.txt`), 'utf8').trim();
  return raw.startsWith('{') ? raw.replace(/^\{|\}$/g, '').split(',').map(x => x.trim()) : rd(path.join(repo, 'vortaro', `${f}.txt`));
};
const radiko = rd(path.join(repo, 'vortaro', 'radiko.txt'));
const radikoSet = new Set(radiko);
const prefikso = load('prefikso');
const sufikso = load('sufikso');
const dict = new Set([...radiko, ...prefikso, ...sufikso, 'a', 'e', 'i', 'o', 'u']);

// 策略 A：现状（短前缀优先，枚举全解）
// 策略 B：长前缀优先（贪心）
// 策略 C：整词优先（若整段是词根则不切），再长前缀优先

function greedy(w, preferWhole) {
  const out = [];
  const rec = (rest) => {
    if (rest === '') return true;
    if (preferWhole && radikoSet.has(rest.toLowerCase()) && rest.length > 1) { out.push(rest); return true; }
    for (let i = rest.length; i >= 1; i--) {          // 长优先
      const p = rest.slice(0, i);
      if (dict.has(p.toLowerCase())) { out.push(p); if (rec(rest.slice(i))) return true; out.pop(); }
    }
    return false;
  };
  return rec(w) ? out : null;
}

console.log('=== 三种策略对比 ===\n');
const words = ['horloĝo', 'ekskurso', 'heroino', 'komputilo', 'lernanto', 'lernantoj',
  'esperanto', 'malsanuleja', 'instruistino', 'domo', 'ananaso', 'universitato',
  'scienco', 'lernejo', 'kredito', 'administranto', 'adopti', 'acerba'];

for (const w of words) {
  const b = greedy(w, false);
  const c = greedy(w, true);
  console.log(`  ${w.padEnd(15)} B长优先: ${(b || ['kontroloto']).join('+')}`);
  console.log(`  ${''.padEnd(15)} C整词优先: ${(c || ['kontroloto']).join('+')}`);
}

console.log('\n=== 统计：整词优先规则保护了多少词根 ===');
let protectedN = 0;
const examples = [];
for (const r of radiko) {
  if (r.length < 4) continue;
  // 该词根若被切，会切成什么？
  const b = greedy(r, false);
  if (b && b.length > 1) {
    protectedN++;
    if (examples.length < 25) examples.push(`${r} (会被切成 ${b.join('+')})`);
  }
}
console.log(`  radiko.txt 中长度>=4 且本身可被切开的词根: ${protectedN}`);
console.log('  样例:');
for (const e of examples) console.log(`    ${e}`);
