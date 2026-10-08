import http.server, json, os, sys
sys.path.insert(0, '/workspace/hackathon-connect/services/api')
import voice
ROOT = '/tmp/voicetest/dist'
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get('content-length', 0))) or b'{}')
        r = voice.handle_stt_url(body) if self.path == '/api/voice/stt-url' else voice.handle_tts(body)
        b = json.dumps(r).encode()
        self.send_response(200); self.send_header('content-type', 'application/json'); self.end_headers(); self.wfile.write(b)
http.server.ThreadingHTTPServer(('127.0.0.1', 8765), H).serve_forever()
