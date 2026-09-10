# -*- coding: utf-8 -*-
import http.server
import os
import socketserver
import threading
import webbrowser

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


try:
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        threading.Timer(
            0.5, lambda: webbrowser.open("http://127.0.0.1:%d/login.html" % PORT)
        ).start()
        print("Demo 01 website started: http://127.0.0.1:%d/login.html" % PORT)
        print("Keep this window open. Press Ctrl+C to stop.")
        httpd.serve_forever()
except OSError as e:
    print("Start failed:", e)
    print("Port 8000 may be in use. Run stop_website.bat first, then retry.")
    input("Press Enter to exit...")
