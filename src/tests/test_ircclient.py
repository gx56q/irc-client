import socket
import threading
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock

from src.IRCClient import IRCClient


class TestIRCClient(unittest.TestCase):

    @patch('socket.socket')
    def test_connect(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()
        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_socket.return_value.connect.assert_called_once_with(
            ('irc.example.com', 6667))

    @patch('socket.socket')
    def test_auth(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        with patch.object(client, 'send_data') as mock_send_data:
            client.auth()

        mock_send_data.assert_has_calls([
            mock.call('NICK', 'test_user'),
            mock.call('USER', 'test_user 0 * :test_user')
        ])

    @patch('socket.socket')
    def test_disconnect(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        with patch.object(client, 'send_data') as mock_send_data:
            client.disconnect('Leaving...')

        mock_send_data.assert_called_once_with('QUIT', ':Leaving...')
        mock_socket.return_value.close.assert_called_once()

    @patch('socket.socket')
    def test_send_message(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        with patch.object(client, 'send_data') as mock_send_data:
            client.send_message('#test_channel', 'Hello, world!')

        expected_calls = [
            mock.call('PRIVMSG', '#test_channel :Hello, world!'),
        ]
        mock_send_data.assert_has_calls(expected_calls)

    @patch('socket.socket')
    def test_join_channel(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        with patch.object(client, 'send_data') as mock_send_data:
            client.join_channel('#test_channel')

        mock_send_data.assert_called_once_with('JOIN', '#test_channel')

    @patch('socket.socket')
    def test_leave_channel(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        with patch.object(client, 'send_data') as mock_send_data:
            client.leave_channel('#test_channel')

        mock_send_data.assert_called_once_with('PART', '#test_channel')

    @patch('socket.socket')
    def test_start_listening(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        with patch.object(threading, 'Thread') as mock_thread:
            client.start_listening()

        mock_thread.assert_called_once_with(target=client.listen)
        mock_thread.return_value.start.assert_called_once()

    @patch('socket.socket')
    def test_send_data_with_message(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        client.send_data('PRIVMSG', '#test_channel :Hello, world!')

        mock_socket.return_value.send.assert_called_once_with(
            b'PRIVMSG #test_channel :Hello, world!\r\n')

    @patch('socket.socket')
    def test_send_data_no_message(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        client.send_data('TEST')

        mock_socket.return_value.send.assert_called_once_with(
            b'TEST\n')

    @patch('socket.socket')
    def test_get_response(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        mock_socket.return_value.recv.return_value = b':irc.example.com 00\r\n'
        response = client.get_response()

        mock_socket.return_value.recv.assert_called_once_with(1024)
        self.assertEqual(response,
                         ':irc.example.com 00\r\n')

    @patch('socket.socket')
    def test_get_response_unicode_decode_error(self, mock_socket):
        mock_recv = MagicMock(
            side_effect=UnicodeDecodeError("encoding", b"bytes", 0, 1,
                                           "reason"))
        mock_socket.return_value.recv = mock_recv

        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        client.connect()

        response = client.get_response()

        mock_socket.return_value.recv.assert_called_once_with(1024)

        self.assertEqual(response, '')

    @patch('socket.socket')
    def test_get_channels(self, mock_socket):
        client = IRCClient(username='test_user', server='irc.example.com',
                           port=6667)
        with patch.object(client, 'send_data') as mock_send_data:
            client.get_channels()
        mock_send_data.assert_called_once_with('LIST')


if __name__ == '__main__':
    unittest.main()
