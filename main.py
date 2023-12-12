from tkinter import Tk
from src import Ui


def main():
    root = Tk()
    app = Ui.Window(root)
    root.mainloop()


if __name__ == '__main__':
    main()
