import tkinter as tk
from tkinter import simpledialog, messagebox
import hashlib
import sys

# ----- CHANGE THIS -----
# Store a hashed password, not plain text
STORED_HASH = "e10adc3949ba59abbe56e057f20f883e"  # default is "123456"
# ------------------------

def ask_password():
    root = tk.Tk()
    root.withdraw()  # hide main window

    pwd = simpledialog.askstring("Authentication", "Enter password:", show="*")

    if pwd is None:
        sys.exit(0)

    # hash entered password
    pwd_hash = hashlib.md5(pwd.encode()).hexdigest()

    if pwd_hash != STORED_HASH:
        messagebox.showerror("Error", "Incorrect password.")
        sys.exit(0)

    # correct
    root.destroy()