import socket
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from cytv import discovery


def reply(host='192.168.1.20', target=None, location=None):
    return ('HTTP/1.1 200 OK\r\nST: ' + (target or discovery.TARGET) +
            '\r\nLOCATION: ' + (location or f'http://{host}:3000/description.xml') + '\r\n\r\n').encode()


class DiscoveryTests(unittest.TestCase):
    def test_only_matching_local_webos_replies_are_accepted(self):
        self.assertEqual(discovery.parse_reply(reply(), '192.168.1.20'),
                         'http://192.168.1.20:3000/description.xml')
        for packet, peer in [
            (reply(target='ssdp:all'), '192.168.1.20'),
            (reply(), '8.8.8.8'), (reply(), '127.0.0.1'),
            (reply(location='http://example.com/x'), '192.168.1.20'),
            (reply(location='http://192.168.1.21/x'), '192.168.1.20'),
            (reply(location='http://user@192.168.1.20/x'), '192.168.1.20'),
            (reply(location='file:///etc/passwd'), '192.168.1.20'),
            (reply(location='http://192.168.1.20:0/x'), '192.168.1.20'),
            (reply()[:-4], '192.168.1.20'),
            (reply() + b'x' * 9000, '192.168.1.20'),
            (reply().replace(b'\r\n\r\n', b'\r\nST: other\r\n\r\n'), '192.168.1.20'),
        ]:
            with self.subTest(peer=peer, packet=packet[:100]):
                self.assertIsNone(discovery.parse_reply(packet, peer))

    def test_names_from_xml_are_optional_and_safe_for_the_terminal(self):
        xml = b'<root xmlns="urn:schemas-upnp-org:device-1-0"><device><friendlyName>Living room TV</friendlyName><modelName>OLED C3</modelName></device></root>'
        self.assertEqual(discovery.description_name(xml), 'Living room TV (OLED C3)')
        self.assertEqual(discovery.description_name(xml.replace(b'Living room TV', b'Room&#x9;TV')), 'Room TV (OLED C3)')
        for data in (b'not XML', b'x' * 65537, b'<!DOCTYPE root [<!ENTITY x "secret">]><root>&x;</root>'):
            self.assertEqual(discovery.description_name(data), 'LG webOS TV')

    def test_search_sends_ssdp_deduplicates_and_closes_socket(self):
        class UDP:
            def __init__(self):
                self.packets = iter([(reply(), ('192.168.1.20', 1900)),
                                     (reply(), ('192.168.1.20', 1900)),
                                     (reply(target='other'), ('192.168.1.30', 1900))])
                self.sent, self.closed = [], False
            def __enter__(self): return self
            def __exit__(self, *args): self.closed = True
            def setsockopt(self, *args): pass
            def bind(self, address): self.bound = address
            def settimeout(self, value): self.timeout = value
            def sendto(self, data, address): self.sent.append((data, address))
            def recvfrom(self, size):
                try: return next(self.packets)
                except StopIteration: raise socket.timeout
        udp = UDP()
        with patch.object(discovery.socket, 'socket', return_value=udp), \
             patch.object(discovery, 'interface_addresses', return_value=['192.168.1.5']), \
             patch.object(discovery, 'fetch_name', return_value='Living room') as fetch:
            result = discovery.find_tvs()
        self.assertEqual(result, [{'host': '192.168.1.20', 'name': 'Living room'}])
        self.assertEqual(fetch.call_count, 1)
        self.assertTrue(udp.closed)
        self.assertEqual(udp.bound, ('', 0))
        self.assertIn(discovery.TARGET.encode(), udp.sent[0][0])
        self.assertEqual(udp.sent[0][1], ('239.255.255.250', 1900))

    def test_metadata_failure_keeps_discovered_tv(self):
        # Names are just labels; malformed XML and unreachable descriptions must
        # never turn a valid SSDP response into a missing TV.
        with patch.object(discovery.socket, 'create_connection', side_effect=OSError):
            self.assertEqual(discovery.fetch_name('http://192.168.1.20/x', 1), 'LG webOS TV')

    def test_name_fetch_is_bounded_and_does_not_follow_redirects(self):
        class TCP:
            def __init__(self, raw): self.raw, self.sent, self.closed = raw, b'', False
            def __enter__(self): return self
            def __exit__(self, *args): self.closed = True
            def settimeout(self, value): pass
            def sendall(self, data): self.sent = data
            def recv(self, size):
                result, self.raw = self.raw[:size], self.raw[size:]
                return result
        body = b'<root><device><friendlyName>Bedroom</friendlyName></device></root>'
        for raw, expected in [
            (b'HTTP/1.1 200 OK\r\nContent-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body, 'Bedroom'),
            (b'HTTP/1.1 302 Found\r\nLocation: http://example.com\r\n\r\n', 'LG webOS TV'),
            (b'HTTP/1.1 200 OK\r\n\r\n' + b'x' * 65537, 'LG webOS TV'),
            (b'HTTP/1.1 200 OK\r\nContent-Length: 999\r\n\r\n' + body, 'LG webOS TV'),
        ]:
            connection = TCP(raw)
            with patch.object(discovery.socket, 'create_connection', return_value=connection) as create:
                self.assertEqual(discovery.fetch_name('http://192.168.1.20:3000/description.xml', 1), expected)
            self.assertEqual(create.call_count, 1)
            self.assertTrue(connection.closed)
            self.assertIn(b'GET /description.xml HTTP/1.1', connection.sent)

    def test_interface_inventory_excludes_loopback_down_and_point_to_point_vpn(self):
        def addr(ip, ptp=None):
            return SimpleNamespace(family=socket.AF_INET, address=ip, ptp=ptp)
        import psutil
        with patch.object(psutil, 'net_if_addrs', return_value={
            'lo': [addr('127.0.0.1')], 'wifi': [addr('192.168.1.5')],
            'down': [addr('192.168.2.5')], 'vpn': [addr('10.1.1.1', '10.1.1.1')],
        }), patch.object(psutil, 'net_if_stats', return_value={
            name: SimpleNamespace(isup=name != 'down') for name in ('lo', 'wifi', 'down', 'vpn')
        }):
            self.assertEqual(discovery.interface_addresses(), ['192.168.1.5'])


if __name__ == '__main__':
    unittest.main()
