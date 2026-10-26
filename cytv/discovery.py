"""Bounded, read-only LG webOS SSDP discovery; no subnet/port scanning."""
import http.client
import io
import ipaddress
import socket
import time
from types import SimpleNamespace
import unicodedata
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

TARGET = 'urn:lge-com:service:webos-second-screen:1'
MULTICAST = ('239.255.255.250', 1900)
SEARCH = (f'M-SEARCH * HTTP/1.1\r\nHOST: {MULTICAST[0]}:{MULTICAST[1]}\r\n'
          f'MAN: "ssdp:discover"\r\nST: {TARGET}\r\nMX: 1\r\n\r\n').encode('ascii')


def local_address(host):
    address = ipaddress.IPv4Address(host)
    return address.is_private and not (address.is_loopback or address.is_unspecified or
                                      address.is_multicast or address.is_reserved)


def parse_reply(packet, peer):
    """Ignore unrelated/malformed packets and off-device description URLs."""
    try:
        if len(packet) > 8192 or b'\r\n\r\n' not in packet or not local_address(peer):
            return None
        lines = packet.decode('utf-8').split('\r\n')
        if lines[0] != 'HTTP/1.1 200 OK':
            return None
        headers = {}
        for line in lines[1:]:
            if not line:
                break
            key, value = line.split(':', 1)
            key = key.strip().lower()
            if key in headers:
                return None
            headers[key] = value.strip()
        if headers.get('st') != TARGET:
            return None
        location = headers.get('location', '')
        if any(ord(c) < 33 or ord(c) > 126 for c in location):
            return None
        url = urlsplit(location)
        if (url.scheme != 'http' or url.hostname != peer or url.username or url.password or
                url.fragment or not 1 <= (url.port if url.port is not None else 80) <= 65535):
            return None
        return location
    except (UnicodeError, ValueError):
        return None


def description_name(data):
    try:
        if len(data) > 65536 or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
            return 'LG webOS TV'
        # Reject alternate encodings too, before ElementTree could expand entities.
        text = data.decode('utf-8-sig')
        if '\x00' in text:
            return 'LG webOS TV'
        root = ET.fromstring(text)
        values = {}
        for element in root.iter():
            tag = element.tag.rsplit('}', 1)[-1]
            if tag in ('friendlyName', 'modelName') and tag not in values:
                clean = ''.join(c if not unicodedata.category(c).startswith('C') else ' '
                                for c in (element.text or ''))
                values[tag] = ' '.join(clean.split())[:80]
        name = values.get('friendlyName') or 'LG webOS TV'
        model = values.get('modelName')
        return f'{name} ({model})' if model and model not in name else name
    except (UnicodeError, ET.ParseError, ValueError):
        return 'LG webOS TV'


def fetch_name(location, timeout):
    """Read at most 64 KiB from the responding TV, within an absolute deadline.

    Collect the bounded HTTP response first, then let stdlib parse it in memory.
    This also bounds slow/trickling headers. No proxies or redirects are used.
    """
    deadline = time.monotonic() + timeout
    data = bytearray()
    try:
        url = urlsplit(location)
        path = (url.path or '/') + ('?' + url.query if url.query else '')
        request = f'GET {path} HTTP/1.1\r\nHost: {url.netloc}\r\nConnection: close\r\n\r\n'.encode('ascii')
        with socket.create_connection((url.hostname, url.port or 80), timeout=timeout) as connection:
            connection.settimeout(max(0.001, deadline - time.monotonic()))
            connection.sendall(request)
            while len(data) <= 65536 and time.monotonic() < deadline:
                connection.settimeout(max(0.001, deadline - time.monotonic()))
                try:
                    chunk = connection.recv(min(4096, 65537 - len(data)))
                except socket.timeout:
                    break
                if not chunk:
                    break
                data.extend(chunk)
        if len(data) > 65536:
            return 'LG webOS TV'
        with http.client.HTTPResponse(SimpleNamespace(makefile=lambda _: io.BytesIO(data))) as response:
            response.begin()
            if response.status == 200:
                body = response.read(65537)
                if response.length in (None, 0):
                    return description_name(body)
    except (OSError, ValueError, UnicodeError, http.client.HTTPException):
        pass
    return 'LG webOS TV'


def interface_addresses():
    # psutil supplies the same small interface inventory on Windows/macOS/Linux.
    # Explicit multicast interfaces avoid a VPN taking the OS's multicast route.
    import psutil
    stats = psutil.net_if_stats()
    return sorted({address.address for name, addresses in psutil.net_if_addrs().items()
                   if name in stats and stats[name].isup
                   for address in addresses
                   if address.family == socket.AF_INET and not address.ptp and local_address(address.address)})[:16]


def find_tvs(timeout=3):
    found = {}
    deadline = time.monotonic() + timeout
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as udp:
        udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        udp.bind(('', 0))
        udp.settimeout(timeout)
        sent, last_error = False, None
        for host in interface_addresses() or ['0.0.0.0']:
            try:
                udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
                # Repetition tolerates a lost datagram without probing other devices.
                udp.sendto(SEARCH, MULTICAST)
                udp.sendto(SEARCH, MULTICAST)
                sent = True
            except OSError as exc:
                last_error = exc
        if not sent and last_error:
            raise last_error
        for _ in range(128):
            remaining = deadline - time.monotonic()
            if remaining <= 0 or len(found) >= 16:
                break
            udp.settimeout(remaining)
            try:
                packet, peer = udp.recvfrom(8193)
            except socket.timeout:
                break
            location = parse_reply(packet, peer[0])
            if location:
                found.setdefault(peer[0], location)
    # All name lookups share a second short budget; unavailable names keep the TV.
    deadline = time.monotonic() + 2
    result = []
    for host in sorted(found, key=ipaddress.IPv4Address):
        remaining = deadline - time.monotonic()
        name = fetch_name(found[host], min(0.7, remaining)) if remaining > 0 else 'LG webOS TV'
        result.append({'host': host, 'name': name})
    return result
