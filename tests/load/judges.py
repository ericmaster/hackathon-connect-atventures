#!/usr/bin/env python3
"""Load test: N concurrent "virtual judges" against the LIVE public path (Cognito guest + SigV4 → API Gateway → Lambda).

  python3 tests/load/judges.py -n 5            # 5 judges, think time 2–5 s, start spread 0–3 s
  python3 tests/load/judges.py -n 3 --spread 0 --think 2,5 --retry429 0

Each judge = own Cognito guest identity: /session → enviar_cedula → consentimiento → 1 free-text turn
(→ safety question template) → seguridad {ok:true} (= the LLM turn, Haiku) → agregar_pedido → retirar_aqui →
billing (consumidor final + email) → confirmación. Synthetic data only. Never prints credentials or signed URLs.
Then reads CloudWatch (read-only) for the orchestrator's per-request trace (llm ok/error/retries) and ThrottlingException.
Results JSON → tests/load/results/<ts>-n<N>.json
"""
import argparse, json, os, random, statistics, subprocess, sys, threading, time, urllib.error, urllib.request
import boto3
from botocore import UNSIGNED
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.config import Config
from botocore.credentials import Credentials

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tests", "e2e"))
import smoke  # noqa: E402  (reuse Client / A2UI helpers; transport replaced below)

URL = os.environ.get("FV_API_URL", "https://znpzz1wg21.execute-api.us-east-1.amazonaws.com")
POOL = os.environ.get("FV_POOL", "us-east-1:8434d4ed-e17e-4082-ad26-42b59e004e3e")
LOG_GROUP = "/aws/lambda/connect-atv-orchestrator"
TEXTS = ["algo para la gripe", "tengo tos", "vitaminas para mi mamá"]
FIXED = ["1710034065", "1712456787"]


def cedula_valida(rng):
    """Synthetic Ecuadorian cédula (provincia 17, 3er dígito < 6, módulo 10)."""
    d = [1, 7, rng.randint(0, 5)] + [rng.randint(0, 9) for _ in range(6)]
    s = 0
    for i, x in enumerate(d):
        v = x * (2 if i % 2 == 0 else 1)
        s += v - 9 if v > 9 else v
    return "".join(map(str, d)) + str((10 - s % 10) % 10)


class HttpInvoker:
    """Drop-in for smoke.Invoker: turns the smoke event into a SigV4-signed HTTPS call with its own guest identity."""
    def __init__(self, think, retry429, log, tts=False):
        ci = boto3.client("cognito-identity", region_name="us-east-1", config=Config(signature_version=UNSIGNED))
        iid = ci.get_id(IdentityPoolId=POOL)["IdentityId"]
        c = ci.get_credentials_for_identity(IdentityId=iid)["Credentials"]
        self.creds = Credentials(c["AccessKeyId"], c["SecretKey"], c["SessionToken"])
        self.think, self.retry429, self.log, self.n, self.tts = think, retry429, log, 0, tts

    def _post(self, path, data):
        r = AWSRequest(method="POST", url=URL + path, data=data, headers={"Content-Type": "application/json"})
        SigV4Auth(self.creds, "execute-api", "us-east-1").add_auth(r)
        t0 = time.perf_counter()
        try:
            resp = urllib.request.urlopen(urllib.request.Request(URL + path, data=data, method="POST", headers=dict(r.headers)), timeout=35)
            st, raw = resp.status, resp.read()
        except urllib.error.HTTPError as e:
            st, raw = e.code, e.read()
        except Exception as e:  # noqa: BLE001
            st, raw = 599, b""
        return st, raw, (time.perf_counter() - t0) * 1000

    def _speak(self, text):
        """Like the PWA: fire-and-forget POST /voice/tts with spokenText (adds API Gateway load)."""
        st, _, ms = self._post("/voice/tts", json.dumps({"text": text[:400]}).encode())
        self.log.append({"path": "/voice/tts", "status": st, "ms": round(ms), "attempt": 0, "t": time.time()})

    def __call__(self, ev):
        if self.n:  # human think time between steps
            time.sleep(random.uniform(*self.think))
        self.n += 1
        method, path = ev["requestContext"]["http"]["method"], ev["rawPath"]
        data = ev["body"].encode() if ev.get("body") else None
        for attempt in range(self.retry429 + 1):
            r = AWSRequest(method=method, url=URL + path, data=data, headers={"Content-Type": "application/json"})
            SigV4Auth(self.creds, "execute-api", "us-east-1").add_auth(r)
            t0 = time.perf_counter()
            try:
                resp = urllib.request.urlopen(urllib.request.Request(URL + path, data=data, method=method, headers=dict(r.headers)), timeout=35)
                st, raw = resp.status, resp.read()
            except urllib.error.HTTPError as e:
                st, raw = e.code, e.read()
            except Exception as e:  # noqa: BLE001  (client timeout / network)
                st, raw = 599, json.dumps({"error": {"code": type(e).__name__}}).encode()
            ms = (time.perf_counter() - t0) * 1000
            self.log.append({"path": path, "status": st, "ms": round(ms), "attempt": attempt, "t": time.time()})
            if st != 429 or attempt == self.retry429:
                break
            time.sleep(0.5 * 2 ** attempt + random.uniform(0, 0.3))
        try:
            body = json.loads(raw) if raw else {}
        except ValueError:
            body = {"raw": raw[:120].decode(errors="replace")}
        if self.tts and st == 200 and isinstance(body, dict) and body.get("spokenText"):
            threading.Thread(target=self._speak, args=(body["spokenText"],), daemon=True).start()
        return st, body, ms


