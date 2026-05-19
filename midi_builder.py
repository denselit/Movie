import streamlit as st
from midiutil import MIDIFile
from io import BytesIO
import pandas as pd
import re

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Neo-Classical Motif Sketchpad",
    page_icon="🎼",
    layout="wide"
)

# --------------------------------------------------
# NOTE SYSTEM
# --------------------------------------------------

NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]

NOTE_BASE = {
    "도": 0,
    "레": 2,
    "미": 4,
    "파": 5,
    "솔": 7,
    "라": 9,
    "시": 11
}

CHORD_SUGGESTIONS = [
    "Am(add9)",
    "Dm9",
    "Fmaj7"
]

# --------------------------------------------------
# MIDI → NOTE NAME
# --------------------------------------------------

def midi_to_name(midi_note):

    note = NOTE_NAMES[midi_note % 12]
    octave = (midi_note // 12) - 1

    return f"{note}{octave}"

# --------------------------------------------------
# PARSE SINGLE NOTE
# Example:
# 라4
# 도#5
# 미♭3
# --------------------------------------------------

def parse_note(note_text):

    pattern = r"([도레미파솔라시])([#♯b♭]?)(\d)"

    match = re.match(pattern, note_text)

    if not match:
        return None

    note_name, accidental, octave = match.groups()

    semitone = NOTE_BASE[note_name]

    # Sharp
    if accidental in ["#", "♯"]:
        semitone += 1

    # Flat
    if accidental in ["b", "♭"]:
        semitone -= 1

    midi_note = semitone + ((int(octave) + 1) * 12)

    return midi_note

# --------------------------------------------------
# PARSE MELODY TEXT
# --------------------------------------------------

def parse_melody(text):

    parsed_sequence = []

    phrases = [
        p.strip()
        for p in text.split("/")
        if p.strip()
    ]

    for phrase_index, phrase in enumerate(phrases):

        notes = phrase.split()

        for note_index, note_text in enumerate(notes):

            midi_note = parse_note(note_text)

            if midi_note is None:
                continue

            # Default values
            duration = 1.0
            velocity = 90

            # Softer ending phrase
            if phrase_index == len(phrases) - 1:
                duration = 2.0
                velocity = 72

            # Final note
            if (
                phrase_index == len(phrases) - 1
                and note_index == len(notes) - 1
            ):
                duration = 3.0
                velocity = 60

            parsed_sequence.append({
                "note": midi_note,
                "duration": duration,
                "velocity": velocity
            })

    return parsed_sequence

# --------------------------------------------------
# CREATE MIDI
# --------------------------------------------------

def create_midi(sequence, bpm=72):

    midi = MIDIFile(1)

    track = 0
    channel = 0
    time = 0

    midi.addTempo(track, time, bpm)

    current_time = 0

    for note_data in sequence:

        midi.addNote(
            track=track,
            channel=channel,
            pitch=note_data["note"],
            time=current_time,
            duration=note_data["duration"],
            volume=note_data["velocity"]
        )

        current_time += note_data["duration"]

    output = BytesIO()

    midi.writeFile(output)

    output.seek(0)

    return output

# --------------------------------------------------
# UI
# --------------------------------------------------

st.title("🎼 Neo-Classical Motif Sketchpad")

st.markdown("""
A melody-first composition tool designed for:

- Korean note input with octave support
- cinematic phrasing
- neo-classical motif sketching
- expressive timing & velocity
- MIDI export
""")

col1, col2 = st.columns([2, 1])

# --------------------------------------------------
# LEFT PANEL
# --------------------------------------------------

with col1:

    st.subheader("Melody Input")

    solfege_input = st.text_area(
        "Enter melody",
        value="라4 시4 도5 시4 / 레5 도5 시4 라4 / 파4 미4",
        height=140
    )

    st.caption("""
Examples:
- 라4 시4 도5
- 파#4 솔4 라♭4
- Use / for phrase separation
""")

    parsed_sequence = parse_melody(solfege_input)

    melody_data = []

    st.subheader("Parsed Melody Sequence")

    for i, note_data in enumerate(parsed_sequence):

        note_label = midi_to_name(note_data["note"])

        with st.expander(f"Note {i+1} — {note_label}"):

            c1, c2, c3 = st.columns(3)

            unique_key = (
                f"{i}_"
                f"{note_data['note']}_"
                f"{note_data['duration']}"
            )

            with c1:

                pitch = st.slider(
                    "MIDI Note",
                    min_value=24,
                    max_value=108,
                    value=note_data["note"],
                    key=f"pitch_{unique_key}"
                )

            with c2:

                duration = st.slider(
                    "Duration",
                    min_value=0.25,
                    max_value=6.0,
                    value=float(note_data["duration"]),
                    step=0.25,
                    key=f"dur_{unique_key}"
                )

            with c3:

                velocity = st.slider(
                    "Velocity",
                    min_value=20,
                    max_value=127,
                    value=note_data["velocity"],
                    key=f"vel_{unique_key}"
                )

            melody_data.append({
                "note": pitch,
                "duration": duration,
                "velocity": velocity
            })

# --------------------------------------------------
# RIGHT PANEL
# --------------------------------------------------

with col2:

    st.subheader("Harmonic Direction")

    for chord in CHORD_SUGGESTIONS:

        st.markdown(f"### {chord}")

    st.divider()

    bpm = st.slider(
        "Tempo (BPM)",
        min_value=40,
        max_value=180,
        value=72
    )

    st.divider()

    st.markdown("### Phrase Shape")

    st.markdown("""
- Ascending opening
- Descending response
- Suspended ending
""")

    st.divider()

    st.markdown("### Expression")

    st.markdown("""
- Longer ending durations
- Softer final phrase
- Neo-classical cadence shaping
""")

# --------------------------------------------------
# TABLE
# --------------------------------------------------

st.divider()

st.subheader("Sequence Table")

sequence_df = pd.DataFrame([
    {
        "Note": midi_to_name(n["note"]),
        "MIDI": n["note"],
        "Duration": n["duration"],
        "Velocity": n["velocity"]
    }
    for n in melody_data
])

st.dataframe(
    sequence_df,
    use_container_width=True
)

# --------------------------------------------------
# MIDI EXPORT
# --------------------------------------------------

midi_file = create_midi(
    melody_data,
    bpm=bpm
)

st.download_button(
    label="⬇ Download MIDI",
    data=midi_file,
    file_name="neo_classical_motif.mid",
    mime="audio/midi"
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown("""
### Future Expansion Ideas

- AI chord suggestion
- motif variation engine
- orchestration layer
- piano roll visualization
- counterpoint assistant
- MusicGen / Magenta integration
""")

st.caption(
    "Built for melody-first cinematic composition sketching."
)
