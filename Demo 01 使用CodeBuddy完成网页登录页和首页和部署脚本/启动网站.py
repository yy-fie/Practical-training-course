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
        print("Demo 01 网站已启动：http://127.0.0.1:%d/login.html" % PORT)
        print("保持本窗口开启，按 Ctrl+C 可停止服务。")
        httpd.serve_forever()
except OSError as e:
    print("启动失败：", e)
    print("可能原因：8000 端口已被占用，请先运行 停止网站.bat 再重试。")
    input("按回车键退出...")
