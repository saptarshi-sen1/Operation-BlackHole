import os, base64, getpass

# Try to import keyring
try:
    import keyring
    KEYRING_AVAILABLE = True
except Exception:
    KEYRING_AVAILABLE = False

SERVICE_NAME = "operation_blackhole_master_key"
USERNAME = os.environ.get("USER") or getpass.getuser()

# Fallback key storage file
FALLBACK_PATH = os.path.expanduser("~/.blackhole_store/master_key.b64")
os.makedirs(os.path.dirname(FALLBACK_PATH), exist_ok=True)

def _write_fallback(key_bytes: bytes):
    data = base64.b64encode(key_bytes).decode()
    tmp = FALLBACK_PATH + ".tmp"
    with open(tmp, "w") as f:
        f.write(data)
    os.replace(tmp, FALLBACK_PATH)
    try:
        os.chmod(FALLBACK_PATH, 0o600)
    except:
        pass

def _read_fallback():
    if not os.path.exists(FALLBACK_PATH):
        return None
    try:
        with open(FALLBACK_PATH, "r") as f:
            return base64.b64decode(f.read().strip())
    except:
        return None

def generate_master_key():
    key = os.urandom(32)
    if KEYRING_AVAILABLE:
        try:
            key_b64 = base64.b64encode(key).decode()
            keyring.set_password(SERVICE_NAME, USERNAME, key_b64)
            return key
        except:
            pass
    _write_fallback(key)
    return key

def get_master_key():
    if KEYRING_AVAILABLE:
        try:
            key_b64 = keyring.get_password(SERVICE_NAME, USERNAME)
            if key_b64:
                return base64.b64decode(key_b64)
        except:
            pass
    fb = _read_fallback()
    if fb:
        return fb
    else:
        return generate_master_key()
