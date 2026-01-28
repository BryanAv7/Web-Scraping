import http.server
import socketserver
import webbrowser
import threading
import os
import sys
import time

PORT = 8000
last_heartbeat = time.time()
TIMEOUT = 5  # 10 segundos

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_heartbeat
        if self.path == "/heartbeat":
            last_heartbeat = time.time()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            super().do_GET()

def monitor_browser(server):
    global last_heartbeat
    while True:
        time.sleep(2)
        if time.time() - last_heartbeat > TIMEOUT:
            print("\n🛑 Navegador cerrado — apagando servidor")
            server.shutdown()
            break

def abrir_navegador():
    #webbrowser.open(f"http://localhost:{PORT}/index.html")
    webbrowser.open(f"http://localhost:{PORT}/dashboard/index.html")


if __name__ == "__main__":
    ###os.chdir(os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(BASE_DIR)

    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"🌐 Dashboard en http://localhost:{PORT}")
        threading.Thread(
            target=monitor_browser,
            args=(httpd,),
            daemon=True
        ).start()

        threading.Timer(1, abrir_navegador).start()
        httpd.serve_forever()

    print("✅ Servidor cerrado limpiamente")
