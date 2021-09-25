import sys
from threading import Event, Thread
from tkinter import Tk, ttk
from urllib.request import urlretrieve

def downloadFile(url, filename):
    root = progressbar = quit_id = None
    ready = Event()
    def reporthook(blocknum, blocksize, totalsize):
        nonlocal quit_id
        if blocknum == 0: # started downloading
            def guiloop():
                nonlocal root, progressbar
                root = Tk()
                root.withdraw() # hide
                progressbar = ttk.Progressbar(root, length=400)
                progressbar.grid()
                # show progress bar if the download takes more than .5 seconds
                root.after(500, root.deiconify)
                ready.set() # gui is ready
                root.mainloop()
            Thread(target=guiloop).start()
        ready.wait(1) # wait until gui is ready
        percent = blocknum * blocksize * 1e2 / totalsize # assume totalsize > 0
        if quit_id is None:
            root.title('%%%.0f %s' % (percent, filename,))
            progressbar['value'] = percent # report progress
            if percent >= 100:  # finishing download
                quit_id = root.after(0, root.destroy) # close GUI

    return urlretrieve(url, filename, reporthook)
