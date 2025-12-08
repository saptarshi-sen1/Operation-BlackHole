import subprocess, os

# modify GUI file
path = "encrypt_decrypt_gui.py"
text = open(path).read()

# new forced-explorer functions
new_open_watched = """
    def open_watched(self):
        try:
            win = subprocess.check_output(["wslpath", "-w", WATCH_DIR]).decode().strip()
            subprocess.Popen(["explorer.exe", win])
        except Exception as e:
            self.log_msg("Could not open Watched:", e)
"""

new_open_store = """
    def open_store(self):
        try:
            win = subprocess.check_output(["wslpath", "-w", STORE_DIR]).decode().strip()
            subprocess.Popen(["explorer.exe", win])
        except Exception as e:
            self.log_msg("Could not open Store:", e)
"""

# replace old definitions
import re
text = re.sub(r"def open_watched.*?def open_store", new_open_watched + "\n    " + "def open_store", text, flags=re.S)
text = re.sub(r"def open_store.*?def", new_open_store + "\n    def", text, flags=re.S)

open(path, "w").write(text)
print("Patched: GUI now always uses Windows Explorer (no xdg-open, no Linux file-manager)")