def judge(i, cedula, text, args, out):
    rec = {"judge": i, "cedula": cedula[:4] + "…", "text": text, "steps": [], "http": [], "ok": False}
    out.append(rec)
    try:
        time.sleep(random.uniform(0, args.spread))
        inv = HttpInvoker(args.think, args.retry429, rec["http"], args.tts)
        c = smoke.Client(inv)
        c.onboard(cedula, True)
        st, b = c.turn(text)
        smoke.check(st == 200, f"/turn → {st} {smoke.err(b)}")
        llm_label = "turn"
        if '"seguridad"' in json.dumps(b.get("messages") or []):
            st, b = c.act("seguridad", {"ok": True}, label="seguridad(LLM)")
            llm_label = "seguridad(LLM)"
            smoke.check(st == 200, f"seguridad → {st} {smoke.err(b)}")
        rec["llm_mode"], rec["llm_label"] = b.get("mode"), llm_label
        prods = smoke.find(b, "ProductCard")
        smoke.check(prods, f"sin ProductCard (state={b.get('state')}, mode={b.get('mode')})")
        c.add(prods[0]["sku"])
        c.pick_pharmacy()
        conf, _ = c.billing(prefer_cf=True)
        smoke.check(smoke.has(conf, "ConfirmacionPedido"), "sin ConfirmacionPedido")
        rec["ok"] = True
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"{type(e).__name__}: {str(e)[:160]}"
    finally:
        rec["steps"] = [{"label": l, "status": s, "ms": m} for (l, s, m) in (c.calls if "c" in locals() else [])]


def pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs); k = (len(xs) - 1) * p / 100; f = int(k)
    return round(xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f))


