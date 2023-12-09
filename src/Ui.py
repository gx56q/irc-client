from tkinter import *
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from src import IRCClient, emoticons
import time
import configparser

DEFAULT_SERVER_IP = 'chat.freenode.net'
SETTINGS_FILE = '../settings.ini'

class Window(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.client = None
        self.username = None
        self.password = None
        self.server = None
        self.port = 6667

        self.tabs = {}
        self.master = master
        self.parser = configparser.ConfigParser()
        self.read_settings()

        self.setup_window()
        self.setup_notebook()
        self.setup_chat_interface()

        self.show_user_popup()

    def show_user_popup(self):
        self.user_popup = Toplevel(self.master)
        self.user_popup.transient(self.master)

        self.center_window(self.user_popup, 350, 150)

        self.user_popup.resizable(True, False)

        self.user_popup.grid_columnconfigure(1, weight=1)

        default_server_ip = self.server or DEFAULT_SERVER_IP

        self.server_entry = self.create_label_entry(self.user_popup,
                                                    "Server IP", 10, 0,
                                                    default_server_ip)
        self.username_entry = self.create_label_entry(self.user_popup,
                                                      "Username", 10, 1,
                                                      self.username or '')
        self.password_entry = self.create_label_entry(self.user_popup,
                                                      "Password", 10, 2,
                                                      self.password or '',
                                                      show="*")

        connect_button = Button(self.user_popup, text='Connect',
                                command=self.on_connect_button_click)
        connect_button.grid(row=3, columnspan=2, pady=10)

        self.user_popup.focus_force()
        self.user_popup.grab_set()

    def on_connect_button_click(self):
        self.server = self.server_entry.get()
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()

        if not self.username:
            messagebox.showinfo(message='You must enter a username',
                                icon='warning')
        elif ' ' in self.username:
            messagebox.showinfo(message='Username cannot contain spaces',
                                icon='warning')
        else:
            self.save_settings_to_file(self.server, self.username,
                                       self.password)

            self.client = IRCClient.IRCClient(self.username, self.server,
                                              self.port, self.update_chat)
            self.client.connect()
            self.client.auth()
            self.client.start_listening()
            self.user_popup.destroy()
            self.master.title('IRC Client - ' + self.username)

    def update_chat(self, message):
        self.master.after_idle(self.iterate_through_incoming, message)

    def setup_chat_interface(self):
        server_info_frame = ttk.Frame(self.n)
        server_info_frame.grid(sticky=N + S + E + W)
        self.n.add(server_info_frame, text='Server Info')

        server_info_frame.grid_rowconfigure(0, weight=8)
        server_info_frame.grid_rowconfigure(1, weight=3)
        server_info_frame.grid_columnconfigure(0, weight=1)

        text_receive = ScrolledText(server_info_frame, height=24, width=47,
                                    wrap=WORD)
        text_receive.grid(sticky=N + S + E + W, padx=(5, 5), pady=(5, 5))
        text_receive.config(state=DISABLED)

        text_entry = ScrolledText(server_info_frame, height=6, width=47,
                                  wrap=WORD)
        text_entry.grid(sticky=N + S + E + W, padx=(5, 5), pady=(5, 5))
        text_entry.bind('<Return>', self.check_pm_commands)

        self.tabs['Server Info'] = {
            'tab': server_info_frame,
            'textbox': text_receive,
            'entry': text_entry,
            'online_users': ''
        }

        self.n.grid(row=0, column=0, sticky=N + S + E + W)

    def setup_notebook(self):
        self.n = ttk.Notebook(self.master)
        self.n.grid(sticky=N + S + E + W)
        self.n.enable_traversal()

    def setup_window(self):
        self.master.title('IRC Client')
        self.center_window(self.master, 600, 500)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

    def read_settings(self):
        self.parser.read(SETTINGS_FILE)
        if 'DEFAULT' in self.parser:
            self.server = self.parser['DEFAULT'].get('server',
                                                     DEFAULT_SERVER_IP)
            self.username = self.parser['DEFAULT'].get('username', '')
            self.password = self.parser['DEFAULT'].get('password', '')

    @staticmethod
    def replace_emoticons(message):
        for emoticon, unicode_symbol in emoticons.EMOTICON_MAPPING.items():
            message = message.replace(emoticon, unicode_symbol)
        return message

    def check_pm_commands(self, event):
        tab = self.n.tab(self.n.select(), "text")
        to_text_box = self.tabs[tab]['textbox']
        raw_message = self.tabs[tab]['entry'].get('1.0', 'end-1c')
        self.tabs[tab]['entry'].delete('1.0', END)
        self.tabs[tab]['entry'].focus_force()
        if len(raw_message) >= 1 and raw_message[0] == '/':
            self.process_commands(raw_message)
        else:
            message = self.replace_emoticons(raw_message)
            self.post_message(self.username + ':>' + message + '\n',
                              to_text_box)
            self.client.send_message(tab, message)
        return 'break'

    def process_commands(self, message):
        if '/join' in message:
            if len(message.strip().split(' ')) == 1:
                messagebox.showinfo(message='You must specify a channel.',
                                    icon='warning')
            else:
                tab_name = message.split(' ')[1].lower()
                self.add_tab(tab_name, 'channel')
        elif '/channels' in message:
            self.client.get_channels()
        elif '/leave' in message:
            self.leave_channel()
        else:
            messagebox.showinfo(message='Command not found.', icon='warning')

    def iterate_through_incoming(self, line):
        try:
            if self.username + '!' in line[0]:
                pass
            elif line[0] == '353' or line[1] == '353':
                self.build_online_list(line)
            elif line[1] == '401':
                self.post_to_tab(line[3].lower(), line[4] + '\n')
            elif line[1] == 'QUIT':
                self.remove_on_quit(line)
            elif line[1] == "PRIVMSG" and line[3] == ':\x01ACTION':
                x = " ".join(line[4:])
                format_user1 = line[0].strip(':')
                finish_format = format_user1.split('!')
                user = finish_format[0]
                self.post_to_tab(line[2].lower(), '*' + user + ' ' + x + '\n')
            elif line[1] == "PRIVMSG":
                self.get_incoming_channel(line)
            elif line[1] == 'JOIN' and self.username not in line[0]:
                tab = line[2].split(':')
                user = line[0].split('!')[0].lstrip(":")
                self.add_online_user(user, tab[1])
            elif line[1] == 'PART' and self.username not in line[0]:
                tab = line[2].split(':')
                user = line[0].split('!')[0].lstrip(":")
                self.remove_online_user(user, tab[1])
            elif line[1] == 'NICK' and self.username not in line[2]:
                user = line[0].split('!')[0].lstrip(":")
                self.handle_name_change(user, line)
            elif line[1] == 'NOTICE' and line[2] == self.username:
                print(line)
                if '[' in line[3]:
                    get_tab = line[3].split('[')[1].split(']')
                    x = " ".join(line[4:])
                    self.post_to_tab(get_tab[0], x + '\n')
                else:
                    x = " ".join(line[4:])
                    self.post_message(x + '\n',
                                      self.tabs['Server Info']['textbox'])
                    self.n.select(self.tabs['Server Info']['tab'])
                    self.tabs['Server Info']['entry'].focus_force()
            elif line[1] == '328' or line[1] == '332' or line[1] == '333' or \
                    line[1] == '366':
                x = " ".join(line[3:])
                self.post_to_tab(line[3].lower(), x + '\n')
            elif ':' in line[0]:
                x = " ".join(line[3:])
                self.post_message(x + '\n',
                                  self.tabs['Server Info']['textbox'])
            else:
                tab = self.n.tab(self.n.select(), "text")
                more_users = [':foo', '353', self.username, '=', tab]
                for item in line:
                    more_users.append(item)
                self.iterate_through_incoming(more_users)
        except IndexError:
            pass

    def get_incoming_channel(self, line):
        if "#" in line[2]:
            channel = ""
            channel += line[0].split('!')[0].lstrip(':')
            x = " ".join(line[3:])
            self.post_to_tab(line[2].lower(), channel + ':>' + x.lstrip(':') +
                             '\n')
        else:
            message = line[3].lstrip(':')
            x = " ".join(line[4:])
            format_sender1 = line[0].strip(':')
            finish_format = format_sender1.split('!')
            user = finish_format[0]
            self.add_tab(user.lower(), 'pm')
            self.post_to_tab(user.lower(), user + ':>' + message + ' ' + x +
                             '\n')

    def add_tab(self, tab_name, tab_type):
        if tab_name not in self.tabs:
            self.build_tab(tab_name, tab_type)
        else:
            if (tab_name == self.n.tab(self.tabs[tab_name]['tab'], "text")
                    and self.n.tab(self.tabs[tab_name]['tab'],
                                   "state") == 'hidden' and tab_type ==
                    'channel'):
                self.n.tab(self.tabs[tab_name]['tab'], state='normal')
                self.n.select(self.tabs[tab_name]['tab'])
                self.tabs[tab_name]['online_users'].delete(1, 'end')
                self.tabs[tab_name]['textbox'].delete(0, 'end-1c')
                self.tabs[tab_name]['entry'].focus_force()
                self.client.join_channel(tab_name)
            elif (tab_name == self.n.tab(self.tabs[tab_name]['tab'], "text")
                  and self.n.tab(self.tabs[tab_name]['tab'], "state") ==
                  'normal' and tab_type == 'channel'):
                self.n.select(self.tabs[tab_name]['tab'])
                self.tabs[tab_name]['entry'].focus_force()

    def build_tab(self, tab_name, tab_type):
        tab_frame = ttk.Frame(self.n)
        tab_frame.grid(row=0, column=0, rowspan=2, sticky=N + S + E + W)

        receive_user = ScrolledText(tab_frame, height=24, width=47, wrap=WORD)
        receive_user.grid(row=0, column=0, padx=(10, 0), pady=(10, 5),
                          sticky=N + S + E + W)
        receive_user.config(state=DISABLED)

        pm_entry = ScrolledText(tab_frame, height=6, width=47, wrap=WORD)
        pm_entry.grid(row=1, column=0, padx=(10, 0), pady=(0, 10),
                      sticky=N + S + E + W)
        pm_entry.bind('<Return>', self.check_pm_commands)

        if tab_type == 'channel':
            pm_users_box = Listbox(tab_frame, width=12)
            pm_users_box.grid(row=0, column=1, rowspan=2, padx=(0, 10),
                              pady=(10, 10), sticky=N + S + E + W)
            pm_users_box.insert(0, 'Online [0]')

            self.tabs[tab_name] = {
                'tab': tab_frame,
                'textbox': receive_user,
                'entry': pm_entry,
                'online_users': pm_users_box
            }
            self.client.join_channel(tab_name)
        else:
            pm_close_button = Button(tab_frame, width=7, text='Close tab',
                                     command=self.remove_on_close)
            pm_close_button.grid(row=0, column=1, padx=(5, 5), pady=(5, 150),
                                 sticky=N + S + E + W)

            self.tabs[tab_name] = {
                'tab': tab_frame,
                'textbox': receive_user,
                'entry': pm_entry,
                'online_users': ''
            }

        Grid.rowconfigure(tab_frame, 0, weight=1)
        Grid.columnconfigure(tab_frame, 0, weight=1)

        self.n.add(tab_frame, text=tab_name)
        self.n.select(tab_frame)
        pm_entry.focus_force()

    def handle_name_change(self, user, line):
        tab_storage = []
        for tabs in self.tabs:
            if self.tabs[tabs]['online_users'] == '':
                pass
            else:
                tab_storage.append(tabs)
        for tabs in tab_storage:
            for item in self.tabs[tabs]['online_users'].get(0, 'end'):
                if user == item:
                    to_box = self.tabs[tabs]['textbox']
                    new_user = line[2].split(':')
                    index = self.tabs[tabs]['online_users'].get(0, END).index(
                        user)
                    self.tabs[tabs]['online_users'].delete(index)
                    self.tabs[tabs]['online_users'].insert(END, new_user[1])
                    self.post_message('*User %s is now known as %s' % (
                            user, new_user[1]) + '\n', to_box)

    def add_online_user(self, user, tab):
        tab_to_update = self.tabs[tab]['textbox']
        self.tabs[tab]['online_users'].insert(END, user)
        self.post_message('*User %s has joined the channel' % user + '\n',
                          tab_to_update)
        self.count_online(tab)

    def remove_online_user(self, user, tab):
        tab_to_update = self.tabs[tab.lower()]
        try:
            index = tab_to_update['online_users'].get(0, 'end').index(user)
            tab_to_update['online_users'].delete(
                index)
            self.post_message('User %s has left the channel' % user + '\n',
                              tab_to_update['textbox'])
            self.count_online(tab)
        except ValueError:
            self.post_message(
                '*User %s has left the channel' % user + '\n',
                tab_to_update['textbox'])
        try:
            index1 = tab_to_update['online_users'].get(0, 'end').index(
                '@' + user)
            tab_to_update['online_users'].delete(index1)
            self.post_message(
                '*User %s has left the channel' % user + '\n',
                tab_to_update['textbox'])
            self.count_online(tab)
        except ValueError:
            pass

    def remove_on_quit(self, line):
        tab_storage = []
        user = line[0].split('!')[0].strip(':')
        for tab in self.tabs:
            if self.tabs[tab]['online_users'] == '':
                pass
            else:
                tab_storage.append(tab)
        for tab in tab_storage:
            for item in self.tabs[tab]['online_users'].get(0, 'end'):
                if user == item:
                    to_box = self.tabs[tab]['textbox']
                    index = self.tabs[tab]['online_users'].get(0, END).index(
                        user)
                    self.tabs[tab]['online_users'].delete(index)
                    x = " ".join(line[2:])
                    self.post_message(
                        '*User %s has quit. Reason: %s' % (user, x) + '\n',
                        to_box)
            self.count_online(tab)

    def leave_channel(self):
        tab = self.n.tab(self.n.select(), "text")
        if tab == self.server:
            pass
        elif "No such channel" in self.tabs[tab]['textbox'].get("1.0",
                                                                'end-1c'):
            self.remove_on_close()
        elif self.tabs[tab]['online_users'] == '':
            self.remove_on_close()
        else:
            self.client.leave_channel(tab)
            self.remove_on_close()

    def remove_on_close(self):
        current_tab = self.n.tab(self.n.select(), "text")
        if current_tab in self.tabs and current_tab != self.server:
            if self.tabs[current_tab]['online_users'] == '':
                self.n.hide(self.n.select())
                current_tab = self.n.tab(self.n.select(), "text")
                self.tabs[current_tab]['entry'].focus_force()
            else:
                self.n.hide(self.n.select())
                current_tab = self.n.tab(self.n.select(), "text")
                self.tabs[current_tab]['entry'].focus_force()

    def build_online_list(self, line):
        try:
            if self.tabs[line[4].lower()]['online_users'] == '':
                pass
            else:
                users = []
                first_user = line[5].replace(':', '')
                users.append(first_user)
                for items in line[6:]:
                    users.append(items)
                for items in sorted(users):
                    self.tabs[line[4].lower()]['online_users'].insert(END,
                                                                      items)
                self.count_online(line[4].lower())
        except KeyError:
            pass

    def count_online(self, tab_name):
        user_count = self.tabs[tab_name]['online_users'].size()
        self.tabs[tab_name]['online_users'].delete(0)
        self.tabs[tab_name]['online_users'].insert(0, 'Online [%d]' % (
                user_count - 1))

    def post_to_tab(self, tab_name, message):
        if tab_name not in self.tabs:
            self.post_message('[' + tab_name + ' ' + message,
                              self.tabs["Server Info"]['textbox'])
        elif tab_name == self.n.tab(self.tabs[tab_name]['tab'], "text"):
            if "No such channel" in self.tabs[tab_name]['textbox'].get("1.0",
                                                                       'end-1c'
                                                                       ):
                pass
            else:
                self.n.tab(self.tabs[tab_name]['tab'], state='normal')
                self.post_message(message, self.tabs[tab_name][
                    'textbox'])

    @staticmethod
    def post_message(pm, window):
        window.config(state=NORMAL)
        window.insert(END, time.strftime("[%I:%M %p]") + pm)
        window.config(state=DISABLED)
        window.see(END)

    def save_settings_to_file(self, server, username, password):
        self.parser["DEFAULT"] = {
            "server": server,
            "username": username,
            "password": password
        }
        with open(SETTINGS_FILE, "w") as config:
            self.parser.write(config)

    @staticmethod
    def create_label_entry(parent, text, x, y, default_val="", show=None):
        Label(parent, text=text).grid(row=y, column=0, sticky=W, padx=x,
                                      pady=5)
        entry = Entry(parent, show=show)
        entry.grid(row=y, column=1, sticky=E + W, padx=x + 10)
        entry.insert(0, default_val)
        return entry

    @staticmethod
    def center_window(window, width, height):
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw - width) / 2
        y = (sh - height) / 2
        window.geometry('%dx%d+%d+%d' % (width, height, x, y))
        window.minsize(width, height)


if __name__ == '__main__':
    root = Tk()
    app = Window(root)
    root.mainloop()
