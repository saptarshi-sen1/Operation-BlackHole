#!/usr/bin/env python3
# manage_passphrase.py
import argparse
import getpass
import json
from password_manager import (
    enable_passphrase, change_passphrase, verify_passphrase,
    get_wrapped_metadata, unwrap_master_from_passphrase,
    export_wrapped_backup, import_wrapped_backup
)

def cmd_set(args):
    pwd = getpass.getpass("Enter new passphrase: ")
    pwd2 = getpass.getpass("Confirm new passphrase: ")
    if pwd != pwd2:
        print("Passphrases do not match. Abort.")
        return
    enable_passphrase(pwd)
    print("Passphrase enabled and wrapped master saved. (Raw master not deleted automatically.)")

def cmd_change(args):
    old = getpass.getpass("Enter current passphrase: ")
    new = getpass.getpass("Enter new passphrase: ")
    new2 = getpass.getpass("Confirm new passphrase: ")
    if new != new2:
        print("New passphrases do not match. Abort.")
        return
    try:
        change_passphrase(old, new)
        print("Passphrase changed successfully.")
    except Exception as e:
        print("Failed to change passphrase:", e)

def cmd_verify(args):
    pwd = getpass.getpass("Enter passphrase to verify: ")
    ok = verify_passphrase(pwd)
    print("Passphrase valid:", ok)

def cmd_show(args):
    blob = get_wrapped_metadata()
    if not blob:
        print("No wrapped passphrase metadata found.")
        return
    print("WARNING: The following values include ciphertext. Do NOT share the wrapped_master with untrusted parties.")
    print(json.dumps(blob, indent=2))

def cmd_unwrap(args):
    pwd = getpass.getpass("Enter passphrase to unwrap master key: ")
    try:
        master = unwrap_master_from_passphrase(pwd)
        print("SUCCESS: master key recovered (hex):")
        print(master.hex())
        print("\nWARNING: This is the raw master key. Keep it secret and do NOT share.")
    except Exception as e:
        print("Failed to unwrap master key:", e)

def cmd_export(args):
    path = args.path
    export_wrapped_backup(path)
    print("Exported wrapped blob to:", path)

def cmd_import(args):
    path = args.path
    import_wrapped_backup(path)
    print("Imported wrapped blob from:", path)

def main():
    p = argparse.ArgumentParser(description="Manage passphrase for Operation Blackhole")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("set", help="Enable passphrase (wrap current master key)")

    sub.add_parser("change", help="Change existing passphrase")

    sub.add_parser("verify", help="Verify a passphrase")

    sub.add_parser("show", help="Display wrapped metadata (ciphertext, salt, kdf params)")

    sub.add_parser("unwrap", help="Attempt to unwrap master key and show hex (DANGEROUS)")

    exp = sub.add_parser("export", help="Export wrapped blob to a file (backup)")
    exp.add_argument("path", help="destination file path")

    imp = sub.add_parser("import", help="Import wrapped blob from file")
    imp.add_argument("path", help="source file path")

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return

    if args.cmd == "set":
        cmd_set(args)
    elif args.cmd == "change":
        cmd_change(args)
    elif args.cmd == "verify":
        cmd_verify(args)
    elif args.cmd == "show":
        cmd_show(args)
    elif args.cmd == "unwrap":
        cmd_unwrap(args)
    elif args.cmd == "export":
        cmd_export(args)
    elif args.cmd == "import":
        cmd_import(args)

if __name__ == "__main__":
    main()