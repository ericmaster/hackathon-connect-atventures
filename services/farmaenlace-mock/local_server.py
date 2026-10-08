"""Servidor HTTP local de la API mock (para pruebas offline): FV_STORE=memory, sin SigV4.

  python3 services/farmaenlace-mock/local_server.py 8765
Simula el requestContext IAM del rol del orquestador.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "api"))  # store.py compartido
os.environ.setdefault("FV_STORE", "memory")
import app  # noqa: E402


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _do(self):
        u = urlsplit(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        ev = {"rawPath": u.path, "queryStringParameters": dict(parse_qsl(u.query)) or None,
              "headers": {k.lower(): v for k, v in self.headers.items()},
              "body": self.rfile.read(n).decode() if n else None,
              "requestContext": {"http": {"method": self.command}, "authorizer": {"iam": {
                  "userArn": "arn:aws:sts::000000000000:assumed-role/connect-atv-orchestrator-role/local"}}}}
        r = app.handler(ev)
        b = r["body"].encode()
        self.send_response(r["statusCode"])
        for k, v in r["headers"].items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    do_GET = do_POST = do_PUT = do_DELETE = _do

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    app.seed()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"farmaenlace-mock local on http://127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
