#!/usr/bin/env python3
import os, io, json, subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import mimetypes

# Core imports
from blackhole_core import save_file_bytes, open_black_file, secure_wipe_file
import password_manager

WATCH_DIR = os.path.expanduser("~/Watched")
STORE_DIR = os.path.expanduser("~/.blackhole_store")

# ---------------------------
# SIMPLE AUTH POPUP
# ---------------------------
class AuthDialog(simpledialog.Dialog):
    def body(self, master):
        ttk.Label(master, text="Enter passphrase:").grid(row=0, column=0, padx=6, pady=6)
        self.box = ttk.Entry(master, show="*", width=30)
        self.box.grid(row=0, column=1, padx=6, pady=6)
        return self.box

    def apply(self):
        self.result = self.box.get()

# ---------------------------
# MAIN GUI
# ---------------------------
class BlackholeGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Operation Blackhole — GUI")
        self.geometry("1000x650")
        self._master_key_cache = None
        self.file_to_encrypt = None

        self.create_menu()
        self.create_widgets()
        self.refresh_list()

        # Ask to unlock at startup if wrapped exists
        try:
            if password_manager.get_wrapped_metadata():
                self.after(300, self.prompt_unlock_start)
        except:
            pass

    # ---------------------------
    # Menu
    # ---------------------------
    def create_menu(self):
        m = tk.Menu(self)
        self.config(menu=m)

        pm = tk.Menu(m, tearoff=0)
        pm.add_command(label="Enable/Set Passphrase", command=self.set_passphrase)
        pm.add_command(label="Change Passphrase", command=self.change_passphrase)
        pm.add_separator()
        pm.add_command(label="Show Wrapped Metadata", command=self.show_wrapped)
        pm.add_command(label="Export Wrapped Blob", command=self.export_wrapped)
        pm.add_command(label="Import Wrapped Blob", command=self.import_wrapped)
        m.add_cascade(label="Passphrase", menu=pm)

        tm = tk.Menu(m, tearoff=0)
        tm.add_command(label="Refresh List", command=self.refresh_list)
        m.add_cascade(label="Tools", menu=tm)

    # ---------------------------
    # Widgets
    # ---------------------------
    def create_widgets(self):
        left = ttk.Frame(self, padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Encrypt File", font=("Arial", 10, "bold")).pack(anchor="w")
        ttk.Button(left, text="Choose file", command=self.choose_file).pack(fill=tk.X, pady=4)
        ttk.Button(left, text="Encrypt to Watched", command=self.encrypt_to_watched).pack(fill=tk.X, pady=4)
        ttk.Separator(left).pack(fill=tk.X, pady=8)

        ttk.Label(left, text="Stored .black Files", font=("Arial", 10, "bold")).pack(anchor="w")
        self.listbox = tk.Listbox(left, width=40, height=22)
        self.listbox.pack(fill=tk.Y, pady=6)
        self.listbox.bind("<Double-Button-1>", lambda e: self.view_selected())

        btnf = ttk.Frame(left)
        btnf.pack(fill=tk.X)
        ttk.Button(btnf, text="View", command=self.view_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btnf, text="Restore", command=self.restore_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btnf, text="Delete", command=self.delete_selected).pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Separator(left).pack(fill=tk.X, pady=8)
        ttk.Button(left, text="Open Watched Folder", command=self.open_watched).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="Open Store Folder", command=self.open_store).pack(fill=tk.X, pady=2)

        # Right Panel
        right = ttk.Frame(self, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(right, text="Preview", font=("Arial", 12, "bold")).pack(anchor="w")
        self.preview_canvas = tk.Canvas(right, bg="black", height=360)
        self.preview_canvas.pack(fill=tk.X, pady=6)

        self.log = tk.Text(right, height=12)
        self.log.pack(fill=tk.BOTH, expand=True)

    # ---------------------------
    def log_msg(self, *parts):
        self.log.insert(tk.END, " ".join(map(str, parts)) + "\n")
        self.log.see(tk.END)

    # ---------------------------
    # Encrypt Workflow
    # ---------------------------
    def choose_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.file_to_encrypt = f
            self.log_msg("Selected:", f)

    def encrypt_to_watched(self):
        if not self.file_to_encrypt:
            messagebox.showinfo("Info", "Select a file first")
            return
        os.makedirs(WATCH_DIR, exist_ok=True)
        dest = os.path.join(WATCH_DIR, os.path.basename(self.file_to_encrypt))
        with open(self.file_to_encrypt, "rb") as a, open(dest, "wb") as b:
            b.write(a.read())
        self.log_msg("Copied to Watched:", dest)
        messagebox.showinfo("Done", "Watcher will encrypt it soon.")

    # ---------------------------
    # List .black files
    # ---------------------------
    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        os.makedirs(STORE_DIR, exist_ok=True)
        for f in sorted(os.listdir(STORE_DIR)):
            if f.endswith(".black"):
                self.listbox.insert(tk.END, f)
        self.log_msg("Refreshed list.")

    def selected_path(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        name = self.listbox.get(sel[0])
        return os.path.join(STORE_DIR, name)

    # ---------------------------
    # Passphrase unlock
    # ---------------------------
    def prompt_unlock_start(self):
        if messagebox.askyesno("Passphrase detected", "Unlock now?"):
            self.unlock_interactive()

    def ensure_master_unlocked(self):
        if password_manager.get_wrapped_metadata() and not self._master_key_cache:
            return self.unlock_interactive()
        return True

    def unlock_interactive(self):
        dlg = AuthDialog(self, title="Enter Passphrase")
        if not dlg.result:
            return False
        try:
            self._master_key_cache = password_manager.unwrap_master_from_passphrase(dlg.result)
            self.log_msg("Master key unlocked.")
            return True
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return False

    # ---------------------------
    # View
    # ---------------------------
    def view_selected(self):
        path = self.selected_path()
        if not path:
            return
        if not self.ensure_master_unlocked():
            return
        try:
            data = open_black_file(path, master_key=self._master_key_cache)
            with open(path, "r") as f:
                meta = json.load(f)
            mime = meta.get("mime") or mimetypes.guess_type(meta.get("orig_name", ""))[0]

            if mime and mime.startswith("image"):
                self.show_image(data)
            else:
                self.show_text_preview(data.decode(errors="replace"))

        except Exception as e:
            self.log_msg("View error:", e)
            messagebox.showerror("Error", str(e))

    def show_image(self, data):
        bio = io.BytesIO(data)
        img = Image.open(bio)
        w, h = img.size
        max_w = self.preview_canvas.winfo_width()
        max_h = 360
        scale = min(max_w / w, max_h / h, 1)
        img = img.resize((int(w * scale), int(h * scale)))
        self.imgtk = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(max_w // 2, max_h // 2, image=self.imgtk, anchor="center")
        bio.close()

    def show_text_preview(self, txt):
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(10, 10, anchor="nw", text=txt[:800], fill="white", font=("Courier", 10))

    # ---------------------------
    # Restore
    # ---------------------------
    def restore_selected(self):
        path = self.selected_path()
        if not path:
            return
        if not self.ensure_master_unlocked():
            return

        with open(path, "r") as f:
            meta = json.load(f)

        out = filedialog.asksaveasfilename(initialfile=meta.get("orig_name", "restored"))
        if not out:
            return

        try:
            data = open_black_file(path, master_key=self._master_key_cache)
            with open(out, "wb") as f:
                f.write(data)
            self.log_msg("Restored:", out)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------------------
    # Delete
    # ---------------------------
    def delete_selected(self):
        path = self.selected_path()
        if not path:
            return
        if not messagebox.askyesno("Confirm", "Delete permanently?"):
            return
        secure_wipe_file(path)
        self.refresh_list()

    # ---------------------------
    # Open folders (WSL safe)
    # ---------------------------
    
    def open_watched(self):
        try:
            win = subprocess.check_output(["wslpath", "-w", WATCH_DIR]).decode().strip()
            subprocess.Popen(["explorer.exe", win])
        except Exception as e:
            self.log_msg("Could not open Watched:", e)

    
    def open_store(self):
        try:
            win = subprocess.check_output(["wslpath", "-w", STORE_DIR]).decode().strip()
            subprocess.Popen(["explorer.exe", win])
        except Exception as e:
            self.log_msg("Could not open Store:", e)

    def _open_folder(self, folder):
        os.makedirs(folder, exist_ok=True)
        try:
            subprocess.Popen(["xdg-open", folder])
            return
        except:
            pass

        # WSL fallback → Windows Explorer
        try:
            ver = open("/proc/version").read().lower()
            if "microsoft" in ver or "wsl" in ver:
                win = subprocess.check_output(["wslpath", "-w", folder]).decode().strip()
                subprocess.Popen(["explorer.exe", win])
                return
        except:
            pass

        messagebox.showinfo("Folder", f"Folder path: {folder}")

    # ---------------------------
    # Passphrase menu functions
    # ---------------------------
    def set_passphrase(self):
        p1 = simpledialog.askstring("Passphrase", "Enter new passphrase:", show="*")
        if not p1:
            return
        p2 = simpledialog.askstring("Confirm", "Confirm:", show="*")
        if p1 != p2:
            messagebox.showerror("Error", "Mismatch")
            return
        password_manager.enable_passphrase(p1)
        messagebox.showinfo("Done", "Passphrase enabled.")

    def change_passphrase(self):
        old = simpledialog.askstring("Current", "Current passphrase:", show="*")
        new = simpledialog.askstring("New", "New passphrase:", show="*")
        new2 = simpledialog.askstring("Confirm", "Confirm:", show="*")
        if new != new2:
            messagebox.showerror("Error", "Mismatch")
            return
        password_manager.change_passphrase(old, new)
        messagebox.showinfo("Done", "Passphrase changed.")

    def show_wrapped(self):
        blob = password_manager.get_wrapped_metadata()
        if not blob:
            messagebox.showinfo("Info", "No wrapped metadata.")
            return
        top = tk.Toplevel(self)
        top.title("Wrapped Metadata")
        t = tk.Text(top, wrap="none")
        t.insert("1.0", json.dumps(blob, indent=2))
        t.pack(fill=tk.BOTH, expand=True)

    def export_wrapped(self):
        blob = password_manager.get_wrapped_metadata()
        if not blob:
            messagebox.showinfo("Info", "Nothing to export.")
            return
        out = filedialog.asksaveasfilename(defaultextension=".json")
        if not out:
            return
        password_manager.export_wrapped_backup(out)
        messagebox.showinfo("Done", "Exported.")

    def import_wrapped(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        password_manager.import_wrapped_backup(path)
        messagebox.showinfo("Done", "Imported.")

# ---------------------------
if __name__ == "__main__":
    BlackholeGUI().mainloop()
