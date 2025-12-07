# blackhole_core.py
import os, base64, json, zlib, secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from key_manager import get_master_key
import secrets as _secrets

STORE_DIR = os.path.expanduser("~/.blackhole_store")
os.makedirs(STORE_DIR, exist_ok=True)

def _wrap_fek_with_master(fek: bytes, master_key: bytes):
    aesgcm = AESGCM(master_key)  # master_key must be 16/24/32 bytes; we use 32
    iv = _secrets.token_bytes(12)
    wrapped = aesgcm.encrypt(iv, fek, None)
    return iv, wrapped

def _unwrap_fek_with_master(iv: bytes, wrapped: bytes, master_key: bytes):
    aesgcm = AESGCM(master_key)
    fek = aesgcm.decrypt(iv, wrapped, None)
    return fek

def save_file_bytes(orig_name: str, data_bytes: bytes, master_key: bytes = None):
    if master_key is None:
        master_key = get_master_key()
    compressed = zlib.compress(data_bytes)
    fek = _secrets.token_bytes(32)  # file encryption key
    iv_file = _secrets.token_bytes(12)
    aes_file = AESGCM(fek)
    ciphertext = aes_file.encrypt(iv_file, compressed, None)
    iv_wrap, wrapped_fek = _wrap_fek_with_master(fek, master_key)
    payload = {
        "version": 1,
        "orig_name": orig_name,
        "iv_wrap": base64.b64encode(iv_wrap).decode(),
        "wrapped_fek": base64.b64encode(wrapped_fek).decode(),
        "iv_file": base64.b64encode(iv_file).decode(),
        "payload": base64.b64encode(ciphertext).decode(),
        "orig_len": len(data_bytes)
    }
    outname = os.path.join(STORE_DIR, secrets.token_hex(16) + ".black")
    with open(outname, "w") as f:
        json.dump(payload, f)
    return outname

def open_black_file(path: str, master_key: bytes = None) -> bytes:
    if master_key is None:
        master_key = get_master_key()
    with open(path, "r") as f:
        payload = json.load(f)
    iv_wrap = base64.b64decode(payload["iv_wrap"])
    wrapped_fek = base64.b64decode(payload["wrapped_fek"])
    iv_file = base64.b64decode(payload["iv_file"])
    ciphertext = base64.b64decode(payload["payload"])
    fek = _unwrap_fek_with_master(iv_wrap, wrapped_fek, master_key)
    aes_file = AESGCM(fek)
    compressed = aes_file.decrypt(iv_file, ciphertext, None)
    data = zlib.decompress(compressed)
    return data

def secure_wipe_file(path: str) -> bool:
    try:
        if not os.path.exists(path):
            return True
        size = os.path.getsize(path)
        with open(path, "r+b") as f:
            f.seek(0)
            f.write(secrets.token_bytes(size))
            f.flush()
            os.fsync(f.fileno())
        os.remove(path)
        return True
    except Exception as e:
        # best-effort fallback
        try:
            os.remove(path)
            return True
        except Exception:
            return False