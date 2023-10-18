import socket
import threading


class IRCClient:
    def __init__(self, nickname, server, port=6667):
        self.listen_thread = None
        self.server = server
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.password = None
        self.nickname = nickname
        self.active_channel = None
        self.channels = []
        self.users = []

    def connect(self):
        self.socket.connect((self.server, self.port))

    def auth(self):
        self.send_data('NICK', self.nickname)
        self.send_data('USER', f"{self.nickname} 0 * :{self.nickname}")

    def disconnect(self, message=""):
        self.send_data('QUIT', f":{message}")
        self.socket.close()

    def send_data(self, command, message=''):
        if message:
            full_message = f"{command} {message}\n"
        else:
            full_message = f"{command}\n"
        self.socket.send(full_message.encode('utf-8'))

    def get_response(self):
        return self.socket.recv(2048).decode('utf-8')

    def join_channel(self, channel_name):
        self.users = []
        self.send_data('JOIN', channel_name)
        self.active_channel = channel_name
        if channel_name not in self.channels:
            self.channels.append(channel_name)

    def send_message(self, message):
        if self.active_channel:
            self.send_data('PRIVMSG', f"{self.active_channel} :{message}")
        else:
            raise ValueError('No active channel')

    def listen(self):
        while True:
            message = self.get_response()
            if message.startswith('PING'):
                self.send_data('PONG', message.split()[1])

            elif " 353 " in message:
                parts = message.split()
                # self.users += message
            print(message)

    def start_listening(self):
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def get_channels(self):
        self.send_data('LIST')

    def is_connected(self):
        return self.socket and self.socket.fileno() != -1
