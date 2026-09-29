
import socket
import select
import http.client
from urllib.parse import urlsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ProxyHandler(BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.1"

    def do_CONNECT(self):
        """Create a tunnel for HTTPS traffic."""
        host, _, port = self.path.partition(":")
        port = int(port or 443)

        try:
            with socket.create_connection((host, port), timeout=10) as remote:
                self.send_response(200, "Connection Established")
                self.end_headers()

                sockets = [self.connection, remote]

                while True:
                    readable, _, exceptional = select.select(
                        sockets, [], sockets, 60
                    )

                    if exceptional or not readable:
                        break

                    for source in readable:
                        destination = (
                            remote if source is self.connection
                            else self.connection
                        )

                        data = source.recv(65536)

                        if not data:
                            return

                        destination.sendall(data)

        except Exception as error:
            print("HTTPS tunnel error:", error)

    def do_GET(self):
        self.forward_request()

    def do_POST(self):
        self.forward_request()

    def do_HEAD(self):
        self.forward_request()

    def do_PUT(self):
        self.forward_request()

    def do_DELETE(self):
        self.forward_request()

    def forward_request(self):
        """Forward a regular HTTP request."""
        try:
            url = urlsplit(self.path)

            if url.scheme != "http" or not url.hostname:
                self.send_error(400, "Use an absolute HTTP URL")
                return

            host = url.hostname
            port = url.port or 80

            path = url.path or "/"

            if url.query:
                path += "?" + url.query

            headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower() not in (
                    "proxy-connection",
                    "proxy-authorization",
                    "connection",
                    "transfer-encoding",
                )
            }

            body = None

            if self.command in ("POST", "PUT"):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else None

            connection = http.client.HTTPConnection(
                host, port, timeout=20
            )

            connection.request(
                self.command,
                path,
                body=body,
                headers=headers,
            )

            response = connection.getresponse()

            self.send_response(
                response.status, response.reason
            )

            for key, value in response.getheaders():
                if key.lower() not in (
                    "transfer-encoding",
                    "connection",
                    "keep-alive",
                ):
                    self.send_header(key, value)

            self.end_headers()

            if self.command != "HEAD":
                while True:
                    data = response.read(65536)

                    if not data:
                        break

                    self.wfile.write(data)

            connection.close()

        except Exception as error:
            print("HTTP forwarding error:", error)

            if not self.wfile.closed:
                try:
                    self.send_error(502, "Proxy forwarding failed")
                except Exception:
                    pass


class ProxyServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    server = ProxyServer(
        ("127.0.0.1", 8888),
        ProxyHandler
    )

    print("ProxyOS network proxy is running!")
    print("Address: 127.0.0.1:8888")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping proxy...")
    finally:
        server.server_close()
