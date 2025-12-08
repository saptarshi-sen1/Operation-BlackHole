# 🌑 Operation Blackhole  
### Zero-Storage Security System — Files Never Persist in Plain Form

**Operation Blackhole** is a next-generation **Zero-Data-Persistence Security System** designed so that **no file on your device ever exists in its original, readable form**.

Once a file enters the system, it is immediately:

1. **Detected** by the watcher  
2. **Encrypted**, converted into `.black` mathematical format  
3. **Stored securely** inside the encrypted vault  
4. **Original file is securely wiped beyond recovery**  
5. **Reconstructed only in RAM** when viewed or restored  

This guarantees that even with full device access, **no forensic tool or attacker can recover your files.** 🌘

---

# 🚀 Features (Updated)

### 🔐 Zero-Storage Model  
Files never exist unencrypted on disk.  
Decrypted data lives only in **RAM**, never written back.

### 🔁 Real-Time Watcher  
A background watchdog converts anything added into the `~/Watched` folder into encrypted `.black` files.

### 🌑 The `.black` Format  
An encrypted, metadata-clean structure containing:

- AES-GCM encrypted payload  
- Encrypted FEK (File Encryption Key)  
- Random IV / Nonce  
- MIME type  
- Original filename  
- **Zero metadata leakage**

### 🔥 Secure Wipe  
Overwrites original files before deletion to prevent recovery.

### 🔒 Passphrase-Protected Master Key  

- Master key wrapping using PBKDF2 + AES  
- Passphrase set / change / reset  
- Metadata-backed wrapped key file  
- Recoverable via exported JSON backup  
- Session-based unlocking  

### 🖥 Modern GUI Application  

Tkinter-based GUI with:

- Image preview (RAM-only)  
- Text preview  
- Restore to chosen path  
- Secure deletion of `.black` files  
- Passphrase setup / change / export / import  
- WSL-friendly folder opening (Windows Explorer)  
- Internal folder browser fallback  

---

# 📁 Folder Structure

```

operation_blackhole/
├── daemon_watcher.py          # Watches ~/Watched and encrypts files
├── blackhole_core.py          # Encryption, decryption, secure wipe
├── password_manager.py       # Master passphrase system
├── encrypt_decrypt_gui.py    # GUI application
├── restore_file.py           # CLI restore tool
├── venv/                     # Virtual environment (ignored)
├── Watched/                  # Auto-encrypt drop folder
└── .blackhole_store/         # Encrypted vault

````

---

# 🛠 Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/<your-username>/operation_blackhole.git
cd operation_blackhole
````

## 2️⃣ Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3️⃣ Install Dependencies

```bash
pip install watchdog cryptography pillow
```

**Tkinter (Linux / WSL):**

```bash
sudo apt install -y python3-tk
```

## 4️⃣ Create Required Folders

```bash
mkdir -p ~/Watched
mkdir -p ~/.blackhole_store
chmod 700 ~/Watched ~/.blackhole_store
```

---

# 🔧 Autostart Watcher (systemd – User Service)

## Create systemd directory

```bash
mkdir -p ~/.config/systemd/user
```

## Create service file

```bash
cat > ~/.config/systemd/user/operation_blackhole.service <<'SERVICE'
[Unit]
Description=Operation Blackhole watcher (user service)

[Service]
Type=simple
ExecStart=%h/operation_blackhole/venv/bin/python %h/operation_blackhole/daemon_watcher.py
Restart=on-failure
WorkingDirectory=%h/operation_blackhole
Environment=PATH=%h/operation_blackhole/venv/bin:/usr/bin:/bin

[Install]
WantedBy=default.target
SERVICE
```

## Enable & Start

```bash
systemctl --user daemon-reload
systemctl --user enable --now operation_blackhole.service
```

## View Logs

```bash
journalctl --user -u operation_blackhole.service -f
```

---

# 🖥 Using the GUI

Launch the GUI:

```bash
source venv/bin/activate
python encrypt_decrypt_gui.py
```

### GUI Capabilities

* Encrypt via `~/Watched`
* Image and text previews (RAM-only)
* Restore decrypted files
* Secure deletion of `.black` entries
* Passphrase management
* Wrapped key metadata viewer
* Export / import wrapped-key backup
* Folder opening via:

  * Windows Explorer (WSL)
  * Linux file manager
  * Internal browser fallback

---

# 📥 Encryption Flow

### 1️⃣ Add Files

Drop files into:

```bash
~/Watched/
```

They are automatically:

* Detected
* Encrypted into `.black`
* Stored in `~/.blackhole_store/`
* Securely wiped from `~/Watched`

### 2️⃣ View

* GUI reconstructs files **only in RAM**
* No decrypted files touch disk

### 3️⃣ Restore

* Choose output path
* File reconstructed on demand

---

# 🧪 Testing

### Text File

```bash
echo "hello_world" > ~/Watched/test.txt
```

### Image File

```bash
cp /usr/share/backgrounds/*.jpg ~/Watched/
```

### Verify

```bash
ls ~/.blackhole_store
ls ~/Watched
```

---

# 🔐 Security Model

### Master Key

* Wrapped using PBKDF2 (passphrase-derived)
* Stored only as encrypted metadata
* Never stored in plaintext
* **Losing passphrase or backup = irreversible data loss**

### Per File

* AES-GCM encryption
* Unique FEK per file
* FEK encrypted with master key
* Strong integrity & authenticity

### RAM-Only Reconstruction

* Decryption occurs in memory only
* `/dev/shm` used for safe previews
* Memory cleared after use

### Secure Wipe

* Multi-pass overwrite
* Resistant to forensic recovery

---

# ⚠️ Important Notes

**NEVER commit:**

```text
.blackhole_store/
master_key.b64
wrapped_key.json
```

* Losing passphrase or wrapped key = total data loss
* GUI supports backup export — store it safely
* WSL relies on Windows Explorer for folder opening

---

# 🧾 .gitignore

```
.blackhole_store/
Watched/
venv/
__pycache__/
*.pyc
*.log
*.tmp
master_key.b64
wrapped_key.json
```

---

# 📡 Future Roadmap

* TPM / Secure Enclave key sealing
* Android Blackhole Camera app
* Encrypted clipboard
* FUSE-based encrypted filesystem (BlackFS)
* Cross-device encrypted sync
* Native Windows / macOS GUI builds
* Built-in encrypted PDF & video viewers

---

# 🎉 Summary

**Operation Blackhole** is a complete zero-storage, zero-trace encryption system featuring:

* Automatic encryption
* RAM-only access
* Passphrase-protected master key
* Secure wiping
* GUI management
* WSL-optimized workflows

A **full cryptographic vault** built for maximum privacy and zero trust.