import socket
import ssl
import struct
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


class EPPClient:
    """Minimal EPP-over-TLS client (RFC 5734 framing)."""

    def __init__(self, host, port, ipv6=False, timeout=30):
        self.host = host
        self.port = int(port)
        self.ipv6 = ipv6
        self.timeout = timeout
        self.sock = None

    def connect(self):
        family = socket.AF_INET6 if self.ipv6 else socket.AF_INET
        info = socket.getaddrinfo(self.host, self.port, family, socket.SOCK_STREAM)
        fam, socktype, proto, _, sockaddr = info[0]
        raw = socket.socket(fam, socktype, proto)
        raw.settimeout(self.timeout)
        raw.connect(sockaddr)
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.sock = ctx.wrap_socket(raw, server_hostname=self.host)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def _recv_all(self, length):
        data = b""
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                raise ConnectionError("Socket closed prematurely")
            data += chunk
        return data

    def receive(self):
        total = struct.unpack("!I", self._recv_all(4))[0]
        return self._recv_all(total - 4).decode("utf-8")

    def send(self, xml):
        payload = xml.encode()
        self.sock.sendall(struct.pack("!I", len(payload) + 4) + payload)


def render_template(name, **placeholders):
    xml = (TEMPLATES / name).read_text()
    for key, value in placeholders.items():
        xml = xml.replace(f"{{{key}}}", value)
    return xml
