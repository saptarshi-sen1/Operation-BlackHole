# secure_wipe.py
import sys
from blackhole_core import secure_wipe_file

if len(sys.argv) < 2:
    print("Usage: python secure_wipe.py path_to_file")
else:
    path = sys.argv[1]
    ok = secure_wipe_file(path)
    print("Wipe OK:", ok)