# password_manager.py
"""
Password-based wrapping / unwrapping of the master key.
Stores wrapped master blob in keyring (service: operation_blackhole_wrapped_master)
or in a fallback JSON file: ~/.blackhole_store/wrapped_master.json
Provides functions:
- enable_passphrase(passphrase)
- change_passphrase(old, new)
- verify_passphrase(passphrase) -> bool
- unwrap_master_from_passphrase(passphrase) -> bytes (raises on failure)
- get_wrapped_metadata() -> dict (safe-to-display fields: salt (b64), iv (b64), wrapped_master (b64), kdf_params)
- remove_raw_master_key() -> deletes the unwrapped master stored via key_manager (if present) — used after enabling passphrase
"""

import os
import json
import base64
from typing import Optional, Dict
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets

# storage targets
KEYRING_SERVICE = "operation_blackhole_wrapped_master"
FALLBACK_PATH = os.path.expanduser("~/.blackhole_store/wrapped_master.json")

# import your existing key_manager to get/generate the current raw master
try:
    from key_manager import get_master_key, generate_master_key
    KEY_MANAGER_AVAILABLE = True
except Exception:
    KEY_MANAGER_AVAILABLE = False

def _derive_key(passphrase: bytes, salt: bytes, n: int, r: int, p: int, length: int = 32) -> bytes:
    kdf = Scrypt(salt=salt, length=length, n=n, r=r, p=p)
    return kdf.derive(passphrase)

def _store_blob_in_keyring(blob_json: dict):
    try:
        import keyring
        keyring.set_password(KEYRING_SERVICE, os.getlogin(), json.dumps(blob_json))
        return True
    except Exception:
        return False

def _read_blob_from_keyring() -> Optional[dict]:
    try:
        import keyring
        raw = keyring.get_password(KEYRING_SERVICE, os.getlogin())
        if not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None

def _write_fallback(blob_json: dict):
    os.makedirs(os.path.dirname(FALLBACK_PATH), exist_ok=True)
    tmp = FALLBACK_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(blob_json, f)
    os.replace(tmp, FALLBACK_PATH)
    try:
        os.chmod(FALLBACK_PATH, 0o600)
    except Exception:
        pass

def _read_fallback() -> Optional[dict]:
    if not os.path.exists(FALLBACK_PATH):
        return None
    try:
        with open(FALLBACK_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return None

def get_wrapped_metadata() -> Optional[Dict]:
    """
    Return wrapped metadata (dictionary) if present. Keys:
    salt (b64), iv (b64), wrapped_master (b64), kdf_params (dict)
    """
    blob = _read_blob_from_keyring()
    if blob:
        return blob
    blob = _read_fallback()
    return blob

def enable_passphrase(passphrase: str, kdf_n: int = 2**14, kdf_r: int = 8, kdf_p: int = 1) -> None:
    """
    Wrap currently stored master key with passphrase and save the wrapped blob.
    After success, this function does NOT delete the raw master key (caller may do so).
    """
    # ensure we have a master key
    if KEY_MANAGER_AVAILABLE:
        master = get_master_key()
    else:
        # if key_manager not available, generate a new master and wrap it
        master = secrets.token_bytes(32)

    salt = secrets.token_bytes(16)
    derived = _derive_key(passphrase.encode(), salt, n=kdf_n, r=kdf_r, p=kdf_p, length=32)
    aes = AESGCM(derived)
    iv = secrets.token_bytes(12)
    wrapped = aes.encrypt(iv, master, None)

    blob = {
        "salt": base64.b64encode(salt).decode(),
        "iv": base64.b64encode(iv).decode(),
        "wrapped_master": base64.b64encode(wrapped).decode(),
        "kdf_params": {"n": kdf_n, "r": kdf_r, "p": kdf_p}
    }

    saved = _store_blob_in_keyring(blob)
    if not saved:
        _write_fallback(blob)

def unwrap_master_from_passphrase(passphrase: str) -> bytes:
    """
    Attempt to unwrap master key using provided passphrase.
    Raises ValueError on failure.
    """
    blob = get_wrapped_metadata()
    if not blob:
        raise ValueError("No wrapped master key found. Please enable passphrase first.")
    salt = base64.b64decode(blob["salt"])
    iv = base64.b64decode(blob["iv"])
    wrapped = base64.b64decode(blob["wrapped_master"])
    params = blob.get("kdf_params", {})
    n = params.get("n", 2**14)
    r = params.get("r", 8)
    p = params.get("p", 1)
    try:
        derived = _derive_key(passphrase.encode(), salt, n=n, r=r, p=p, length=32)
        master = AESGCM(derived).decrypt(iv, wrapped, None)
        return master
    except Exception as e:
        raise ValueError("Incorrect passphrase or decryption failed.") from e

def verify_passphrase(passphrase: str) -> bool:
    try:
        _ = unwrap_master_from_passphrase(passphrase)
        return True
    except Exception:
        return False

def change_passphrase(old_pass: str, new_pass: str, new_kdf_n: int = 2**14, new_kdf_r: int = 8, new_kdf_p: int = 1):
    # unwrap master using old
    master = unwrap_master_from_passphrase(old_pass)
    # wrap with new pass
    salt = secrets.token_bytes(16)
    derived = _derive_key(new_pass.encode(), salt, n=new_kdf_n, r=new_kdf_r, p=new_kdf_p, length=32)
    aes = AESGCM(derived)
    iv = secrets.token_bytes(12)
    wrapped = aes.encrypt(iv, master, None)
    blob = {
        "salt": base64.b64encode(salt).decode(),
        "iv": base64.b64encode(iv).decode(),
        "wrapped_master": base64.b64encode(wrapped).decode(),
        "kdf_params": {"n": new_kdf_n, "r": new_kdf_r, "p": new_kdf_p}
    }
    saved = _store_blob_in_keyring(blob)
    if not saved:
        _write_fallback(blob)

def export_wrapped_backup(path: str):
    """Export the wrapped JSON to a file (safe as backup)"""
    blob = get_wrapped_metadata()
    if not blob:
        raise ValueError("No wrapped blob to export")
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(blob, f)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass

def import_wrapped_backup(path: str):
    """Import wrapped blob from file (overwrite existing)"""
    with open(path, "r") as f:
        blob = json.load(f)
    saved = _store_blob_in_keyring(blob)
    if not saved:
        _write_fallback(blob)