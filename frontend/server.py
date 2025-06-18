#!/usr/bin/env python3
"""
简单的 HTTP 服务器，用于运行前端界面
"""

import http.server
import os
import socketserver
import webbrowser
from pathlib import Path

PORT = 3001

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def end_headers(self):
        # 添加 CORS 头部以允许跨域请求
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    # 切换到前端目录
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    # 创建服务器
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"✨ 前端服务器已启动！")
        print(f"🌐 访问地址: http://localhost:{PORT}")
        print(f"📁 服务目录: {frontend_dir}")
        print(f"⚠️  请确保后端服务已在 http://localhost:8000 运行")
        print(f"🚀 正在自动打开浏览器...")
        
        # 自动打开浏览器
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            print("无法自动打开浏览器，请手动访问上述地址")
        
        print(f"按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == "__main__":
    main()