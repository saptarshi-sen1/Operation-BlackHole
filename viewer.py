# viewer.py
import os
import glob
import io
import json
import subprocess
import mimetypes
import tkinter as tk
from PIL import Image, ImageTk

from blackhole_core import open_black_file, secure_wipe_file

STORE_DIR = os.path.expanduser("~/.blackhole_store")


def list_black_files():
    return sorted(glob.glob(os.path.join(STORE_DIR, "*.black")))


def read_metadata(path):
    with open(path, "r") as f:
        meta = json.load(f)
    orig = (
        meta.get("orig_name")
        or meta.get("original_name")
        or meta.get("filename")
        or "file"
    )
    return orig, meta


def view_image_bytes(data_bytes):
    root = tk.Tk()
    root.title("Blackhole Secure Preview (RAM only)")

    bio = io.BytesIO(data_bytes)
    img = Image.open(bio)
    tkimg = ImageTk.PhotoImage(img)

    lbl = tk.Label(root, image=tkimg)
    lbl.pack()

    root.after(20000, root.destroy)  # auto close after 20 sec
    root.mainloop()
    bio.close()


def open_via_windows(path):
    win_path = subprocess.check_output(
        ["wslpath", "-w", path],
        text=True
    ).strip()
    subprocess.Popen(["explorer.exe", win_path])


def write_to_shm_and_open(data_bytes, filename):
    name, ext = os.path.splitext(filename)
    if not ext:
        ext = ".bin"

    path = os.path.join("/dev/shm", f"bh_preview_{name}{ext}")

    with open(path, "wb") as f:
        f.write(data_bytes)
        f.flush()
        os.fsync(f.fileno())

    print("Opening securely via Windows:", path)
    open_via_windows(path)

    input("Press Enter after viewing to securely wipe preview...")
    secure_wipe_file(path)


def main():
    files = list_black_files()
    if not files:
        print("No protected files found.")
        return

    for i, f in enumerate(files):
        orig, _ = read_metadata(f)
        print(f"{i}: {os.path.basename(f)} → {orig}")

    choice = input("Select file index (or q): ").strip()
    if choice.lower() == "q":
        return

    try:
        idx = int(choice)
    except ValueError:
        print("Invalid input.")
        return

    path = files[idx]
    orig_name, meta = read_metadata(path)

    mime = meta.get("mime") or mimetypes.guess_type(orig_name)[0]

    print("Decrypting...")
    data = open_black_file(path)

    if mime and mime.startswith("image"):
        view_image_bytes(data)
    else:
        write_to_shm_and_open(data, orig_name)

    del data
    print("Done.")


if __name__ == "__main__":
    main()