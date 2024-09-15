from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
# from pyngrok import ngrok

# ngrok.set_auth_token("")

class WebhookReceiver(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = urllib.parse.unquote(post_data.decode("utf-8"))
        print(f"Received data: {data}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run(server_class=HTTPServer, handler_class=WebhookReceiver, port=8000):
    # Start the HTTP server locally
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    # Expose the server using ngrok
    # public_url = ngrok.connect(port)
    print(f'Starting httpd on port {port}...')
    # print(f'Public URL: {public_url}')
    
    httpd.serve_forever()

if __name__ == "__main__":
    run()
