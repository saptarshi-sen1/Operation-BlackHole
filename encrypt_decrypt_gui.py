import os
import io
import json
import base64
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import mimetypes
import subprocess

from blackhole_core import save_file_bytes, open_black_file, secure_wipe_file, STORE_DIR

WATCH_DIR = os.path.expanduser("~/Watched")
STORE_DIR = os.path.expanduser("~/.blackhole_store")

class BlackholeGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Operation Blackhole — Encrypt / Decrypt GUI")
        self.geometry("900x600")
        self.create_widgets()
        self.refresh_list()

    def create_widgets(self):
        # Left frame - controls
        left = ttk.Frame(self, padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Encrypt (convert to .black)").pack(anchor=tk.W)
        ttk.Button(left, text="Choose file to encrypt", command=self.choose_file_to_encrypt).pack(fill=tk.X, pady=5)
        ttk.Button(left, text="Encrypt and move original to Watched", command=self.encrypt_to_watched).pack(fill=tk.X)
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        ttk.Label(left, text="Encrypted files (.black)").pack(anchor=tk.W, pady=(8,0))
        self.listbox = tk.Listbox(left, width=40, height=20)
        self.listbox.pack(fill=tk.Y, pady=5)
        self.listbox.bind('<Double-Button-1>', lambda e: self.view_selected())

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_list).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="View", command=self.view_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Restore", command=self.restore_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Delete", command=self.delete_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        ttk.Button(left, text="Open Watched Folder", command=self.open_watched).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Open Store Folder", command=self.open_store).pack(fill=tk.X, pady=2)

        # Right frame - preview and logs
        right = ttk.Frame(self, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.preview_label = ttk.Label(right, text="Preview", font=(None, 12, 'bold'))
        self.preview_label.pack(anchor=tk.W)
        self.preview_canvas = tk.Canvas(right, bg='black', height=320)
        self.preview_canvas.pack(fill=tk.X, pady=5)

        self.log = tk.Text(right, height=10)
        self.log.pack(fill=tk.BOTH, expand=True)

    def log_msg(self, *parts):
        self.log.insert(tk.END, ' '.join(map(str, parts)) + '\n')
        self.log.see(tk.END)

    def choose_file_to_encrypt(self):
        path = filedialog.askopenfilename(title='Select file to encrypt')
        if path:
            self.file_to_encrypt = path
            self.log_msg('Selected to encrypt:', path)

    def encrypt_to_watched(self):
        # If user selected a file, copy it to WATCH_DIR to let watcher process
        if not hasattr(self, 'file_to_encrypt') or not self.file_to_encrypt:
            messagebox.showinfo('Info', 'Choose a file first (Choose file to encrypt)')
            return
        try:
            os.makedirs(WATCH_DIR, exist_ok=True)
            dest = os.path.join(WATCH_DIR, os.path.basename(self.file_to_encrypt))
            with open(self.file_to_encrypt, 'rb') as src, open(dest, 'wb') as dst:
                dst.write(src.read())
            self.log_msg('Copied to Watched for auto-encryption:', dest)
            messagebox.showinfo('Done', 'File copied to Watched folder. The watcher will encrypt it shortly.')
        except Exception as e:
            self.log_msg('Error copying to Watched:', e)
            messagebox.showerror('Error', str(e))

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        os.makedirs(STORE_DIR, exist_ok=True)
        files = sorted([f for f in os.listdir(STORE_DIR) if f.endswith('.black')])
        for f in files:
            self.listbox.insert(tk.END, f)
        self.log_msg('Refreshed list —', len(files), 'items')

    def get_selected_path(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo('Info', 'Select a .black file from the list')
            return None
        name = self.listbox.get(sel[0])
        return os.path.join(STORE_DIR, name)

    def view_selected(self):
        path = self.get_selected_path()
        if not path: return
        self.log_msg('Viewing:', path)
        try:
            # reconstruct bytes
            data = open_black_file(path)
            # try to detect mime
            with open(path, 'r') as f:
                meta = json.load(f)
            mime = meta.get('mime') or mimetypes.guess_type(meta.get('orig_name',''))[0]
            if mime and mime.startswith('image'):
                self.show_image(data)
            elif mime and mime.startswith('text'):
                txt = data.decode(errors='replace')
                self.show_text_preview(txt)
            else:
                # write to /dev/shm and open
                tmp = os.path.join('/dev/shm', 'bh_preview_' + os.path.basename(path))
                with open(tmp, 'wb') as f:
                    f.write(data)
                    f.flush(); os.fsync(f.fileno())
                subprocess.Popen(['xdg-open', tmp])
                self.log_msg('Opened in external app from /dev/shm:', tmp)
        except Exception as e:
            self.log_msg('View error:', e)
            messagebox.showerror('Error', str(e))

    def show_image(self, data_bytes):
        try:
            bio = io.BytesIO(data_bytes)
            img = Image.open(bio)
            # resize to fit canvas
            w, h = img.size
            cw = self.preview_canvas.winfo_width() or 800
            max_h = 320
            scale = min(1, cw / w, max_h / h)
            new_size = (int(w*scale), int(h*scale))
            img = img.resize(new_size, Image.ANTIALIAS)
            self.imgtk = ImageTk.PhotoImage(img)
            self.preview_canvas.delete('all')
            self.preview_canvas.create_image(cw//2, max_h//2, image=self.imgtk, anchor='center')
            self.log_msg('Image preview shown')
            bio.close()
        except Exception as e:
            self.log_msg('Image preview failed:', e)

    def show_text_preview(self, txt):
        self.preview_canvas.delete('all')
        self.preview_canvas.create_text(10,10, anchor='nw', text=txt[:400], fill='white', font=('Courier', 10), width=self.preview_canvas.winfo_width()-20)
        self.log_msg('Text preview shown')

    def restore_selected(self):
        path = self.get_selected_path()
        if not path: return
        # load meta for default name
        with open(path, 'r') as f:
            meta = json.load(f)
        default = os.path.expanduser('~/' + meta.get('orig_name', 'restored'))
        out = filedialog.asksaveasfilename(title='Restore to (choose filename)', initialfile=os.path.basename(default), initialdir=os.path.dirname(default))
        if not out:
            return
        try:
            data = open_black_file(path)
            with open(out, 'wb') as f:
                f.write(data)
            self.log_msg('Restored to:', out)
            messagebox.showinfo('Restored', f'Restored to {out}')
        except Exception as e:
            self.log_msg('Restore error:', e)
            messagebox.showerror('Error', str(e))

    def delete_selected(self):
        path = self.get_selected_path()
        if not path: return
        if not messagebox.askyesno('Confirm', 'Permanently delete selected .black file?'):
            return
        ok = secure_wipe_file(path)
        if ok:
            self.log_msg('Deleted:', path)
            self.refresh_list()
            messagebox.showinfo('Deleted', 'File deleted securely')
        else:
            self.log_msg('Delete failed:', path)
            messagebox.showerror('Error', 'Could not delete file')

    def open_watched(self):
        os.makedirs(WATCH_DIR, exist_ok=True)
        subprocess.Popen(['xdg-open', WATCH_DIR])

    def open_store(self):
        os.makedirs(STORE_DIR, exist_ok=True)
        subprocess.Popen(['xdg-open', STORE_DIR])

if __name__ == '__main__':
    app = BlackholeGUI()
    app.mainloop()