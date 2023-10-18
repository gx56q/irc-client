import unittest
from src import IRCClient


class TestIRCClient(unittest.TestCase):

    def setUp(self):
        self.client = IRCClient.IRCClient('TestNick', 'chat.freenode.net')

    def tearDown(self):
        if self.client.is_connected():
            self.client.disconnect()

    def test_connect(self):
        self.client.connect()
        self.assertTrue(self.client.is_connected())

    def test_disconnect(self):
        self.client.connect()
        self.client.disconnect()
        self.assertFalse(self.client.is_connected())


if __name__ == '__main__':
    unittest.main()
