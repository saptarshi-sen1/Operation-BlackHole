# restore_file.py
import json, base64, os, getpass
from blackhole_core import open_black_file

STORE = os.path.expanduser("~/.blackhole_store")

def list_black_files():
    files = [os.path.join(STORE, f) for f in os.listdir(STORE) if f.endswith(".black")]
    return sorted(files)

def main():
    files = list_black_files()
    if not files:
        print("No .black files found.")
        return

    print("\nAvailable encrypted files:")
    for i, f in enumerate(files):
        print(f"{i}) {os.path.basename(f)}")

    idx = int(input("\nEnter index of file to restore: "))
    path = files[idx]

    # Load metadata to get original filename
    with open(path, "r") as fh:
        meta = json.load(fh)
    orig_name = meta.get("orig_name", "restored_output")

    print(f"\nRestoring original file: {orig_name}")

    # Reconstruct the original data
    data = open_black_file(path)

    # Let user choose restore destination
    out_path = input(f"Enter output path (default: {orig_name}): ").strip()
    if out_path == "":
        out_path = orig_name

    # Prevent accidental overwrite
    if os.path.exists(out_path):
        confirm = input("File exists. Overwrite? (y/N): ").lower()
        if confirm != "y":
            print("Restore cancelled.")
            return

    with open(out_path, "wb") as f:
        f.write(data)

    print(f"\n✔ File successfully restored to: {out_path}")
    print("You now have the decrypted, original file back on disk.")

if __name__ == "__main__":
    main()