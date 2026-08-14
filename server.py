import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class FileReceiverHandler(BaseHTTPRequestHandler):
    """অন্য ডিভাইস থেকে ফাইল আসার সাথে সাথে রিসিভ করার লজিক"""

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            filename = self.headers.get('File-Name', 'received_file')

            # সেভ করার জন্য ফোল্ডার
            download_dir = "HandShare_Downloads"
            os.makedirs(download_dir, exist_ok=True)
            filepath = os.path.join(download_dir, filename)

            bytes_read = 0
            chunk_size = 64 * 1024  # 64 KB করে স্ট্রিম রাইট

            with open(filepath, 'wb') as f:
                while bytes_read < content_length:
                    read_bytes = min(chunk_size, content_length - bytes_read)
                    chunk = self.rfile.read(read_bytes)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_read += len(chunk)

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"File Uploaded Successfully!")

        except Exception as e:
            print(f"Error receiving file: {e}")
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        return


def start_server_in_background(port=5000):
    server = HTTPServer(('0.0.0.0', port), FileReceiverHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server