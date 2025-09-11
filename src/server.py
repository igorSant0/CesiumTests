#!/usr/bin/env python3
import http.server
import socketserver
from urllib.parse import urlparse
import os

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token')
        
        if self.path.endswith('.pnts'):
            self.send_header('Content-Type', 'application/octet-stream')
        elif self.path.endswith('.json'):
            self.send_header('Content-Type', 'application/json')
        
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.end_headers()

if __name__ == "__main__":
    PORT = 8000
    Handler = CORSRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Servidor rodando na porta {PORT}")
        httpd.serve_forever()
