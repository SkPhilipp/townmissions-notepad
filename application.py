import tkinter

import pywintypes
import win32api
import win32con


class Application:
    def __init__(self):
        self.root = tkinter.Tk()
        self.text = tkinter.StringVar()
        self.text.set("")
        self.label = tkinter.Label(self.root, textvariable=self.text, font=('Consolas', '10'), fg='white', bg='black', )
        self.label.master.overrideredirect(True)
        self.label.master.geometry("+50+50")
        self.label.master.lift()
        self.label.master.wm_attributes("-topmost", True)
        self.label.master.wm_attributes("-disabled", True)
        self.label.master.wm_attributes("-alpha", "0.7")
        self.label.pack(fill='both')
        window_handle = pywintypes.HANDLE(int(self.label.master.frame(), 16))
        win32api.SetWindowLong(window_handle, win32con.GWL_EXSTYLE,
                               win32con.WS_EX_COMPOSITED | win32con.WS_EX_LAYERED | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT)
        self.hidden = False

    def update(self, text):
        # manual padding, can be resolved by making alignment and styling of label work
        max_len = 0
        for line in text.splitlines():
            max_len = len(line) if len(line) > max_len else max_len
        lines = []
        for line in text.splitlines():
            len_diff = max_len - len(line)
            lines.append(' ' + line + (' ' * len_diff) + ' ')
        self.text.set('\n'.join(lines))

    def show(self):
        self.root.deiconify()
        self.hidden = False

    def hide(self):
        self.root.withdraw()
        self.hidden = True

    def join(self):
        self.root.mainloop()

    def is_hidden(self):
        return self.hidden
