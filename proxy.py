
import json
import os
import re
import socket
import ipaddress
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode, urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler

HOST = "127.0.0.1"
PORT = 8765
MAX_DOWNLOAD = 25 * 1024 * 1024
VERSION = "ProxyOS-2.0"


# ==========================================
# SEARCH PARSER
# ==========================================

class SearchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.current = None
        self.in_title = False
        self.title_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "")

        if tag == "a" and (
            "result__a" in classes
            or "result-link" in classes
        ):
            self.current = {
                "title": "",
                "url": attrs.get("href", "")
            }
            self.title_parts = []
            self.in_title = True

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.in_title and self.current:
            self.current["title"] = " ".join(
                "".join(self.title_parts).split()
            )

            self.results.append(self.current)
            self.current = None
            self.in_title = False


# ==========================================
# URL VALIDATION
# ==========================================

def validate_public_url(url):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise ValueError("Invalid URL.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are blocked.")

    try:
        addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM
        )
    except OSError:
        raise ValueError("Could not resolve hostname.")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0].split("%")[0])

        if not ip.is_global:
            raise ValueError("Private and local network addresses are blocked.")

    return url


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urljoin(req.full_url, newurl)
        validate_public_url(target)

        return super().redirect_request(
            req, fp, code, msg, headers, target
        )


# ==========================================
# HTTP SERVER
# ==========================================

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print("%s - %s" % (
            self.address_string(),
            fmt % args
        ))

    def send_data(
        self,
        status,
        data,
        content_type="application/json",
        extra_headers=None
    ):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")

        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)

        self.send_header("Content-Length", str(len(data)))
        self.end_headers()

        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_json(self, status, obj):
        self.send_data(
            status,
            json.dumps(obj).encode("utf-8")
        )

    def do_OPTIONS(self):
        self.send_data(204, b"")

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # ======================================
        # STATUS
        # ======================================

        if parsed.path == "/":
            return self.send_json(200, {
                "status": "running",
                "version": VERSION
            })

        if parsed.path == "/api/version":
            return self.send_json(200, {
                "version": VERSION,
                "server": "Proxy OS helper"
            })

        # ======================================
        # SEARCH
        # ======================================

        if parsed.path == "/api/search":
            query = params.get("q", [""])[0].strip()

            if not query:
                return self.send_json(400, {
                    "error": "Enter a search query."
                })

            fallback_url = (
                "https://duckduckgo.com/?"
                + urlencode({"q": query})
            )

            results = []
            search_error = None

            try:
                search_url = (
                    "https://html.duckduckgo.com/html/?"
                    + urlencode({"q": query})
                )

                request = Request(
                    search_url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 Chrome/131.0.0.0 "
                            "Safari/537.36"
                        ),
                        "Accept": "text/html"
                    }
                )

                with build_opener().open(
                    request, timeout=20
                ) as response:
                    html = response.read(
                        3_000_000
                    ).decode("utf-8", "replace")

                parser = SearchParser()
                parser.feed(html)

                for item in parser.results:
                    url = item["url"]

                    if url.startswith("//"):
                        url = "https:" + url

                    if url.startswith("/"):
                        url = urljoin(
                            "https://html.duckduckgo.com", url
                        )

                    if not url.startswith(("http://", "https://")):
                        continue

                    results.append({
                        "title": item["title"] or url,
                        "url": url,
                        "description": ""
                    })

            except Exception as error:
                search_error = str(error)
                print("Search error:", search_error)

            # GUARANTEED FALLBACK IF NO RESULTS WERE FOUND
            if not results:
                results = [{
                    "title": "Search DuckDuckGo for " + query,
                    "url": fallback_url,
                    "description": (
                        "No results could be extracted. "
                        "Click to view the search page."
                    )
                }]

            print("Search query:", query)
            print("Results returned:", len(results))

            return self.send_json(200, {
                "query": query,
                "results": results[:20],
                "count": len(results),
                "version": VERSION,
                "fallback": search_error is not None
            })

        # ======================================
        # DOWNLOAD
        # ======================================

        if parsed.path == "/api/download":
            url = params.get("url", [""])[0]

            try:
                validate_public_url(url)

                request = Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 ProxyOS/2.0"
                    }
                )

                with build_opener(
                    SafeRedirect()
                ).open(request, timeout=20) as response:

                    data = response.read(MAX_DOWNLOAD + 1)

                    if len(data) > MAX_DOWNLOAD:
                        return self.send_data(
                            413,
                            b"Download exceeds the 25 MB limit.",
                            "text/plain"
                        )

                    filename = os.path.basename(
                        urlparse(response.geturl()).path
                    ) or "download.bin"

                    filename = re.sub(
                        r"[^A-Za-z0-9._-]",
                        "_",
                        filename
                    )[:120] or "download.bin"

                    return self.send_data(
                        200,
                        data,
                        response.headers.get_content_type(),
                        {
                            "Content-Disposition":
                                f'attachment; filename="{filename}"'
                        }
                    )

            except Exception as error:
                return self.send_data(
                    400,
                    str(error).encode("utf-8"),
                    "text/plain; charset=utf-8"
                )

        # ======================================
        # UNKNOWN ROUTE
        # ======================================

        return self.send_json(404, {
            "error": "Not found"
        })


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)

    print("=" * 45)
    print("          PROXY OS HELPER")
    print("          VERSION:", VERSION)
    print("=" * 45)
    print(f"Server: http://{HOST}:{PORT}")
    print("Version: /api/version")
    print("Search: /api/search?q=hello")
    print("Downloads: /api/download?url=...")
    print("Press Ctrl+C to stop.")
    print("=" * 45)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Proxy OS helper...")
    finally:
        server.server_close()
