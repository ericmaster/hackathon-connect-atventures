"""Lambda `connect-atv-orchestrator`: API Gateway HTTP API (payload v2, IAM auth) + invocación directa.

Directa: {"route": "POST /turn", "body": {...}, "identityId": "opcional"} → devuelve el body (dict) + "_status".
"""
import base64
import json
import time
import traceback

import fsm
import mock
import templates as T

ADMIN_SERVICES = {"crm", "catalogo", "inventario", "farmacias", "smartclub", "pedidos", "facturacion"}


def _caller(event):
    rc = event.get("requestContext") or {}
    iam = (rc.get("authorizer") or {}).get("iam") or {}
    ident = (iam.get("cognitoIdentity") or {}).get("identityId")
    if ident:
        return ident
    if iam.get("userArn"):
        return iam["userArn"]
    if "requestContext" in event:
        return "anonymous"
    return event.get("identityId") or "direct"


def _parse(event):
    if "requestContext" in event and ("rawPath" in event or "routeKey" in event):
        method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
        path = event.get("rawPath") or "/"
        stage = event.get("requestContext", {}).get("stage")
        if stage and stage != "$default" and path.startswith("/" + stage + "/"):
            path = path[len(stage) + 1:]
        raw = event.get("body") or ""
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw).decode()
        body = json.loads(raw) if raw else {}
        return method.upper(), path.rstrip("/") or "/", body, True
    route = event.get("route") or "POST /turn"
    method, path = route.split(" ", 1)
    return method.upper(), path.rstrip("/"), event.get("body") or {}, False


def _voice(fn, body):
    try:
        import voice  # workstream C
    except ImportError:
        return 501, {"error": {"code": "not_implemented", "message": "voice.py no disponible"}}
    try:
        return 200, getattr(voice, fn)(body)
    except ValueError as e:
        return 400, {"error": {"code": "bad_request", "message": str(e)[:200]}}
    except Exception as e:  # noqa: BLE001
        return 502, {"error": {"code": "voice_failed", "message": type(e).__name__}}


def route(method, path, body, caller, event=None):
    if method == "POST" and path == "/session":
        return 200, fsm.create_session(caller, body)
    if method == "POST" and path == "/turn":
        return 200, fsm.turn(caller, body)
    if method == "POST" and path == "/action":
        return 200, fsm.action(caller, body)
    if method == "POST" and path == "/demo/reset":
        return 200, fsm.reset(caller, body)
    if method == "POST" and path == "/voice/tts":
        return _voice("handle_tts", body)
    if method == "POST" and path == "/voice/stt-url":
        return _voice("handle_stt_url", body)
    if method == "GET" and path.startswith("/admin/"):
        svc = path.split("/")[2]
        try:
            import admin  # helpers de C (allowlist + redacción)
            return admin.handle(svc, event)
        except ImportError:
            pass
        if svc == "logs":
            return 200, {"service": "logs", "items": mock.recent_logs(100)}
        if svc in ADMIN_SERVICES:
            return 200, {"service": svc, "items": mock.admin_list(svc)}
        return 404, {"error": {"code": "not_found", "message": "servicio desconocido"}}
    if method == "POST" and path == "/internal/seed" and caller == "direct":
        return 200, mock.seed()
    if method == "POST" and path == "/internal/warm" and caller == "direct":
        import nlu
        return 200, {"gliner_warm_sent": nlu.warm()}
    return 404, {"error": {"code": "not_found", "message": f"{method} {path}"}}


def handler(event, context=None):
    t0 = time.time()
    if isinstance(event, str):
        event = json.loads(event)
    status, body, http = 500, None, False
    fsm.TRACE.clear()
    mock.STATS.clear()
    trace, sid = {}, None
    try:
        method, path, req, http = _parse(event)
        sid = (req or {}).get("sessionId")
        status, body = route(method, path, req or {}, _caller(event), event)
    except fsm.ApiError as e:
        status = e.status
        s = e.session
        if s:
            body = fsm.out(s, T.stale(s["revision"], e.message) if e.status == 409 else T.message(s["revision"], e.message),
                           e.message, "real")
        else:
            body = {"sessionId": sid, "state": None, "revision": None, "messages": [], "spokenText": "", "mode": "real"}
        body["error"] = {"code": e.code, "message": e.message}
    except json.JSONDecodeError:
        status, body = 400, {"error": {"code": "bad_request", "message": "JSON inválido"}}
    except Exception as e:  # noqa: BLE001
        print("ERROR", type(e).__name__, traceback.format_exc()[-1500:])
        status, body = 500, {"sessionId": sid, "state": None, "revision": None, "messages": [],
                             "spokenText": "Tuve un problema. ¿Lo intentamos de nuevo?", "mode": "simulado",
                             "error": {"code": "internal", "message": type(e).__name__}}
    ms = int((time.time() - t0) * 1000)
    try:
        p = locals().get("path", "?")
        if not str(p).startswith("/admin"):
            mock.log({"route": f"{locals().get('method', '?')} {p}", "status": status, "ms": ms,
                      "state": (body or {}).get("state"), "mode": (body or {}).get("mode"),
                      "sessionId": (sid or (body or {}).get("sessionId") or "")[:10], **_trace_of()})
    except Exception:  # noqa: BLE001
        pass
    print(json.dumps({"route": locals().get("path"), "status": status, "ms": ms, **_trace_of()}, ensure_ascii=False))
    if http:
        return {"statusCode": status, "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
                "body": json.dumps(body, ensure_ascii=False)}
    return dict(body or {}, _status=status, _ms=ms, _trace=_trace_of())


def _trace_of():
    return dict({k: v for k, v in fsm.TRACE.items() if v is not None}, **mock.STATS)
