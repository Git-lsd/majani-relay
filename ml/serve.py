"""Local test server for the app (phone on the same Wi-Fi): correct audio/wasm types, no caching.
Run from kahawa-check/:  ../.venv/bin/python ml/serve.py   then open http://<Mac IP>:8765 on the phone."""
import http.server, functools, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.m4a': 'audio/mp4', '.wasm': 'application/wasm', '.mjs': 'text/javascript',
                      '.webmanifest': 'application/manifest+json', '.onnx': 'application/octet-stream'}

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

if __name__ == '__main__':
    http.server.ThreadingHTTPServer(('0.0.0.0', 8765), functools.partial(Handler, directory=ROOT)).serve_forever()
