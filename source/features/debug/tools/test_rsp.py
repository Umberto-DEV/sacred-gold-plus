import unittest
from unittest.mock import patch

from .rsp import Rsp, RspError


class FakeSocket:
    def __init__(self, peer='127.0.0.1', incoming=b'+'):
        self.peer = peer
        self.incoming = incoming
        self.sent = bytearray()
        self.closed = False

    def getpeername(self):
        return (self.peer, 3333)

    def recv(self, amount):
        data, self.incoming = self.incoming[:amount], self.incoming[amount:]
        return data

    def sendall(self, data):
        self.sent.extend(data)

    def settimeout(self, _):
        pass

    def setsockopt(self, *_):
        pass

    def close(self):
        self.closed = True


class RspTransportTests(unittest.TestCase):
    def instance(self, incoming=b''):
        client = Rsp.__new__(Rsp)
        client.s = FakeSocket(incoming=incoming)
        client.buf = b''
        client.noack = True
        client._alt = False
        return client

    def test_receive_buffer_and_packet_body_are_bounded(self):
        client = self.instance(b'x')
        client.buf = b'a' * Rsp.MAX_BUFFER
        with self.assertRaisesRegex(RspError, 'buffer'):
            client._recv()
        client.buf = b'$' + b'a' * (Rsp.MAX_PACKET + 1) + b'#00'
        with self.assertRaisesRegex(RspError, 'pacchetto'):
            client.read_packet()

    def test_outbound_command_and_malformed_checksum_are_refused(self):
        client = self.instance()
        with self.assertRaisesRegex(RspError, 'comando'):
            client.send('x' * (Rsp.MAX_PACKET + 1))
        client.buf = b'$OK#zz'
        with self.assertRaisesRegex(RspError, 'checksum'):
            client.read_packet()

    def test_only_loopback_peers_pass_before_handshake(self):
        remote = FakeSocket(peer='192.0.2.10')
        with patch('socket.create_connection', return_value=remote):
            client = Rsp.__new__(Rsp)
            with self.assertRaisesRegex(RspError, 'non loopback'):
                client._apri('example.test', 3333, 1, 1)
        self.assertTrue(remote.closed)
        self.assertEqual(remote.sent, b'')

        loopback = FakeSocket(peer='::1')
        with patch('socket.create_connection', return_value=loopback):
            client = Rsp.__new__(Rsp)
            client._apri('localhost', 3333, 1, 1)
        self.assertEqual(loopback.sent, b'+')


if __name__ == '__main__':
    unittest.main()
