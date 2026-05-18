import streamlit as st
from midiutil import MIDIFile
from io import BytesIO
import pandas as pd

st.set_page_config(
    page_title="Neo-Classical MIDI Builder",
    page_icon="🎼",
    layout="wide"
)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

DEFAULT_MELODY = [
    {"note": 57, "duration": 1.0, "velocity": 92},
    {"note": 59, "duration": 1.0, "velocity": 90},
    {"note": 60, "duration": 1.0, "velocity": 94},
    {"note": 59, "duration": 1.0, "velocity": 88},

    {"note": 62, "duration": 1.0, "velocity": 96},
    {"note": 60, "duration": 1.0, "velocity": 90},
    {"note": 59, "duration": 1.0, "velocity": 84},
    {"note": 57, "duration": 1.0, "velocity": 82},

    {"note": 65, "duration": 2.0, "velocity": 76},
    {"note": 64, "duration": 3.0, "velocity": 62},
]

CHORDS = [
    "Am(add9)",
    "Dm9",
    "Fmaj7"
]


def midi_to_name(midi_note):
    note = NOTE_NAMES[midi_note % 12]
    octave = (midi_note // 12) - 1
    return f"{note}{octave}"


def create_midi(sequence, bpm=72):
    midi = MIDIFile(1)

    track = 0
    channel = 0
    time = 0

    midi.addTempo(track, time, bpm)

    current_time = 0

    for n in sequence:
        midi.addNote(
            track=track,
            channel=channel,
            pitch=n["note"],
            time=current_time,
            duration=n["duration"],
            volume=n["velocity"]
        )

        current_time += n["duration"]

    output = BytesIO()
    midi.writeFile(output)
    output.seek(0)

    return output


st.title("🎼 Neo-Classical MIDI Builder")

st.markdown(
    """
A sequence-based MIDI sketch tool designed for:

- melodic phrasing
- cinematic harmony
- neo-classical motif writing
- expressive velocity shaping
- MIDI export
"""
)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Melody Sequence")

    melody_data = []

    for i, note_data in enumerate(DEFAULT_MELODY):
        with st.expander(f"Note {i+1} — {midi_to_name(note_data['note'])}"):
            c1, c2, c3 = st.columns(3)

            with c1:
                pitch = st.slider(
                    "MIDI Note",
                    min_value=36,
                    max_value=96,
                    value=note_data["note"],
                    key=f"pitch_{i}"
                )

            with c2:
                duration = st.slider(
                    "Duration",
                    min_value=0.25,
                    max_value=4.0,
                    value=float(note_data["duration"]),
                    step=0.25,
                    key=f"dur_{i}"
                )

            with c3:
                velocity = st.slider(
                    "Velocity",
                    min_value=20,
                    max_value=127,
                    value=note_data["velocity"],
                    key=f"vel_{i}"
                )

            melody_data.append({
                "note": pitch,
                "duration": duration,
                "velocity": velocity
            })

with col2:
    st.subheader("Harmonic Direction")

    for chord in CHORDS:
        st.markdown(f"### {chord}")

    st.divider()

    bpm = st.slider(
        "Tempo (BPM)",
        min_value=40,
        max_value=160,
        value=72
    )

    st.markdown("### Phrase Structure")

    st.markdown(
        """
- A B C B
- D C B A
- F → E
"""
    )

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

st.dataframe(sequence_df, use_container_width=True)

midi_file = create_midi(melody_data, bpm=bpm)

st.download_button(
    label="⬇ Download MIDI",
    data=midi_file,
    file_name="neo_classical_motif.mid",
    mime="audio/midi"
)

st.divider()

st.markdown(
    """
### Future Expansion Ideas

- AI chord suggestion
- motif variation engine
- orchestration layer
- cinematic tension analysis
- MusicGen / Magenta integration
- piano roll visualization
"""
)

st.caption("Built for cinematic neo-classical composition sketching.")
