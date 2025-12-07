# viewer.py
import os, glob, io, json, subprocess
from blackhole_core import open_black_file, secure_wipe_file
from PIL import Image, ImageTk
import tkinter as tk
import mimetypes

STORE_DIR = os.path.expanduser("~/.blackhole_store")

def list_black_files():
    return sorted(glob.glob(os.path.join(STORE_DIR, "*.black")))

def read_metadata(path):
    with open(path, "r") as f:
        payload = json.load(f)
    return payload.get("orig_name","unknown"), payload

def view_image_bytes(data_bytes):
    # display in a Tkinter window from memory (no external temp files)
    root = tk.Tk()
    root.title("Blackhole Viewer - Secure Preview")
    # Prevent screenshots by placing window always on top is limited — Tkinter cannot block OS screenshots.
    bio = io.BytesIO(data_bytes)
    img = Image.open(bio)
    tkimg = ImageTk.PhotoImage(img)
    lbl = tk.Label(root, image=tkimg)
    lbl.pack()
    # Auto-close after 20 seconds for safety
    def close_after():
        root.destroy()
    root.after(20000, close_after)  # 20000 ms = 20 s
    root.mainloop()
    bio.close()

def write_to_shm_and_open(data_bytes, filename):
    shm_dir = "/dev/shm"
    if not os.path.isdir(shm_dir):
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False)
        path = tmp.name
        tmp.write(data_bytes)
        tmp.close()
    else:
        path = os.path.join(shm_dir, "bh_" + filename)
        with open(path, "wb") as f:
            f.write(data_bytes)
            f.flush()
            os.fsync(f.fileno())
    # open with default program
    try:
        subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print("Failed to open automatically. Path:", path, "Error:", e)
        print("You can manually open and then close when done.")
    input("Press Enter after you finish viewing to wipe temporary file...")
    secure_wipe_file(path)

def main():
    files = list_black_files()
    if not files:
        print("No protected files found.")
        return
    for i,f in enumerate(files):
        orig_name, meta = read_metadata(f)
        print(f"{i}: {os.path.basename(f)}  -> original name: {orig_name}")
    idx = input("Enter file index to view (or q to quit): ").strip()
    if idx.lower() == 'q':
        return
    try:
        idx = int(idx)
    except:
        print("Invalid input.")
        return
    path = files[idx]
    orig_name, meta = read_metadata(path)
    mime = meta.get("mime")
    if not mime:
        mime, _ = mimetypes.guess_type(orig_name)
    print("Decrypting ...")
    data = open_black_file(path)
    if mime and mime.startswith("image"):
        view_image_bytes(data)
    else:
        print("Opening file in RAM-backed temp:", orig_name)
        write_to_shm_and_open(data, orig_name)
    # overwrite and delete Python references
    del data
    print("Done.")

if _name_ == "_main_":
    main()