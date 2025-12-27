# MicroPython Development Tool (`tool/mpy_tool.py`)

## Overview

This script is an all-in-one utility designed to streamline the workflow for MicroPython development on ESP32 devices (specifically targeting ESP32-S2 as per the default firmware). It handles environment setup, firmware flashing, file uploading, and filesystem formatting.

## Prerequisites

Before running the tool, ensure the following are installed on your system:

  * **Python 3**
  * **pyenv** (Required for the `setup` mode to manage virtual environments)
  * **curl** (Used to download firmware)
  * **requirements.txt** (Must exist in the same directory, containing `esptool` and `adafruit-ampy`)

-----

## Configuration

You can modify the global variables at the top of `mpy_tool.py` to customize the tool for your specific environment:

```python
PROJECT_NAME = "hololive"       # Name of the pyenv virtual environment
FIRMWARE_RELEASE = "..."        # URL to the specific MicroPython .bin file
SERIAL_PORT = None              # Set this to your COM port (e.g., "COM3" or "/dev/ttyUSB0") 
                                # to skip the -p argument in commands.
```

-----

## Usage

The script is executed via the command line with specific **subcommands** (modes).

```bash
python mpy_tool.py [mode] [options]
```

### 1\. Environment Setup (`setup`)

Checks for `pyenv`, creates a virtual environment named according to `PROJECT_NAME` (default: `hololive`), and installs dependencies defined in `requirements.txt`.

**Command:**

```bash
python mpy_tool.py setup
```

**Post-Setup:**
After running setup, you must manually activate the virtual environment:

```bash
pyenv shell hololive
```

### 2\. Flash Firmware (`flash`)

Downloads the MicroPython firmware (defined in `FIRMWARE_RELEASE`) if it doesn't exist locally, erases the device flash, and writes the new firmware.

**Command:**

```bash
python mpy_tool.py flash -p [PORT]
```

  * **`-p / --port`**: The serial port of the device (e.g., `/dev/tty.usbmodem1234`, `COM3`).
      * *Note: This is optional if `SERIAL_PORT` is set in the script.*

**Process:**

1.  Checks for the `.bin` file. If missing, it downloads it via `curl`.
2.  Prompts you to ensure the board is in **Bootloader Mode**.
3.  Erases flash.
4.  Writes firmware at address `0x1000`.

### 3\. Upload Scripts (`upload`)

Recursively uploads files from a local directory to the device.

**Command:**

```bash
python mpy_tool.py upload [DIRECTORY_PATH] -p [PORT]
```

  * **`DIRECTORY_PATH`**: Path to the local folder containing your project code.
  * **`-p / --port`**: The serial port of the device.

**Whitelist:**
Only files with the following extensions are uploaded:

  * `.py`, `.pyc`, `.pyo`, `.json`, `.txt`, `.bin`

### 4\. Format Filesystem (`format`)

**WARNING:** This is a destructive action. It recursively removes **ALL** files and directories from the MicroPython device.

**Command:**

```bash
python mpy_tool.py format -p [PORT]
```

  * **`-p / --port`**: The serial port of the device.

-----

## Example Workflow

1.  **Initialize the project:**

    ```bash
    python mpy_tool.py setup
    pyenv shell hololive
    ```

2.  **Flash the ESP32 (if new or corrupted):**

    ```bash
    python mpy_tool.py flash -p /dev/ttyUSB0
    ```

3.  **Upload your project code:**

    ```bash
    # Uploads contents of the current directory (.) to the device
    python mpy_tool.py upload . -p /dev/ttyUSB0
    ```

# MIDI to Binary Converter Usage Guide (`tool/midi_converter.py`)

## Overview

`midi_converter.py` is a Python utility that parses a MIDI file, processes a selected track, and converts it into a raw binary format consisting of **(Frequency, Duration)** tuples. This is designed for generating audio data for microcontroller projects (e.g., using PWM).

### Key Features

  * **Track Analysis:** Displays instrument names, note counts, and frequency ranges for all tracks.
  * **Chord Handling:** Automatically selects the highest pitch note when chords are detected.
  * **Silence Handling:** Fills gaps between notes with 0Hz (silence) to ensure continuous timing.
  * **Transposition:** Supports key shifting (semitones) via command-line arguments.
  * **Binary Output:** Exports data as 16-bit little-endian integers (`<HH`).

-----

## Prerequisites

Ensure you have Python installed. You also need the `mido` library to parse MIDI files. If you have used mpy_tool.py, activate vitualenv `hololive`

```bash
pip install mido
OR
pyenv shell hololive
```

-----

## Usage

Run the script from the command line using the following syntax:

```bash
python midi_converter.py [midi_file_path] [options]
```

### Arguments

| Argument | Type | Description |
| :--- | :--- | :--- |
| `midi_file_path` | **Required** | The path to the input `.mid` file. |
| `-k` / `--key` | Optional | Transpose the key by $N$ semitones.<br>• **Positive int**: Pitch up<br>• **Negative int**: Pitch down<br>• **Default**: `0` |
| `-b` / `--bpm` | Optional | Manually set the BPM (overrides MIDI file tempo).<br>• **Float**: Target BPM (e.g., `140`, `128.5`) |
| `-l` / `--length` | Optional | Limit the conversion to a specific number of beats.<br>• **Float**: Max beats (e.g., `64`, `100.25`) |

-----

## Step-by-Step Execution

### 1\. Run the Command

Example: Convert `song.mid` and raise the pitch by 1 octave (12 semitones).

```bash
python midi_converter.py song.mid -k 12
```

### 2\. Select a Track

The script will analyze the MIDI file and list available tracks with details such as instrument name and note count. After checking the output, it is recommended to transpose the key to keep the maximum frequency below 3 kHz.

**Example Output:**

```text
MIDI File Loaded. Analyzing tracks...
----------------------------------------
Track 0: Piano Right
  - Instrument: Acoustic Grand Piano
  - Note Count: 154
  - Lowest Note: 48 (130.81 Hz)
  - Highest Note: 84 (1046.50 Hz)
----------------------------------------
Track 1: Piano Left
  - Instrument: Not set
  - Note Count: 0
----------------------------------------
Enter the track number to process: 
```

Type the **Track Number** (e.g., `0`) and press Enter. 

### 3\. File Generation

Upon successful processing, the script generates binary files in two locations:

1.  **Local Copy:** `[filename].bin` (Saved in the same directory as the script).
2.  **Project Copy:** `audio.bin` (Saved in `../src/` relative to the script).

-----

## Output Data Specifications

The generated binary file follows this structure:

  * **Format:** Binary (No headers, pure data).
  * **Data Type:** `struct.pack('<HH', frequency, duration)`
      * **Frequency (Hz):** 16-bit Unsigned Integer (0 \~ 20,000 Hz).
      * **Duration (ms):** 16-bit Unsigned Integer (0 \~ 60,000 ms).
  * **Logic:**
      * **0 Hz** indicates silence (rest).
      * Chord sections use the **highest pitch** note.
      * Values are clamped to fit 16-bit limits.