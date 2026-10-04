"""Local test server for the app (phone on the same Wi-Fi): correct audio/wasm types, no caching.
Run from kahawa-check/:  ../.venv/bin/python ml/serve.py   then open http://<laptop IP>:8765 on the phone.
POST /baseline/save stores one labeller's human-baseline answers in ../data_work/baseline/ (outside the repo)."""
import http.server, functools, os, json, re, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_DIR = os.path.join(os.path.dirname(ROOT), 'data_work', 'baseline')
MAX_BODY = 200 * 1024


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.m4a': 'audio/mp4', '.wasm': 'application/wasm', '.mjs': 'text/javascript',
                      '.webmanifest': 'application/manifest+json', '.onnx': 'application/octet-stream'}

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.split('?')[0] != '/baseline/save':
            self.close_connection = True
            return self._json(404, {'ok': False, 'error': 'not found'})
        try:
            n = int(self.headers.get('Content-Length', ''))
        except ValueError:
            n = -1
        if n < 0:
            self.close_connection = True
            return self._json(411, {'ok': False, 'error': 'Content-Length required'})
        if n > MAX_BODY:
            self.close_connection = True  # body not read
            return self._json(413, {'ok': False, 'error': f'body larger than {MAX_BODY} bytes'})
        raw = self.rfile.read(n)
        try:
            data = json.loads(raw)
            assert isinstance(data, dict)
        except Exception:
            return self._json(400, {'ok': False, 'error': 'body must be a JSON object'})
        safe = re.sub(r'[^A-Za-z0-9_-]+', '-', str(data.get('name') or '').strip().lower()).strip('-')[:40] or 'anon'
        t = time.time()
        stamp = time.strftime('%Y%m%d-%H%M%S', time.localtime(t)) + f'-{int(t * 1e6) % 1000000:06d}'
        os.makedirs(BASELINE_DIR, exist_ok=True)
        path = os.path.join(BASELINE_DIR, f'{safe}_{stamp}.json')
        with open(path + '.tmp', 'wb') as fh:
            fh.write(raw)
        os.replace(path + '.tmp', path)
        self._json(200, {'ok': True, 'file': os.path.basename(path)})


if __name__ == '__main__':
    http.server.ThreadingHTTPServer(('0.0.0.0', 8765), functools.partial(Handler, directory=ROOT)).serve_forever()
