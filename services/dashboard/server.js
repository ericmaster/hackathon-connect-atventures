// Master control dashboard. No deps. Reads progress.json per request.
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');

const HOST = process.env.HOST || '127.0.0.1';
const PORT = Number(process.env.PORT || 41830);
const DATA = path.join(__dirname, 'progress.json');
const CANVAS_MAX = 64 * 1024; // per editable doc (canvas.json, value-prop.json)
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

// --- editable docs (lean canvas, value prop): GET full doc, PUT {<coll>:{key:{...}}} merges given entries ---
const bogotaNow = () => new Date(Date.now() - 5 * 36e5).toISOString().slice(0, 19) + '-05:00';
const httpErr = (status, msg) => Object.assign(new Error(msg), { status });
function readBody(req, max) {
  return new Promise((resolve, reject) => {
    if (Number(req.headers['content-length'] || 0) > max) return reject(httpErr(413, 'payload demasiado grande'));
    let n = 0, chunks = [], over = false;
    req.on('data', d => { n += d.length; if (n > max) over = true; else if (!over) chunks.push(d); });
    req.on('end', () => over ? reject(httpErr(413, 'payload demasiado grande')) : resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}
function validBlock(b) {
  return b && typeof b === 'object' && typeof b.title === 'string' && b.title.length <= 80 &&
    Array.isArray(b.items) && b.items.length <= 40 && b.items.every(i => typeof i === 'string' && i.length <= 500) &&
    (b.status === 'base' || b.status === 'borrador');
}
const optStr = (v, n) => v === undefined || (typeof v === 'string' && v.length <= n);
function validVersion(v) {
  return v && typeof v === 'object' && typeof v.name === 'string' && v.name.length <= 80 && optStr(v.template, 300) &&
    typeof v.text === 'string' && v.text.length <= 2000 && ['cliente', 'Farmaenlace', 'jurado'].includes(v.audience) &&
    (v.status === 'base' || v.status === 'borrador') && optStr(v.note, 300) &&
    (v.checks === undefined || (v.checks && typeof v.checks === 'object' && Object.keys(v.checks).length <= 20 &&
      Object.entries(v.checks).every(([k, c]) => /^[a-z0-9_]{1,32}$/.test(k) && (c === 'todo' || c === 'ok'))));
}
const DOCS = {
  '/api/canvas': { file: path.join(__dirname, 'canvas.json'), coll: 'blocks', valid: validBlock,
    pick: ({ title, items, status }) => ({ title, status, items }) },
  '/api/value-prop': { file: path.join(__dirname, 'value-prop.json'), coll: 'versions', valid: validVersion,
    pick: ({ name, template, text, audience, status, checks, note }) => ({ name, template, text, audience, status, checks, note }) },
};
function putAuth(req) { // CF Access identity, or direct localhost (not proxied through Cloudflare/tunnel)
  const email = String(req.headers['cf-access-authenticated-user-email'] || '').trim().slice(0, 200);
  if (email) return email;
  const local = ['127.0.0.1', '::1', '::ffff:127.0.0.1'].includes(req.socket.remoteAddress);
  if (local && !req.headers['cf-ray'] && !req.headers['cf-connecting-ip']) return 'localhost';
  return null;
}
async function putDoc(req, d) {
  const by = putAuth(req);
  if (!by) throw httpErr(403, 'no autorizado');
  let body;
  try { body = JSON.parse(await readBody(req, CANVAS_MAX)); } catch (e) { throw e.status ? e : httpErr(400, 'JSON inválido'); }
  const C = d.coll, src = body && body[C];
  const keys = src && typeof src === 'object' && !Array.isArray(src) ? Object.keys(src) : [];
  if (!keys.length || keys.length > 30) throw httpErr(400, `se espera {${C}:{...}}`);
  for (const k of keys) if (!/^[a-z0-9_]{1,32}$/.test(k) || !d.valid(src[k])) throw httpErr(400, `entrada inválida: ${k.slice(0, 32)}`);
  let cur = { [C]: {} };
  try { cur = JSON.parse(fs.readFileSync(d.file, 'utf8')); } catch {}
  if (!cur[C] || typeof cur[C] !== 'object') cur[C] = {};
  for (const k of keys) cur[C][k] = d.pick(src[k]);
  if (Object.keys(cur[C]).length > 30) throw httpErr(400, 'demasiadas entradas');
  cur.updated_at = bogotaNow(); cur.updated_by = by;
  const out = JSON.stringify(cur, null, 2) + '\n';
  if (Buffer.byteLength(out) > CANVAS_MAX * 2) throw httpErr(413, 'documento demasiado grande');
  const tmp = `${d.file}.tmp-${process.pid}-${Date.now()}`;
  fs.writeFileSync(tmp, out); fs.renameSync(tmp, d.file);
  return out;
}

const send = (res, code, type, body) => { res.writeHead(code, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body); };

http.createServer(async (req, res) => {
  const url = req.url.split('?')[0];
  try {
    if (url === '/api/state') {
      const p = compute(JSON.parse(fs.readFileSync(DATA, 'utf8')));
      p.infra = await getInfra();
      return send(res, 200, 'application/json; charset=utf-8', JSON.stringify(p));
    }
    const doc = DOCS[url];
    if (doc) {
      if (req.method === 'GET') return send(res, 200, 'application/json; charset=utf-8', fs.readFileSync(doc.file, 'utf8'));
      if (req.method === 'PUT') return send(res, 200, 'application/json; charset=utf-8', await putDoc(req, doc));
      return send(res, 405, 'text/plain', 'method not allowed');
    }
    if (url === '/' || url === '/index.html') return send(res, 200, 'text/html; charset=utf-8', fs.readFileSync(path.join(__dirname, 'index.html')));
    if (url === '/healthz') return send(res, 200, 'text/plain', 'ok');
    send(res, 404, 'text/plain', 'not found');
  } catch (e) {
    send(res, e.status || 500, 'application/json', JSON.stringify({ error: String(e.message || e).slice(0, 200) }));
  }
}).listen(PORT, HOST, () => console.log(`dashboard on http://${HOST}:${PORT}`));
