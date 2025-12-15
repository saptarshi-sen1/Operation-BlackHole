import os
import io
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import mimetypes
import subprocess

from blackhole_core import open_black_file, secure_wipe_file

WATCH_DIR = os.path.expanduser("~/Watched")
STORE_DIR = os.path.expanduser("~/.blackhole_store")


def open_via_windows(path):
    win_path = subprocess.check_output(
        ["wslpath", "-w", path],
        text=True
    ).strip()
    subprocess.Popen(["explorer.exe", win_path])


class BlackholeGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Operation Blackhole — Secure File Vault")
        self.geometry("900x600")
        self.create_widgets()
        self.refresh_list()

    def create_widgets(self):
        left = ttk.Frame(self, padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Encrypt").pack(anchor=tk.W)
        ttk.Button(left, text="Choose File", command=self.choose_file).pack(fill=tk.X)
        ttk.Button(left, text="Encrypt via Watched", command=self.encrypt_to_watched).pack(fill=tk.X, pady=5)

        ttk.Separator(left).pack(fill=tk.X, pady=8)

        ttk.Label(left, text="Encrypted Files").pack(anchor=tk.W)
        self.listbox = tk.Listbox(left, width=40, height=20)
        self.listbox.pack(fill=tk.Y, pady=5)
        self.listbox.bind("<Double-Button-1>", lambda e: self.view_selected())

        btns = ttk.Frame(left)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Refresh", command=self.refresh_list).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btns, text="View", command=self.view_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btns, text="Restore", command=self.restore_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btns, text="Delete", command=self.delete_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Separator(left).pack(fill=tk.X, pady=8)
        ttk.Button(left, text="Open Watched", command=lambda: open_via_windows(WATCH_DIR)).pack(fill=tk.X)
        ttk.Button(left, text="Open Store", command=lambda: open_via_windows(STORE_DIR)).pack(fill=tk.X)

        right = ttk.Frame(self, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(right, bg="black", height=320)
        self.canvas.pack(fill=tk.X)

        self.log = tk.Text(right, height=10)
        self.log.pack(fill=tk.BOTH, expand=True)

    def log_msg(self, *msg):
        self.log.insert(tk.END, " ".join(map(str, msg)) + "\n")
        self.log.see(tk.END)

    def choose_file(self):
        self.file = filedialog.askopenfilename()
        if self.file:
            self.log_msg("Selected:", self.file)

    def encrypt_to_watched(self):
        if not hasattr(self, "file"):
            messagebox.showinfo("Info", "Choose a file first")
            return
        os.makedirs(WATCH_DIR, exist_ok=True)
        dst = os.path.join(WATCH_DIR, os.path.basename(self.file))
        with open(self.file, "rb") as s, open(dst, "wb") as d:
            d.write(s.read())
        self.log_msg("Copied to Watched:", dst)

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        os.makedirs(STORE_DIR, exist_ok=True)
        for f in sorted(os.listdir(STORE_DIR)):
            if f.endswith(".black"):
                self.listbox.insert(tk.END, f)
        self.log_msg("Refreshed list")

    def get_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return os.path.join(STORE_DIR, self.listbox.get(sel[0]))

    def view_selected(self):
        path = self.get_selected()
        if not path:
            return

        with open(path) as f:
            meta = json.load(f)

        orig = (
            meta.get("orig_name")
            or meta.get("original_name")
            or meta.get("filename")
            or "file"
        )

        mime = meta.get("mime") or mimetypes.guess_type(orig)[0]
        data = open_black_file(path)

        if mime and mime.startswith("image"):
            self.show_image(data)
        else:
            self.open_external(data, orig)

    def show_image(self, data):
        bio = io.BytesIO(data)
        img = Image.open(bio)

        img = img.resize((600, 320), Image.Resampling.LANCZOS)
        self.tkimg = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(300, 160, image=self.tkimg)

    def open_external(self, data, name):
        base, ext = os.path.splitext(name)
        if not ext:
            ext = ".bin"

        path = f"/dev/shm/bh_preview_{base}{ext}"

        with open(path, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        open_via_windows(path)
        self.log_msg("Opened via Windows:", path)

    def restore_selected(self):
        path = self.get_selected()
        if not path:
            return
        data = open_black_file(path)
        out = filedialog.asksaveasfilename()
        if out:
            with open(out, "wb") as f:
                f.write(data)
            messagebox.showinfo("Restored", out)

    def delete_selected(self):
        path = self.get_selected()
        if path and messagebox.askyesno("Confirm", "Delete permanently?"):
            secure_wipe_file(path)
            self.refresh_list()


if __name__ == "__main__":
    app = BlackholeGUI()
    app.mainloop()