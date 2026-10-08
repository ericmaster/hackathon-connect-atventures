#!/usr/bin/env bash
# Keep-warm de GLiNER: invocaciones directas SERIALES (sin URL pública), sin reintentos, timeout 300 s.
# Uso: tests/e2e/warm_gliner.sh [n_invocaciones=1] [pausa_s=0]
# Registra cold/ms en tests/e2e/results/warm_gliner.log. NO programado (cron) a propósito.
set -euo pipefail
FN="${FV_GLINER_FN:-connect-atv-gliner}"
REGION="${AWS_REGION:-us-east-1}"
N="${1:-1}"; PAUSE="${2:-0}"
export AWS_MAX_ATTEMPTS=1 AWS_PAGER=""
DIR="$(cd "$(dirname "$0")" && pwd)/results"; mkdir -p "$DIR"; LOG="$DIR/warm_gliner.log"
PAYLOAD='{"text":"Necesito algo para la gripe, tengo fiebre y dolor de cabeza"}'
for i in $(seq 1 "$N"); do
  out="$(mktemp)"; t0=$(date +%s%3N)
  if aws lambda invoke --region "$REGION" --function-name "$FN" --cli-read-timeout 300 --cli-connect-timeout 10 \
       --cli-binary-format raw-in-base64-out --payload "$PAYLOAD" "$out" >/dev/null 2>"$out.err"; then
    t1=$(date +%s%3N); wall=$((t1 - t0))
    # cold/ms los reporta la función si existen; si no, inferimos cold por tiempo de pared (>10 s)
    read -r cold ms < <(python3 -c "
import json,sys
try:
  d=json.load(open('$out')); b=d.get('body',d); b=json.loads(b) if isinstance(b,str) else b
  r=(b.get('results') or [{}])[0]
  print(str(b.get('cold','?')).lower(), r.get('ms', b.get('ms','?')))
except Exception: print('?','?')")
    [ "$cold" = "?" ] && cold=$([ "$wall" -gt 10000 ] && echo "true(inferido)" || echo "false(inferido)")
    line="$(date '+%F %T %Z') fn=$FN i=$i ok cold=$cold fn_ms=$ms wall_ms=$wall"
  else
    t1=$(date +%s%3N); line="$(date '+%F %T %Z') fn=$FN i=$i ERROR wall_ms=$((t1 - t0)) $(tail -c 200 "$out.err" | tr '\n' ' ')"
  fi
  echo "$line" | tee -a "$LOG"; rm -f "$out" "$out.err"
  if [ "$i" -lt "$N" ]; then sleep "$PAUSE"; fi
done
