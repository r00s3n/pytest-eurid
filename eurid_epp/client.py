import re
import socket
import ssl
import struct
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


class EPPClient:
    """Minimal EPP-over-TLS client (RFC 5734 framing)."""

    def __init__(self, host, port, ipv6=False, timeout=30, transcript=None):
        self.host = host
        self.port = int(port)
        self.ipv6 = ipv6
        self.timeout = timeout
        self.sock = None
        self.ip = None
        # list of (direction, xml) tuples, passwords masked; used for the report
        self.transcript = transcript if transcript is not None else []

    def connect(self):
        family = socket.AF_INET6 if self.ipv6 else socket.AF_INET
        target = f"{self.host!r} port {self.port} ({'IPv6' if self.ipv6 else 'IPv4'})"
        try:
            info = socket.getaddrinfo(self.host, self.port, family, socket.SOCK_STREAM)
        except socket.gaierror as e:
            raise ConnectionError(
                f"Cannot resolve EPP_HOST {target}: {e}. Check EPP_HOST in your ENV_FILE "
                "(hostname only: no https://, spaces or quotes) and your VPN/DNS."
            ) from e
        fam, socktype, proto, _, sockaddr = info[0]
        self.ip = sockaddr[0]
        raw = socket.socket(fam, socktype, proto)
        raw.settimeout(self.timeout)
        try:
            raw.connect(sockaddr)
        except OSError as e:
            raw.close()
            raise ConnectionError(
                f"Cannot connect to EPP server {target}: {e}. "
                "Check EPP_PORT, VPN and IP whitelisting."
            ) from e
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
        xml = self._recv_all(total - 4).decode("utf-8")
        self.transcript.append(("received", mask_secrets(xml)))
        return xml

    def send(self, xml):
        self.transcript.append(("sent", mask_secrets(xml)))
        payload = xml.encode()
        self.sock.sendall(struct.pack("!I", len(payload) + 4) + payload)


def mask_secrets(xml):
    return re.sub(r"(<(?:\w+:)?(?:pw|newPW)>)[^<]*(</)", r"\1***\2", xml)


def render_template(name, **placeholders):
    xml = (TEMPLATES / name).read_text()
    for key, value in placeholders.items():
        xml = xml.replace(f"{{{key}}}", value)
    return xml
