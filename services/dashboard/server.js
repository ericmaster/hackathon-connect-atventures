// Master control dashboard. No deps. Reads progress.json per request.
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');

const HOST = process.env.HOST || '127.0.0.1';
const PORT = Number(process.env.PORT || 41830);
const DATA = path.join(__dirname, 'progress.json');
const INFRA_TTL = 60_000;
const W = { todo: 0, doing: 0.5, done: 1 };

function compute(p) {
  let total = 0;
  const criteria = (p.criteria || []).map(c => {
    const items = c.items || [];
    const prog = items.length ? items.reduce((a, i) => a + (W[i.s] || 0), 0) / items.length : 0;
    const nota = typeof c.nota === 'number' ? c.nota : null;
    const pts = nota == null ? 0 : (nota / 5) * c.weight;
    total += pts;
    return { ...c, nota, pts: Math.round(pts * 10) / 10, progress: Math.round(prog * 100) };
  });
  return { ...p, criteria, total: Math.round(total * 10) / 10 };
}

// --- infra checks (cached, single-flight; bedrock at most once per window) ---
let infra = null, infraAt = 0, infraP = null;
function aws(args) {
  const env = { ...process.env };
  for (const k of ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_PROFILE']) delete env[k];
  return new Promise(res => execFile('aws', [...args, '--output', 'json'], { env, timeout: 20_000 }, (err, out, errOut) => {
    if (err) return res({ ok: false, err: String(errOut || err.message).trim().split('\n').pop().slice(0, 160) });
    try { res({ ok: true, data: JSON.parse(out) }); } catch { res({ ok: false, err: 'respuesta inválida' }); }
  }));
}
async function checkInfra() {
  const r = { checked_at: new Date().toISOString() };
  const sts = await aws(['sts', 'get-caller-identity']);
  if (sts.ok) {
    const arn = sts.data.Arn || '';
    const m = arn.match(/:assumed-role\/([^/]+)/) || arn.match(/:role\/(.+)$/) || arn.match(/:user\/(.+)$/);
    r.aws = { ok: true, account: sts.data.Account, role: m ? m[1] : arn.split(':').pop() };
    const br = await aws(['bedrock', 'list-foundation-models', '--region', 'us-east-1']);
    r.bedrock = br.ok ? { ok: true, models: (br.data.modelSummaries || []).length } : { ok: false, err: br.err };
  } else {
    const nocreds = /credentials|could not be found|Unable to locate|ExpiredToken|InvalidClientTokenId/i.test(sts.err);
    r.aws = { ok: false, err: nocreds ? 'sin credenciales' : sts.err };
    r.bedrock = { ok: false, err: 'sin credenciales' };
  }
  return r;
}
function getInfra() {
  if (infra && Date.now() - infraAt < INFRA_TTL) return Promise.resolve(infra);
  if (!infraP) infraP = checkInfra().then(r => { infra = r; infraAt = Date.now(); infraP = null; return r; },
    e => { infraP = null; infraAt = Date.now(); return infra = { aws: { ok: false, err: String(e).slice(0, 160) } }; });
  return infra ? Promise.resolve(infra) : infraP; // serve stale while refreshing
}
getInfra();

const send = (res, code, type, body) => { res.writeHead(code, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };

http.createServer(async (req, res) => {
  const url = req.url.split('?')[0];
  try {
    if (url === '/api/state') {
      const p = compute(JSON.parse(fs.readFileSync(DATA, 'utf8')));
      p.infra = await getInfra();
      return send(res, 200, 'application/json; charset=utf-8', JSON.stringify(p));
    }
    if (url === '/' || url === '/index.html') return send(res, 200, 'text/html; charset=utf-8', fs.readFileSync(path.join(__dirname, 'index.html')));
    if (url === '/healthz') return send(res, 200, 'text/plain', 'ok');
    send(res, 404, 'text/plain', 'not found');
  } catch (e) {
    send(res, 500, 'application/json', JSON.stringify({ error: String(e.message || e).slice(0, 200) }));
  }
}).listen(PORT, HOST, () => console.log(`dashboard on http://${HOST}:${PORT}`));
