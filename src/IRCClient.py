import socket
import threading


class IRCClient:
    def __init__(self, server, port=6667):
        self.listen_thread = None
        self.server = server
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nickname = None
        self.channels = []
        self.users = {}

    def connect(self):
        self.socket.connect((self.server, self.port))

    def send_data(self, command, message=''):
        if message:
            full_message = f"{command} {message}\n"
        else:
            full_message = f"{command}\n"
        self.socket.send(full_message.encode('utf-8'))

    def set_nickname(self, nickname):
        self.send_data('NICK', nickname)
        self.nickname = nickname

    def join_channel(self, channel_name):
        self.send_data('JOIN', channel_name)
        if channel_name not in self.channels:
            self.channels.append(channel_name)

    def send_message(self, message, channel=None):
        if channel:
            self.send_data('PRIVMSG', f"{channel} :{message}")
        else:
            for ch in self.channels:
                self.send_data('PRIVMSG', f"{ch} :{message}")

    def listen(self):
        while True:
            message = self.socket.recv(2048).decode('utf-8')
            if message.startswith('PING'):
                self.send_data('PONG', message.split()[1])
            # TODO: обработка других сообщений
            print(message)

    def start_listening(self):
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()
