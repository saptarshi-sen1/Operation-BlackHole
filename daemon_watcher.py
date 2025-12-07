# daemon_watcher.py
import time, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from blackhole_core import save_file_bytes, secure_wipe_file

WATCH_DIR = os.path.expanduser("~/Watched")
os.makedirs(WATCH_DIR, exist_ok=True)

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = event.src_path
        # small wait to ensure writing completed
        time.sleep(0.5)
        try:
            print("[watcher] New file detected:", path)
            with open(path, "rb") as f:
                data = f.read()
            outblack = save_file_bytes(os.path.basename(path), data)
            print("[watcher] Saved .black:", outblack)
            ok = secure_wipe_file(path)
            if ok:
                print("[watcher] Original securely removed:", path)
            else:
                print("[watcher] Could not securely wipe original; deleted normally.")
        except Exception as e:
            print("[watcher] Error processing file:", e)

def run_daemon():
    observer = Observer()
    handler = NewFileHandler()
    observer.schedule(handler, WATCH_DIR, recursive=False)
    observer.start()
    print("[watcher] Watching:", WATCH_DIR)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run_daemon()