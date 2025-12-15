# 🌑 Operation Blackhole

### Zero-Storage Security System — Files Never Exist in Original Form

Operation Blackhole is a next-generation **Zero-Data Storage System** designed to ensure that **no file stored on your device ever exists in its original, readable form**.

The moment a file enters the watched folder (e.g., photos, videos, documents, PDFs, text files), it is:

1. **Detected automatically**
2. **Encrypted + transformed into mathematical parameters (`.black` format)**
3. **Stored securely**
4. **The original file is permanently and securely wiped**
5. **Reconstructed only in RAM** when the user chooses to view it

This ensures that **nothing sensitive ever touches permanent storage**.

---

## 🚀 Features

### 🔐 Zero-Storage Model

Files never exist on disk in decrypted form. Reconstruction happens **ONLY in RAM**.

### 🔁 Automatic Processing

A watcher daemon continuously monitors the `~/Watched` directory.

### 🌑 `.black` Format

Encrypted JSON-based mathematical representation containing:

* Wrapped FEK
* AES-GCM encrypted payload
* MIME type
* Original filename
* No traceable metadata

### 🔥 Secure Wipe

Original files overwritten + deleted to prevent recovery.

### 🔒 Pluggable Master-Key Storage

Supports:

* System keyring (Secret Service / GNOME Keyring)
* Secure fallback (`master_key.b64` with `chmod 600`)

### 👁 RAM-Based Viewer

Reconstructs files in memory only. No permanent files or thumbnails left behind.

---

## 📁 Folder Structure

```
operation_blackhole/
├── daemon_watcher.py       # Watches folder & converts files to .black
├── blackhole_core.py       # Encryption, encoding, file wiping logic
├── key_manager.py          # Master key generation & secure storage
├── viewer.py               # Secure file viewer (RAM-only reconstruction)
├── secure_wipe.py          # Utility to securely delete files
├── venv/                   # Virtual environment (ignored in git)
├── Watched/                # Input folder (auto-created)
└── .blackhole_store/       # Encrypted .black files + fallback master key
```

---

## 🛠 Installation

### 1) Clone the repository

```bash
git clone https://github.com/<your-username>/operation_blackhole.git
cd operation_blackhole
```

### 2) Create a Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3) Install dependencies

```bash
pip install watchdog cryptography pillow keyring
```

### 4) Create directories

```bash
mkdir -p ~/Watched
mkdir -p ~/.blackhole_store
chmod 700 ~/Watched
chmod 700 ~/.blackhole_store
```

---

## 🔧 Systemd Service (Auto-Start Watcher)

Create the service folder:

```bash
mkdir -p ~/.config/systemd/user
```

Create the service file:

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

Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable --now operation_blackhole.service
```

View logs:

```bash
journalctl --user -u operation_blackhole.service -f
```

---

## 📥 How to Use

### 1️⃣ Drop files into:

```bash
~/Watched/
```

The system will:

* Detect the file
* Wait until fully written
* Convert to `.black` (encrypted parameters)
* Securely wipe the original
* Store encrypted data in `~/.blackhole_store/`

### 2️⃣ View encrypted files:

```bash
cd ~/operation_blackhole
source venv/bin/activate
python encrypt_decrypt_gui.py
```

Viewer behavior:

* **Images** → displayed in RAM-only Tkinter window
* **Text** → preview printed in the terminal
* **PDFs / Videos / Others** → written to `/dev/shm` (RAM), opened with `xdg-open`, wiped after confirmation

Nothing remains on disk after viewing (best effort).

---

## 🧪 Testing Your Setup

### Test Text File

```bash
echo "test123" > ~/Watched/test.txt
```

### Test Image

```bash
cp ~/Pictures/some_image.jpg ~/Watched/
```

### Confirm Processing

List encrypted files:

```bash
ls ~/.blackhole_store
```

Ensure original is deleted:

```bash
ls ~/Watched
```

View encrypted files:

```bash
python viewer.py
```

Inspect `.black` file (should reveal nothing readable):

```bash
strings ~/.blackhole_store/*.black | head
```

---

## 🔐 Security Model

### Master Key

* Wraps per-file FEKs
* Stored in system keyring or fallback local file
* Losing it = **permanent loss of all .black files**

### Per-file Encryption

* AES-GCM with random FEK & IV
* FEK encrypted with master key
* No metadata or thumbnails stored

### Secure Wipe

* Overwrites original files before deletion

### RAM-only Reconstruction

* Rebuilt files exist only in volatile memory (`/dev/shm` for non-image types)

---

## ⚠️ Important Notes

* Losing the master key → all files permanently unrecoverable
* **Never commit** `.black` files or master keys to GitHub
* `.gitignore` prevents accidental uploads — review it before first commit

---

## 🧾 Recommended `.gitignore`

```
.blackhole_store/
Watched/
venv/
__pycache__/
*.pyc
*.log
*.tmp
master_key.b64
```

---

## 📡 Future Roadmap

* GUI dashboard
* TPM-backed master key sealing
* Better embedded viewers (PDF, video)
* FUSE filesystem integration (“blackFS”)
* Secure multi-device sync
* Mobile (Android) implementation
