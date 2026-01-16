import mido
import argparse
import struct
import os
import math
from typing import List, Tuple, Dict, Optional

def midi_to_hz(note: int, transpose: int = 0) -> float:
    """
    Converts a MIDI note number to frequency in Hz, applying transposition.
    MIDI 노트 번호를 주파수(Hz)로 변환합니다. (조옮김 적용)
    """
    if note == 0:
        return 0
    note += transpose
    return 440 * 2**((note - 69) / 12)

def analyze_and_process_midi(
    midi_path: str, 
    transpose: int, 
    num_channels: int = 1,
    target_bpm: Optional[float] = None, 
    max_beats: Optional[float] = None
) -> Tuple[Optional[List[Tuple[int, List[int]]]], Optional[str]]:
    """
    Analyzes a MIDI file, prompts the user to select a track,
    and processes it into a list of (duration, [freq_0, freq_1, ...]) tuples.
    MIDI 파일을 분석하고 트랙을 선택받아 다채널 주파수 데이터로 변환합니다.
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

    print(f"Processing Track {selected_track_num} with {num_channels} channels...")

    # --- Note Processing ---
    selected_track = mid.tracks[selected_track_num]
    ticks_per_beat = mid.ticks_per_beat
    
    if target_bpm:
        tempo = mido.bpm2tempo(target_bpm)
        print(f"Using manual BPM: {target_bpm} (Tempo: {tempo})")
    else:
        tempo = 500000  # Default MIDI tempo (120 BPM)
        # Only detect tempo if not manually specified
        # Merge tracks to get global tempo changes
        for msg in mido.merge_tracks(mid.tracks): 
            if msg.is_meta and msg.type == 'set_tempo':
                tempo = msg.tempo
        print(f"Detected Tempo: {tempo} (BPM: {mido.tempo2bpm(tempo):.2f})")

    limit_ticks = None
    if max_beats is not None:
        limit_ticks = int(max_beats * ticks_per_beat)
        print(f"Limit set to {max_beats} beats ({limit_ticks} ticks)")

    # 1. Extract raw notes (Start Tick, End Tick, Pitch)
    # 원시 노트 데이터 추출 (시작 틱, 종료 틱, 음정)
    raw_notes = []
    current_time_ticks = 0
    open_notes = {} # {note: start_tick}

    for msg in selected_track:
        current_time_ticks += msg.time
        
        if limit_ticks is not None and current_time_ticks > limit_ticks:
            break

        is_note_on = msg.type == 'note_on' and msg.velocity > 0
        is_note_off = msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)

        if is_note_on:
            # If the same note is already playing, end it first (monophonic per key).
            if msg.note in open_notes:
                start_tick = open_notes.pop(msg.note)
                raw_notes.append({'start_tick': start_tick, 'end_tick': current_time_ticks, 'pitch': msg.note})
            open_notes[msg.note] = current_time_ticks

        elif is_note_off:
            if msg.note in open_notes:
                start_tick = open_notes.pop(msg.note)
                if current_time_ticks > start_tick: # only add notes with duration
                    raw_notes.append({'start_tick': start_tick, 'end_tick': current_time_ticks, 'pitch': msg.note})
    
    # Sort notes: Primary by Start Time (ASC), Secondary by Pitch (DESC)
    # 시작 시간 오름차순, 음정 내림차순 정렬 (높은 음 우선 선택을 위함)
    raw_notes.sort(key=lambda x: (x['start_tick'], -x['pitch']))

    if not raw_notes:
        print("No processable note events found in the selected track.")
        return None, None
        
    final_events = [] # List[Tuple(duration_ms, List[freq_hz])]
    current_tick = 0
    
    # 2. Process Timeline (Greedy Algorithm for Channels)
    # 타임라인 처리 (채널 할당을 위한 그리디 알고리즘)
    # raw_notes를 순회하며 시간 순서대로 블록을 만듭니다.
    
    note_idx = 0
    total_notes = len(raw_notes)
    
    while note_idx < total_notes:
        # Find the next valid note that starts on or after current_tick
        # 현재 시점 이후에 시작하는 유효한 노트를 찾습니다.
        next_valid_note = None
        
        while note_idx < total_notes:
            candidate = raw_notes[note_idx]
            if candidate['start_tick'] >= current_tick:
                next_valid_note = candidate
                break
            # Skip notes that started in the past (overlap handling: discard)
            # 이미 지난 시점에 시작된 겹치는 노트는 버립니다.
            note_idx += 1
            
        if next_valid_note is None:
            break
            
        # Add silence gap if needed
        # 노트 시작 전 빈 공간이 있으면 무음(0Hz)으로 채웁니다.
        if next_valid_note['start_tick'] > current_tick:
            gap_duration_tick = next_valid_note['start_tick'] - current_tick
            gap_ms = mido.tick2second(gap_duration_tick, ticks_per_beat, tempo) * 1000
            if gap_ms > 1: # Ignore tiny gaps
                final_events.append((round(gap_ms), [0] * num_channels))
            current_tick = next_valid_note['start_tick']
            
        # Identify Chord Group
        # "화음 그룹" 정의: 시작 시간과 종료 시간이 정확히 일치하는 노트들
        # 기준 노트(next_valid_note)와 start/end가 같은 노트들을 수집합니다.
        
        target_start = next_valid_note['start_tick']
        target_end = next_valid_note['end_tick']
        
        chord_candidates = []
        
        # Look ahead in the sorted list for matches
        # 정렬된 리스트에서 같은 구간을 가진 노트들을 찾습니다.
        temp_idx = note_idx
        while temp_idx < total_notes:
            note = raw_notes[temp_idx]
            if note['start_tick'] > target_start:
                break # 더 늦게 시작하는 노트가 나오면 탐색 중단
            
            if note['start_tick'] == target_start and note['end_tick'] == target_end:
                chord_candidates.append(note)
            
            temp_idx += 1
            
        # Select notes for channels
        # 채널 개수에 맞춰 노트 선택 (이미 Pitch 내림차순 정렬되어 있음)
        selected_notes = chord_candidates[:num_channels]
        
        # Create Frequency List
        # 주파수 리스트 생성
        freqs = []
        for note in selected_notes:
            hz = midi_to_hz(note['pitch'], transpose)
            freqs.append(round(hz))
        
        # Pad with 0Hz if fewer notes than channels
        # 노트가 채널보다 적으면 0Hz로 채움
        while len(freqs) < num_channels:
            freqs.append(0)
            
        duration_tick = target_end - target_start
        duration_ms = mido.tick2second(duration_tick, ticks_per_beat, tempo) * 1000
        
        if duration_ms > 0:
            final_events.append((round(duration_ms), freqs))
            
        # Advance time
        # 시간 진행
        current_tick = target_end
        
        # Note index will be updated in the next while loop iteration to skip overlapped notes
        # 다음 루프에서 current_tick보다 이전에 시작하는 노트들은 자동으로 건너뛰게 됩니다.

    # Clamp values to 16-bit range
    clamped_events = []
    for duration, freqs in final_events:
        clamped_duration = max(0, min(60000, duration)) # Max 60s per block
        clamped_freqs = [max(0, min(20000, f)) for f in freqs] # Max 20kHz
        clamped_events.append((clamped_duration, clamped_freqs))

    return clamped_events, mid.filename

def write_binary_file(events: List[Tuple[int, List[int]]], output_path: str, num_channels: int) -> int:
    """
    Writes the processed events to a binary file and returns its size.
    Format: Duration(2B) + Freq_0(2B) + ... + Freq_N(2B) (Little Endian)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Format string: <H (Duration) + H...H (Frequencies)
    fmt = '<H' + 'H' * num_channels
    
    with open(output_path, 'wb') as f:
        for duration, freqs in events:
            # Ensure freqs matches num_channels (safety check)
            if len(freqs) != num_channels:
                 # Should not happen if logic is correct, but pad/truncate just in case
                freqs = freqs[:num_channels] + [0] * (num_channels - len(freqs))
            
            f.write(struct.pack(fmt, int(duration), *freqs))

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
    parser.add_argument(
        "-b", "--bpm",
        type=float,
        default=None,
        help="Manually set the BPM (overrides MIDI file tempo)."
    )
    parser.add_argument(
        "-l", "--length",
        type=float,
        default=None,
        help="Limit the conversion to a specific number of beats (e.g., 120 or 100.25)."
    )
    parser.add_argument(
        "-c", "--channels",
        type=int,
        default=1,
        help="Number of channels (voices) to extract. Default: 1"
    )
    args = parser.parse_args()

    processed_events, original_filename = analyze_and_process_midi(
        args.midi_file, 
        args.key, 
        args.channels, 
        args.bpm, 
        args.length
    )

    if processed_events:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        base_filename = os.path.basename(original_filename)

        # Path 1: [current script path]/[original_filename].bin
        output_filename_1 = os.path.splitext(base_filename)[0] + '.bin'
        path1 = os.path.join(script_dir, output_filename_1)

        # Path 2: ../src/audio.bin
        output_dir_2 = os.path.join(script_dir, '..', 'src')
        path2 = os.path.join(output_dir_2, 'audio.bin')

        print("\n--- Writing output files ---")
        print(f"Format: Duration (ms) + {args.channels} x Frequency (Hz)")

        # Write file 1
        file_size1 = write_binary_file(processed_events, path1, args.channels)
        print(f"1. File created: {path1} ({file_size1} bytes)")

        # Write file 2
        file_size2 = write_binary_file(processed_events, path2, args.channels)
        print(f"2. File created: {path2} ({file_size2} bytes)")

        print("--- Success! ---")

if __name__ == "__main__":
    main()