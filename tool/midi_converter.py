
import mido
import argparse
import struct
import os
import math

def midi_to_hz(note, transpose=0):
    """Converts a MIDI note number to frequency in Hz, applying transposition."""
    if note == 0:
        return 0
    note += transpose
    return 440 * 2**((note - 69) / 12)

def analyze_and_process_midi(midi_path, transpose):
    """
    Analyzes a MIDI file, prompts the user to select a track,
    and processes it into a list of (frequency, duration) tuples.
    """
    try:
        mid = mido.MidiFile(midi_path)
    except FileNotFoundError:
        print(f"Error: MIDI file not found at '{midi_path}'")
        return None, None

    print("MIDI File Loaded. Analyzing tracks...")
    print("-" * 40)

    tracks_info = []
    for i, track in enumerate(mid.tracks):
        instrument_name = "Not set"
        note_count = 0
        notes = []
        for msg in track:
            if msg.is_meta and msg.type == 'instrument_name':
                instrument_name = msg.name
            if msg.type == 'note_on' and msg.velocity > 0:
                note_count += 1
                notes.append(msg.note)
        
        info = {
            "track_num": i,
            "name": track.name or "Unnamed",
            "instrument": instrument_name,
            "note_count": note_count,
            "min_note": min(notes) if notes else 0,
            "max_note": max(notes) if notes else 0,
        }
        tracks_info.append(info)

        print(f"Track {info['track_num']}: {info['name']}")
        print(f"  - Instrument: {info['instrument']}")
        print(f"  - Note Count: {info['note_count']}")
        if notes:
            min_hz = midi_to_hz(info['min_note'], transpose)
            max_hz = midi_to_hz(info['max_note'], transpose)
            print(f"  - Lowest Note: {info['min_note']} ({min_hz:.2f} Hz)")
            print(f"  - Highest Note: {info['max_note']} ({max_hz:.2f} Hz)")
        print("-" * 40)

    # --- Track Selection ---
    selected_track_num = -1
    while True:
        try:
            choice = input("Enter the track number to process: ")
            selected_track_num = int(choice)
            if 0 <= selected_track_num < len(mid.tracks):
                if tracks_info[selected_track_num]['note_count'] > 0:
                    break
                else:
                    print("Selected track has no notes. Please choose another track.")
            else:
                print("Invalid track number.")
        except ValueError:
            print("Please enter a valid number.")

    print(f"Processing Track {selected_track_num}...")

    # --- Note Processing ---
    selected_track = mid.tracks[selected_track_num]
    ticks_per_beat = mid.ticks_per_beat
    tempo = 500000  # Default MIDI tempo (120 BPM)

    note_events = []
    current_time_ticks = 0
    open_notes = {} # {note: start_tick}

    for msg in mido.merge_tracks(mid.tracks): # Merge tracks to get global tempo changes
        if msg.is_meta and msg.type == 'set_tempo':
            tempo = msg.tempo

    for msg in selected_track:
        current_time_ticks += msg.time
        
        is_note_on = msg.type == 'note_on' and msg.velocity > 0
        is_note_off = msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)

        if is_note_on:
            # If the same note is already playing, end it first.
            if msg.note in open_notes:
                start_tick = open_notes.pop(msg.note)
                start_ms = mido.tick2second(start_tick, ticks_per_beat, tempo) * 1000
                end_ms = mido.tick2second(current_time_ticks, ticks_per_beat, tempo) * 1000
                note_events.append({'start': start_ms, 'end': end_ms, 'pitch': msg.note})
            open_notes[msg.note] = current_time_ticks

        elif is_note_off:
            if msg.note in open_notes:
                start_tick = open_notes.pop(msg.note)
                start_ms = mido.tick2second(start_tick, ticks_per_beat, tempo) * 1000
                end_ms = mido.tick2second(current_time_ticks, ticks_per_beat, tempo) * 1000
                if end_ms > start_ms: # only add notes with duration
                    note_events.append({'start': start_ms, 'end': end_ms, 'pitch': msg.note})
    
    # Sort events by start time
    note_events.sort(key=lambda x: x['start'])

    if not note_events:
        print("No processable note events found in the selected track.")
        return None, None
        
    final_notes = []
    last_event_end_time = 0

    # Group overlapping notes (chords)
    processed_events = []
    if note_events:
        current_group = [note_events[0]]
        for i in range(1, len(note_events)):
            # if the current note starts before the previous one ends, it's part of a chord or overlap
            if note_events[i]['start'] < current_group[-1]['end']:
                current_group.append(note_events[i])
            else:
                processed_events.append(current_group)
                current_group = [note_events[i]]
        processed_events.append(current_group)
    
    for group in processed_events:
        highest_pitch_note = max(group, key=lambda x: x['pitch'])
        start_time = min(item['start'] for item in group)
        end_time = max(item['end'] for item in group)
        
        # Add silence if needed
        silence_duration = start_time - last_event_end_time
        if silence_duration > 1: # Use a small threshold to avoid tiny silences
            final_notes.append((0, round(silence_duration)))

        # Add the note (highest pitch from the chord)
        freq = midi_to_hz(highest_pitch_note['pitch'], transpose)
        duration = end_time - start_time
        
        if duration > 0:
            final_notes.append((round(freq), round(duration)))
        
        last_event_end_time = end_time

    # Clamp values to 16-bit range
    clamped_notes = []
    for freq, duration in final_notes:
        clamped_freq = max(0, min(20000, freq))
        clamped_duration = max(0, min(60000, duration))
        clamped_notes.append((clamped_freq, clamped_duration))

    return clamped_notes, mid.filename

def write_binary_file(notes, output_path):
    """Writes the processed notes to a binary file and returns its size."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'wb') as f:
        for freq, duration in notes:
            f.write(struct.pack('<HH', int(freq), int(duration)))

    return os.path.getsize(output_path)

def main():
    """Main function to parse arguments and run the converter."""
    parser = argparse.ArgumentParser(
        description="Convert a MIDI file track to a custom binary format.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "midi_file",
        help="Path to the input MIDI file."
    )
    parser.add_argument(
        "-k", "--key",
        type=int,
        default=0,
        help="Transpose the key by a number of semitones (e.g., -1 to lower, 1 to raise)."
    )
    args = parser.parse_args()

    processed_notes, original_filename = analyze_and_process_midi(args.midi_file, args.key)

    if processed_notes:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        base_filename = os.path.basename(original_filename)

        # Path 1: [current script path]/[original_filename].bin
        output_filename_1 = os.path.splitext(base_filename)[0] + '.bin'
        path1 = os.path.join(script_dir, output_filename_1)

        # Path 2: ../src/audio.bin
        output_dir_2 = os.path.join(script_dir, '..', 'src')
        path2 = os.path.join(output_dir_2, 'audio.bin')

        print("\n--- Writing output files ---")

        # Write file 1
        file_size1 = write_binary_file(processed_notes, path1)
        print(f"1. File created: {path1} ({file_size1} bytes)")

        # Write file 2
        file_size2 = write_binary_file(processed_notes, path2)
        print(f"2. File created: {path2} ({file_size2} bytes)")

        print("--- Success! ---")

if __name__ == "__main__":
    main()
