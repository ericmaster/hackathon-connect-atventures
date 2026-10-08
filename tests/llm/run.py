#!/usr/bin/env python3
"""Benchmark A2UI: corre cada fixture N veces por modelo y puntúa automáticamente.

Uso:
  python3 tests/llm/run.py                                   # modelos disponibles, 2 corridas, T=0
  python3 tests/llm/run.py --models haiku-4.5 --runs 3 --temperature 0.2
  python3 tests/llm/run.py --models haiku-4.5-so             # structured outputs nativo
  python3 tests/llm/run.py --summary tests/llm/results/bench-*.jsonl   # tabla compacta
  python3 tests/llm/run.py --report tests/llm/results/<archivo>.jsonl   # solo reimprime la tabla

Respeta el límite de Bedrock (>= 1,1 s entre llamadas, backoff exponencial ante throttling).
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import checks  # noqa: E402

MODELS = {k: v for k, v in json.loads((HERE / "models.json").read_text()).items() if not k.startswith("_")}
DEFAULT_MODELS = [k for k, v in MODELS.items() if v.get("available", True) and not v.get("structured")]


def load_fixtures(pattern="*.json"):
    return [json.loads(p.read_text()) for p in sorted((HERE / "fixtures").glob(pattern))]


PROMPT_FILE = HERE / "system_prompt.md"


def system_prompt():
    return PROMPT_FILE.read_text()


def user_message(fx):
    return "CONTEXTO DEL TURNO:\n" + json.dumps(fx["context"], ensure_ascii=False, indent=1) + \
        "\n\nResponde solo con el JSONL A2UI."


def call_model(brt, mk, fx, temperature=0.0, max_tokens=3000):
    """Una llamada para un fixture, con los ajustes del modelo (structured, sin temperature…)."""
    import bedrock
    import structured
    m = MODELS[mk]
    so = m.get("structured")
    res = bedrock.converse_stream(brt, m["model_id"], system_prompt(),
                                  user_message(fx) + (structured.USER_SUFFIX if so else ""),
                                  temperature=None if m.get("no_temperature") else temperature,
                                  max_tokens=max_tokens, system_in_user=m.get("system_in_user", False),
                                  extra=m.get("extra"), output_config=structured.OUTPUT_CONFIG if so else None)
    if so and res["ok"]:
        res["raw_text"], res["text"] = res["text"], structured.to_jsonl(res["text"])
    return res


def run(model_keys, runs, temperature, max_tokens, pattern, out):
    import bedrock
    brt = bedrock.client()
    fixtures = load_fixtures(pattern)
    total = len(model_keys) * len(fixtures) * runs
    n = 0
    with out.open("a") as f:
        for mk in model_keys:
            m = MODELS[mk]
            for fx in fixtures:
                for r in range(runs):
                    n += 1
                    res = call_model(brt, mk, fx, temperature, max_tokens)
                    sc = checks.score(res.get("text", ""), fx) if res["ok"] else None
                    rec = {"model": mk, "model_id": m["model_id"], "case": fx["id"], "run": r, "prompt": PROMPT_FILE.name,
                           "temperature": temperature, **{k: v for k, v in res.items()},
                           "scores": sc, "all_pass": bool(sc and checks.all_pass(sc))}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    fails = [k for k in checks.CHECKS if sc and sc[k]["ok"] is False] if sc else ["CALL:" + str(res.get("error"))[:80]]
                    print(f"[{n}/{total}] {mk:13s} {fx['id']:28s} r{r} "
                          f"{res.get('latency_s') or 0:5.1f}s out={res.get('output_tokens')} "
                          f"{'PASS' if rec['all_pass'] else 'FAIL ' + ','.join(fails)}", flush=True)


def rescore(path):
    """Re-aplica checks.py a las respuestas guardadas (sin llamar a Bedrock)."""
    fx = {f["id"]: f for f in load_fixtures()}
    recs = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    for r in recs:
        if r["ok"]:
            r["scores"] = checks.score(r["text"], fx[r["case"]])
            r["all_pass"] = checks.all_pass(r["scores"])
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))


def _avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def report(path):
    recs = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    lines = []
    for mk in dict.fromkeys(r["model"] for r in recs):
        rs = [r for r in recs if r["model"] == mk]
        m = MODELS.get(mk, {})
        temps = sorted({r["temperature"] for r in rs})
        lines.append(f"\n### {m.get('label', mk)} (`{rs[0]['model_id']}`, T={','.join(map(str, temps))}, n={len(rs)})\n")
        lines.append("| check | pass |\n|---|---|")
        for c in checks.CHECKS + ["ALL"]:
            vals = []
            for r in rs:
                if not r["ok"]:
                    vals.append(False)
                elif c == "ALL":
                    vals.append(r["all_pass"])
                elif r["scores"][c]["ok"] is not None:
                    vals.append(r["scores"][c]["ok"])
            if vals:
                lines.append(f"| {c} | {sum(vals)}/{len(vals)} ({100 * sum(vals) / len(vals):.0f}%) |")
        ok = [r for r in rs if r["ok"]]
        if not ok:
            lines.append(f"\nsin respuestas válidas: {rs[0].get('error', '')[:200]}")
            continue
        # Nova a veces no manda usage en el stream (0/0): fuera de los promedios de tokens/costo.
        tok = [r for r in ok if r.get("output_tokens")]
        cost = _avg([(r["input_tokens"] or 0) * m.get("price_in", 0) / 1e6 +
                     (r["output_tokens"] or 0) * m.get("price_out", 0) / 1e6 for r in tok])
        fenced = sum(1 for r in ok if r["scores"]["_parse"]["fenced"])
        strict = sum(1 for r in ok if r["scores"]["_parse"]["strict_jsonl"])
        lat = _avg([r["latency_s"] for r in ok])
        ttft = _avg([r["ttft_s"] for r in ok])
        lines.append(
            f"\nlatencia prom {lat:.2f} s · TTFT prom {ttft:.2f} s · máx {max(r['latency_s'] for r in ok):.2f} s · "
            f"in prom {_avg([r['input_tokens'] for r in tok]):.0f} · out prom {_avg([r['output_tokens'] for r in tok]):.0f} tok · "
            f"≈ ${cost:.5f}/llamada · JSONL estricto {strict}/{len(ok)} · con ``` {fenced}/{len(ok)} · "
            f"reintentos {sum(r.get('retries', 0) for r in rs)} · errores {len(rs) - len(ok)}")
        fails = [(r["case"], r["run"], k, r["scores"][k]["detail"]) for r in ok for k in checks.CHECKS
                 if r["scores"][k]["ok"] is False and r["scores"][k]["detail"] != "sin JSON"]
        if fails:
            lines.append("\nFallos:")
            lines += [f"- {c} r{n} **{k}**: {d[:160]}" for c, n, k, d in fails]
    txt = "\n".join(lines)
    print(txt)
    return txt


def summary(paths):
    """Tabla compacta: una fila por (archivo, modelo). % de pase por chequeo + latencia/tokens/costo."""
    hdr = ["corrida", "modelo", "n"] + checks.CHECKS + ["ALL", "lat s", "TTFT s", "out tok", "USD/llamada"]
    rows = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for path in paths:
        recs = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
        for mk in dict.fromkeys(r["model"] for r in recs):
            rs = [r for r in recs if r["model"] == mk and r["ok"]]
            if not rs:
                continue
            m = MODELS.get(mk, {})
            cells = [Path(path).stem.replace("bench-", ""), mk, str(len(rs))]
            for c in checks.CHECKS + ["ALL"]:
                v = [r["all_pass"] if c == "ALL" else r["scores"][c]["ok"] for r in rs]
                v = [x for x in v if x is not None]
                cells.append(f"{100 * sum(v) / len(v):.0f}%" if v else "—")
            tok = [r for r in rs if r.get("output_tokens")]
            cost = _avg([r["input_tokens"] * m.get("price_in", 0) / 1e6 + r["output_tokens"] * m.get("price_out", 0) / 1e6 for r in tok])
            cells += [f"{_avg([r['latency_s'] for r in rs]):.1f}", f"{_avg([r['ttft_s'] for r in rs]):.2f}",
                      f"{_avg([r['output_tokens'] for r in tok]):.0f}", f"{cost:.5f}"]
            rows.append("| " + " | ".join(cells) + " |")
    txt = "\n".join(rows)
    print(txt)
    return txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=DEFAULT_MODELS,
                    help=f"claves de models.json (por defecto {DEFAULT_MODELS})")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=3000)
    ap.add_argument("--cases", default="*.json", help="glob dentro de fixtures/")
    ap.add_argument("--out", default=None)
    ap.add_argument("--prompt", default=None, help="system prompt alternativo (por defecto system_prompt.md)")
    ap.add_argument("--report", default=None)
    ap.add_argument("--summary", nargs="*", default=None, help="tabla compacta de uno o más .jsonl")
    ap.add_argument("--rescore", action="store_true", help="con --report: re-puntúa los textos guardados")
    a = ap.parse_args()
    if a.summary:
        summary(a.summary)
        return
    if a.report:
        if a.rescore:
            rescore(a.report)
        report(a.report)
        return
    global PROMPT_FILE
    if a.prompt:
        PROMPT_FILE = Path(a.prompt)
    out = Path(a.out) if a.out else HERE / "results" / f"{dt.datetime.now():%Y%m%d-%H%M%S}.jsonl"
    out.parent.mkdir(exist_ok=True)
    run(a.models, a.runs, a.temperature, a.max_tokens, a.cases, out)
    print(f"\nresultados: {out}")
    report(out)


if __name__ == "__main__":
    main()
