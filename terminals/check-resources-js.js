const fs = require('fs');
const h = fs.readFileSync('/usr/share/nginx/html/resources.html','utf8');
const m = h.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.log('NO_SCRIPT'); process.exit(1); }
try {
  new Function(m[1]);
  console.log('JS_SYNTAX_OK', m[1].length);
} catch (e) {
  console.log('JS_SYNTAX_ERROR', e.message);
}
console.log('has_results_id', h.includes('id="results"'));
console.log('has_navList', h.includes('id="navList"'));
console.log('loadCatalog_calls', (m[1].match(/loadCatalog\(\)/g)||[]).length);
