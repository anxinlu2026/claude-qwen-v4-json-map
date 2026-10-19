#!/usr/bin/env python3
"""Small local proxy between the Claude Code CLI and Ollama's Anthropic endpoint. With --no-think it sets "thinking": {"type": "disabled"} in every /v1/messages
request (the one form that switches thinking off: measured, see the evaluation notes) and passes everything else through, streaming included.
usage: ollama_proxy.py [--port 11435] [--target 127.0.0.1:11434] [--no-think]"""
import http.client, json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
a = sys.argv[1:]; port = int(a[a.index('--port') + 1]) if '--port' in a else 11435
host, tport = (a[a.index('--target') + 1] if '--target' in a else '127.0.0.1:11434').split(':'); tport = int(tport); nothink = '--no-think' in a
class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def handle_any(self):
        n = int(self.headers.get('Content-Length') or 0); body = self.rfile.read(n) if n else b''
        if nothink and self.command == 'POST' and self.path.startswith('/v1/messages') and body:
            try: d = json.loads(body); d['thinking'] = {"type": "disabled"}; body = json.dumps(d).encode()
            except Exception: pass
        hdr = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'content-length', 'connection')}; hdr['Content-Length'] = str(len(body))
        c = http.client.HTTPConnection(host, tport, timeout=3600); c.request(self.command, self.path, body, hdr); r = c.getresponse()
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in ('transfer-encoding', 'connection', 'content-length'): self.send_header(k, v)
        self.send_header('Transfer-Encoding', 'chunked'); self.end_headers()
        while True:
            chunk = r.read(4096) if r.getheader('Content-Type', '').startswith('text/event-stream') is False else r.read1(4096)
            if not chunk: break
            self.wfile.write(b'%x\r\n%s\r\n' % (len(chunk), chunk)); self.wfile.flush()
        self.wfile.write(b'0\r\n\r\n'); self.wfile.flush(); c.close()
    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = handle_any
    def log_message(self, *x): pass
ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
