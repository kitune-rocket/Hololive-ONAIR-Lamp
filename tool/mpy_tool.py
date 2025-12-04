#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MicroPython development tool.

This tool provides functionalities for:
1. Setting up the development environment using pyenv.
2. Flashing the MicroPython firmware to an ESP32 device.
3. Uploading project scripts to the device.
4. Formatting the device's filesystem.
"""

import os
import sys
import subprocess
import argparse
import shutil
from urllib import request

# ==============================================================================
# Global Configuration
# ==============================================================================
PROJECT_NAME = "hololive"
FIRMWARE_RELEASE = "https://micropython.org/resources/firmware/ESP32_GENERIC_S2-20250911-v1.26.1.bin"
SERIAL_PORT = None
DEBUG = False
# ==============================================================================

class MockProcessResult:
    """A mock result object for dry runs to mimic subprocess.CompletedProcess."""
    def __init__(self, stdout='', stderr='', returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.check_returncode = lambda: None # Mock check_returncode

def run_command(command, check=True):
    """Executes a shell command and returns its output, with a dry-run mode."""
    if DEBUG:
        print(f"[DRY RUN] Would execute: {' '.join(command)}")
        # Return mock results for commands whose output is parsed
        if command[0] == "pyenv" and command[1] == "version-name":
            return MockProcessResult(stdout=PROJECT_NAME)
        if command[0] == "pyenv" and command[1] == "root":
            # Must return a valid-looking path for os.path.join to work
            return MockProcessResult(stdout=f"/Users/tester/.pyenv/versions/{PROJECT_NAME}")
        if command[0] == "ampy" and command[1] == "ls":
            return MockProcessResult(stdout="/boot.py\n/main.py\nlib/\n")
        # For other commands, return a generic success object
        return MockProcessResult()

    print(f"Executing: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=check, capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Is it installed and in your PATH?", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}", file=sys.stderr)
        print(e.stdout, file=sys.stdout)
        print(e.stderr, file=sys.stderr)
        return None


def check_venv():
    """Checks if the correct pyenv virtualenv is active."""
    if not shutil.which("pyenv"):
        print("Warning: 'pyenv' not found. Cannot verify virtual environment.", file=sys.stderr)
        return

    result = run_command(["pyenv", "version-name"], check=False)
    if not result or result.returncode != 0:
        print("Warning: Could not determine pyenv version.", file=sys.stderr)
        return

    active_venv = result.stdout.strip()
    if active_venv != PROJECT_NAME:
        print(f"Error: Pyenv virtualenv '{PROJECT_NAME}' is not active.", file=sys.stderr)
        print(f"Please run 'pyenv shell {PROJECT_NAME}' first.", file=sys.stderr)
        sys.exit(1)


def setup_environment():
    """
    Sets up the Python virtual environment using pyenv.
    """
    print("--- Setting up environment ---")
    if not shutil.which("pyenv"):
        print("Error: 'pyenv' not found. Please install pyenv to continue.", file=sys.stderr)
        print("Installation guide: https://github.com/pyenv/pyenv#installation")
        sys.exit(1)

    if not PROJECT_NAME:
        print("Error: PROJECT_NAME is not set. Please define it at the top of the script.", file=sys.stderr)
        sys.exit(1)

    # Deactivating is handled by pyenv's shell integration,
    # attempting to create will work even if another venv is active.
    print(f"Creating virtual environment '{PROJECT_NAME}'...")
    run_command(["pyenv", "virtualenv", PROJECT_NAME], check=False) # Fails if exists, which is fine

    print("Activating virtual environment...")
    # Activating in script is complex. We will use the pyenv-virtualenv python executable directly.
    pyenv_root = run_command(["pyenv", "root"]).stdout.strip()
    venv_python = os.path.join(pyenv_root, "versions", PROJECT_NAME, "bin", "python")

    if not DEBUG:
        if not os.path.exists(venv_python):
            print(f"Error: Could not find python executable for virtualenv '{PROJECT_NAME}'", file=sys.stderr)
            sys.exit(1)
        
        print("Installing/updating dependencies from requirements.txt...")
        run_command([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("[DRY RUN] Would install dependencies from requirements.txt")

    print("\nSetup complete. Please activate the virtual environment manually:")
    print(f"  pyenv shell {PROJECT_NAME}")


def flash_firmware(port, baud="460800"):
    """
    Downloads firmware if not present and flashes it to the device.
    """
    check_venv()
    print("--- Flashing firmware ---")
    if SERIAL_PORT:
        port = SERIAL_PORT
    if not port:
        print("Error: Serial port must be provided via argument or SERIAL_PORT variable.", file=sys.stderr)
        sys.exit(1)

    bin_files = [f for f in os.listdir('.') if f.endswith('.bin')]
    if not bin_files:
        if DEBUG:
            print("[DRY RUN] Would download firmware.")
            bin_files.append("firmware.bin") # mock file
        else:
            print(f"No .bin file found. Downloading from {FIRMWARE_RELEASE}...")
            try:
                firmware_filename = FIRMWARE_RELEASE.split('/')[-1]
                request.urlretrieve(FIRMWARE_RELEASE, firmware_filename)
                bin_files.append(firmware_filename)
                print(f"Downloaded '{firmware_filename}'")
            except Exception as e:
                print(f"Error downloading firmware: {e}", file=sys.stderr)
                sys.exit(1)
    
    firmware_path = bin_files[0]
    print(f"Using firmware: {firmware_path}")

    print("Erasing flash...")
    input('Make sure the target board is in bootloader mode, and press enter...')
    # if not run_command(["esptool.py", "--port", port, "erase_flash"]):
    if not run_command(["esptool.py", "erase_flash"]):
        print("Error erasing flash. Please check the connection and try again.", file=sys.stderr)
        sys.exit(1)

    print("Writing firmware...")
    input('Make sure the target board is in bootloader mode, and press enter...')
    # write_command = [
    #     "esptool.py", "--port", port, "--baud", baud,
    #     "write_flash", "0x1000", firmware_path
    # ]
    write_command = ["esptool.py", "--baud", baud, "write_flash", "0x1000", firmware_path]
    if not run_command(write_command):
        print("Error writing firmware.", file=sys.stderr)
        sys.exit(1)
    
    print("Firmware flashing complete.")


def upload_scripts(path, port):
    """
    Recursively uploads whitelisted files from a given path to the device.
    """
    check_venv()
    print("--- Uploading scripts ---")
    if SERIAL_PORT:
        port = SERIAL_PORT
    if not port:
        print("Error: Serial port must be provided via argument or SERIAL_PORT variable.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(path):
        print(f"Error: Path '{path}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    whitelist = ['.py', '.pyc', '.pyo', '.json', '.txt']
    
    for root, _, files in os.walk(path):
        for filename in files:
            if any(filename.endswith(ext) for ext in whitelist):
                local_path = os.path.join(root, filename)
                device_path = os.path.relpath(local_path, path)
                print(f"Uploading {local_path} to /{device_path}...")
                run_command(["ampy", "-p", port, "put", local_path, device_path])

    print("Script upload complete.")


def format_device(port):
    """
    Removes all files and directories from the device's root filesystem.
    """
    check_venv()
    print("--- Formatting device filesystem ---")
    if SERIAL_PORT:
        port = SERIAL_PORT
    if not port:
        print("Error: Serial port must be provided via argument or SERIAL_PORT variable.", file=sys.stderr)
        sys.exit(1)

    def list_files_recursive(path):
        """Recursively list all files and dirs on device."""
        result = run_command(["ampy", "-p", port, "ls", path], check=False)
        if not result or result.returncode != 0:
            return [], []

        entries = result.stdout.strip().split('\n')
        files, dirs = [], []
        for entry in entries:
            entry = entry.strip()
            if entry:
                if entry.endswith('/'):
                     dirs.append(entry)
                else:
                    files.append(entry)
        return files, dirs

    def remove_all(path):
        """Recursively remove files and directories."""
        files, dirs = list_files_recursive(path)

        for f in files:
            full_path = f"{path}{f}" if path != "/" else f
            print(f"Removing file: {full_path}")
            run_command(["ampy", "-p", port, "rm", full_path])

        for d in dirs:
            full_path = f"{path}{d}" if path != "/" else d
            remove_all(full_path)

    print("This will delete all files on the device. Listing root contents:")
    # Initial list to show the user what's there
    run_command(["ampy", "-p", port, "ls", "/"])

    # Start recursive delete from root
    remove_all('/')
    
    # Finally, remove the directories themselves
    _, dirs = list_files_recursive('/')
    for d in sorted(dirs, key=lambda x: x.count('/'), reverse=True):
         print(f"Removing directory: {d}")
         run_command(["ampy", "-p", port, "rmdir", d])


    print("Device format complete.")


def main():
    """Main function to parse arguments and call corresponding functions."""
    parser = argparse.ArgumentParser(description="MicroPython development tool for the Hololive-ONAIR-Lamp project.")
    subparsers = parser.add_subparsers(dest="mode", required=True, help="Available modes")

    # Setup mode
    subparsers.add_parser("setup", help="Set up the pyenv virtual environment and install dependencies.")

    # Flash mode
    flash_parser = subparsers.add_parser("flash", help="Flash firmware to the device.")
    flash_parser.add_argument("-p", "--port", help="Serial port of the device (e.g., /dev/ttyUSB0, COM3).")

    # Upload mode
    upload_parser = subparsers.add_parser("upload", help="Upload scripts to the device.")
    upload_parser.add_argument("path", help="Path to the script directory to upload.")
    upload_parser.add_argument("-p", "--port", help="Serial port of the device.")

    # Format mode
    format_parser = subparsers.add_parser("format", help="Format the device's filesystem.")
    format_parser.add_argument("-p", "--port", help="Serial port of the device.")

    args = parser.parse_args()

    if args.mode == "setup":
        setup_environment()
    elif args.mode == "flash":
        flash_firmware(args.port)
    elif args.mode == "upload":
        upload_scripts(args.path, args.port)
    elif args.mode == "format":
        format_device(args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
