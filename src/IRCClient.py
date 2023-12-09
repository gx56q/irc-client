import socket
import threading
import time
from select import select


class IRCClient:
    def __init__(self, username, server, port=6667, callback=None):
        self.message_callback = callback
        self.listen_thread = None
        self.server = server
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.password = None
        self.username = username

    def connect(self):
        self.socket.connect((self.server, self.port))

    def auth(self):
        time.sleep(0.5)
        self.send_data('NICK', self.username)
        time.sleep(0.5)
        self.send_data('USER', f"{self.username} 0 * :{self.username}")

    def disconnect(self, message=""):
        self.send_data('QUIT', f":{message}")
        self.socket.close()

    def send_data(self, command, message=''):
        if message:
            full_message = f"{command} {message}\r\n"
        else:
            full_message = f"{command}\n"
        self.socket.send(full_message.encode('utf-8'))

    def get_response(self):
        try:
            return self.socket.recv(2048).decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            return ''

    def join_channel(self, channel_name):
        self.send_data('JOIN', channel_name)

    def send_message(self, channel, message):
        max_message_length = 400
        message_chunks = [message[i:i + max_message_length] for i in
                          range(0, len(message), max_message_length)]

        for chunk in message_chunks:
            self.send_data('PRIVMSG', f"{channel} :{chunk}")
            time.sleep(0.3)

    def change_nick(self, new_nick):
        self.send_data('NICK', new_nick)
        self.username = new_nick

    def leave_channel(self, channel_name):
        self.send_data('PART', channel_name)

    def listen(self):
        while True:
            (readable, writable, errored) = select([self.socket], [],
                                                   [self.socket], 0.1)
            if readable:
                read_buffer = ""
                read_buffer += self.get_response()
                temp = str.split(read_buffer, "\n")
                temp.pop()
                for line in temp:
                    line = str.rstrip(line)
                    line = str.split(line)
                    if len(line) >= 1:
                        if line[0] == 'PING':
                            self.send_data('PONG', line[1])
                        else:
                            self.message_callback(line)

    def start_listening(self):
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def get_channels(self):
        self.send_data('LIST')

    def is_connected(self):
        return self.socket and self.socket.fileno() != -1
