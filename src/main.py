import time
import IRCClient


def main():
    server = 'chat.freenode.net'
    port = 6667
    nickname = 'web-43'
    client = IRCClient.IRCClient(nickname, server, port)
    client.connect()
    client.start_listening()
    client.set_nickname()
    time.sleep(5)
    client.join_channel('#freenode')
    client.get_channels()
    client.send_message('Hello, world!')


if __name__ == '__main__':
    main()
