# Hololive-ONAIR-Lamp

A project to upgrade the official Hololive desk light into a "ON AIR" notification lamp. This lamp automatically lights up and plays a tune when your favorite Hololive member starts a YouTube stream.

The project utilizes an ESP32-S2 microcontroller and MicroPython to periodically check the [Holodex API](https://docs.holodex.net/) for live and upcoming streams. Great thanks to **Holodex Team** for wonderful web service and API! 

[Holodex Github](https://github.com/HolodexNet/Holodex)

## Features

- **Automatic Stream Detection**: Monitors a configured YouTube channel via the Holodex API.
- **ON AIR Notification**: When a stream goes live, the lamp plays a startup sound and then remains lit.
- **Customizable Audio**: The notification sound can be changed by converting a MIDI file to the required format.

## Hardware

This project is designed to run on an **ESP32-S2** microcontroller. A custom PCB is designed to fit inside the official Hololive desk light merchandise.

- **Microcontroller**: ESP32-S2 based board.
- **Custom PCB**: Schematic files (`desklight_board.pdf`) and Gerber/Pick&Place files for manufacturing (`jlcpcb.zip`) can be found in the [`resource`](./resource/) directory.
- **Official Hololive Desklight**: This project is intended to modify the official merchandise.
- **3D Print Case & bolt/nuts**

## Software Setup

The firmware is written in MicroPython.

### 1. Configuration

Create a `config.json` file inside the `src` directory with the following content. You can use `config.json.example` as a template.

```json
{
    "ssid": "YOUR_WIFI_SSID",
    "password": "YOUR_WIFI_PASSWORD",
    "token": "YOUR_HOLODEX_API_KEY",
    "channelId": "YOUTUBE_CHANNEL_ID_TO_MONITOR"
}
```

- `ssid` & `password`: Your Wi-Fi network credentials.
- `token`: Your personal API key for the Holodex API. You can get one by registering on the [Holodex](https://holodex.net/) website.
- `channelId`: The ID of the Hololive member's YouTube channel you want to monitor (e.g., `UCdn5BQ06XqgXoAxIhbqw5Rg` for Fubuki Ch.).

### 2. Notification Sound

The lamp plays a notification sound from an `audio.bin` file. A tool is provided to convert a simple MIDI file into this format.

- Place your MIDI file (e.g., `sound.mid`) in the `tool` directory.
- Run the converter: `python midi_converter.py ./sound.mid`
- This will generate the `audio.bin` file in the `src` directory.

### 3. Flashing the Firmware

- Flash your ESP32-S2 board with a recent version of MicroPython.
- Upload all the files from the `src` directory to the root of the microcontroller's filesystem.
- A `mpy_tool.py` will do it for you.

## [Tools](./tool/README.md)

The [`tool/`](./tool/) directory contains helpful scripts for development:
- `midi_converter.py`: Converts MIDI files to the `audio.bin` format used by the device.
- `mpy_tool.py`: A utility for interacting with a MicroPython board (e.g., uploading files).
- `requirements.txt`: Python dependencies for the tools.

## Future Improvements

- Reducing **tick** sounds at start of all notes.
- Increase API response with additional Google Youtube Data API