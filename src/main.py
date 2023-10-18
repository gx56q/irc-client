import time
import IRCClient


def main():
    server = 'chat.freenode.net'
    port = 6667
    nickname = 'web-43'
    client = IRCClient.IRCClient(nickname, server, port)
    print('Connecting to server...')
    client.connect()
    print('Starting listening thread...')
    client.start_listening()
    print('Authenticating...')
    client.auth()
    time.sleep(5)
    print('Joining channel...')
    client.join_channel('#freenode')
    time.sleep(5)
    print('Users in channel:')
    print(client.users)
    print('Getting channels...')
    client.get_channels()
    # print('Sending message...')
    # client.send_message('Hello, world!')


if __name__ == '__main__':
    main()
