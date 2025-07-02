import os
import subprocess
import urllib.request
import sys
import venv
from pathlib import Path

# === Required Packages ===
REQUIRED_PACKAGES = [
    "torch",
    "opencv-python",
    "numpy",
    "pygame",
    "pyttsx3",
    "matplotlib"
]

# === Paths ===
D_DRIVE_ROOT = Path("D:/smart_trolley_env")
VENV_DIR = D_DRIVE_ROOT / "venv"
PYTHON_EXE = VENV_DIR / "Scripts/python.exe"
BEEP_URL = "https://github.com/openai-sounds/beep/raw/main/beep.mp3"
BEEP_PATH = D_DRIVE_ROOT / "beep.mp3"

def create_virtualenv():
    if not VENV_DIR.exists():
        print(f"🧪 Creating virtual environment at {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)
        print("✅ Virtual environment created!\n")

def install_packages():
    print("📦 Installing required packages into virtualenv...\n")
    for package in REQUIRED_PACKAGES:
        try:
            subprocess.check_call([str(PYTHON_EXE), "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install package: {package}")

def ensure_beep_sound():
    if not BEEP_PATH.exists():
        try:
            print("🔊 Downloading beep.mp3 to D:...")
            urllib.request.urlretrieve(BEEP_URL, str(BEEP_PATH))
            print("✅ beep.mp3 downloaded successfully!\n")
        except Exception as e:
            print(f"⚠️ Failed to download beep.mp3: {e}")
            print("Fallback: Voice alert will work without beep sound.\n")

def run_main():
    print("🚀 Launching Smart Trolley System...\n")
    exit_code = subprocess.call([str(PYTHON_EXE), "main.py"])
    if exit_code != 0:
        print("❌ main.py exited with errors.")
    else:
        print("✅ Smart Trolley finished successfully.")

if __name__ == "__main__":
    os.makedirs(D_DRIVE_ROOT, exist_ok=True)
    create_virtualenv()
    install_packages()
    ensure_beep_sound()
    run_main()