def cloudwatch(t0, t1):
    """Read-only: orchestrator JSON trace lines + ThrottlingException count in [t0, t1]."""
    logs = boto3.client("logs", region_name="us-east-1")
    def events(pattern):
        out, kw = [], dict(logGroupName=LOG_GROUP, startTime=int(t0 * 1000), endTime=int(t1 * 1000) + 5000, filterPattern=pattern)
        while True:
            r = logs.filter_log_events(**kw)
            out += [e["message"] for e in r.get("events", [])]
            if not r.get("nextToken"):
                return out
            kw["nextToken"] = r["nextToken"]
    throttles = len(events('"ThrottlingException"'))
    llm = []
    for m in events('"llm"'):
        try:
            j = json.loads(m[m.index("{"):])
        except ValueError:
            continue
        if isinstance(j.get("llm"), dict) and j["llm"]:
            llm.append(j)
    return {"throttling_lines": throttles, "llm_calls": len(llm),
            "llm_failed": sum(1 for j in llm if not j["llm"].get("ok")),
            "llm_errors": sorted({str(j["llm"].get("error")) for j in llm if not j["llm"].get("ok")}),
            "llm_retries": sum(int(j["llm"].get("retries") or 0) for j in llm),
            "llm_validation_retry": sum(1 for j in llm if j["llm"].get("attempt") == 2),
            "lambda_ms_llm": [j.get("ms") for j in llm]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=3)
    ap.add_argument("--think", default="2,5")
    ap.add_argument("--spread", type=float, default=3.0, help="judges start uniformly within this many seconds")
    ap.add_argument("--retry429", type=int, default=0, help="client retries on HTTP 429 (0 = report raw)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--no-logs", action="store_true")
    ap.add_argument("--tts", action="store_true", help="also call /voice/tts after each response, like the PWA")
    args = ap.parse_args()
    args.think = tuple(float(x) for x in args.think.split(","))
    rng = random.Random()
    out, threads = [], []
    t0 = time.time()
    for i in range(args.n):
        ced = FIXED[i] if i < len(FIXED) else cedula_valida(rng)
        th = threading.Thread(target=judge, args=(i, ced, TEXTS[i % len(TEXTS)], args, out)); th.start(); threads.append(th)
    for th in threads:
        th.join()
    time.sleep(3 if args.tts else 0)  # let last fire-and-forget TTS calls land
    t1 = time.time()

    by = {}
    for r in out:
        for s in r["steps"]:
            by.setdefault(s["label"], []).append(s["ms"])
    llm_ms = [s["ms"] for r in out for s in r["steps"] if s["label"] == r.get("llm_label")]
    tmpl_ms = [s["ms"] for r in out for s in r["steps"] if s["label"] != r.get("llm_label")]
    http = [h for r in out for h in r["http"]]
    summ = {
        "n": args.n, "tag": args.tag, "start": time.strftime("%H:%M:%S", time.localtime(t0)), "wall_s": round(t1 - t0, 1),
        "completed": sum(r["ok"] for r in out),
        "llm_turn_ms": {"p50": pct(llm_ms, 50), "p95": pct(llm_ms, 95), "max": max(llm_ms) if llm_ms else None, "n": len(llm_ms)},
        "template_ms": {"p50": pct(tmpl_ms, 50), "p95": pct(tmpl_ms, 95), "max": max(tmpl_ms) if tmpl_ms else None, "n": len(tmpl_ms)},
        "llm_fallback_simulado": sum(1 for r in out if r.get("llm_mode") == "simulado"),
        "http_429": sum(h["status"] == 429 for h in http), "http_403": sum(h["status"] == 403 for h in http),
        "http_5xx": sum(h["status"] >= 500 for h in http), "http_4xx_other": sum(400 <= h["status"] < 500 and h["status"] not in (403, 429) for h in http),
        "requests": len(http),
        "tts": {"n": sum(h["path"] == "/voice/tts" for h in http), "non200": sum(h["path"] == "/voice/tts" and h["status"] != 200 for h in http),
                "p95": pct([h["ms"] for h in http if h["path"] == "/voice/tts"], 95)},
        "status_by_path": {f'{h["path"]} {h["status"]}': sum(1 for x in http if x["path"] == h["path"] and x["status"] == h["status"]) for h in http if h["status"] != 200},
        "per_step": {k: {"p50": pct(v, 50), "p95": pct(v, 95), "max": max(v), "n": len(v)} for k, v in by.items()},
        "errors": [f"j{r['judge']}: {r['error']}" for r in out if r.get("error")],
    }
    if not args.no_logs:
        time.sleep(8)  # CloudWatch ingestion lag
        try:
            summ["cloudwatch"] = cloudwatch(t0, time.time())
        except Exception as e:  # noqa: BLE001
            summ["cloudwatch"] = {"error": type(e).__name__}
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    fn = os.path.join(HERE, "results", time.strftime("%Y%m%d-%H%M%S") + f"-n{args.n}{('-' + args.tag) if args.tag else ''}.json")
    json.dump({"summary": summ, "judges": out}, open(fn, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))
    print("→", os.path.relpath(fn, ROOT))


if __name__ == "__main__":
    main()
