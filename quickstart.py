#!/usr/bin/env python
"""
Voice Sentinel - Simple Launcher
This script provides an interactive menu to launch Voice Sentinel
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header():
    """Print the header"""
    print("\n" + "="*50)
    print("Voice Sentinel - QuickStart")
    print("="*50 + "\n")


def check_environment():
    """Check if environment is ready"""
    # Check virtual environment
    if not Path(".venv").exists():
        print("[1/3] Creating virtual environment...")
        result = subprocess.run([sys.executable, "-m", "venv", ".venv"])
        if result.returncode != 0:
            print("[ERROR] Failed to create virtual environment")
            return False
        print("[OK] Virtual environment created")

    # Check .env file
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("\n[INFO] Using .env.example for API Key")
            print("[OK] Environment ready\n")
            return True
        print("\n[WARNING] .env file not found")
        print("Please run: copy .env.example .env")
        print("Then edit .env and add your Google API Key")
        print("\nGet API Key: https://ai.google.dev/tutorials/python_quickstart\n")
        input("Press Enter to continue...")
        return False

    print("[OK] Environment ready\n")
    return True


def run_test_mode():
    """Run test mode"""
    print("\n[TEST MODE] Running...\n")
    result = subprocess.run([sys.executable, "voice_sentinel.py", "--test"])
    return result.returncode == 0


def run_full_mode():
    """Run full mode"""
    print("\n[FULL MODE] Get ready to speak!\n")
    result = subprocess.run([sys.executable, "voice_sentinel.py"])
    return result.returncode == 0


def open_guide():
    """Open usage guide"""
    guide_file = Path("USAGE_GUIDE.md")
    if guide_file.exists():
        print("[INFO] Opening guide...")
        if sys.platform == "win32":
            os.startfile(guide_file)
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(guide_file)])
        else:  # Linux
            subprocess.run(["xdg-open", str(guide_file)])
    else:
        print("[ERROR] USAGE_GUIDE.md not found")


def main():
    """Main function"""
    print_header()

    # Check environment
    if not check_environment():
        print("[ERROR] Environment not ready")
        return 1

    # Show menu
    print("Select Mode:\n")
    print("  1. Test Mode (no microphone needed)")
    print("  2. Full Mode (requires voice input)")
    print("  3. View Guide")
    print("  4. Exit\n")

    choice = input("Choose (1-4): ").strip()

    if choice == "1":
        success = run_test_mode()
        return 0 if success else 1
    elif choice == "2":
        success = run_full_mode()
        return 0 if success else 1
    elif choice == "3":
        open_guide()
        return 0
    elif choice == "4":
        print("\nExit.")
        return 0
    else:
        print("\n[ERROR] Invalid choice")
        return 1


if __name__ == "__main__":
    sys.exit(main())
