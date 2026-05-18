import streamlit as st
from midiutil import MIDIFile
from io import BytesIO
import pandas as pd

st.set_page_config(
    page_title="Neo-Classical Motif Sketchpad",
    page_icon="🎼",
    layout="wide"
)

NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]

KOREAN_NOTE_MAP = {
    "도": 60,
    "레": 62,
    "미": 64,
    "파": 65,
    "솔": 67,
    "라": 69,
    "시": 71
}

CHORD_SUGGESTIONS = [
    "Am(add9)",
    "Dm9",
    "Fmaj7"
]


def midi_to_name(midi_note):
    note = NOTE_NAMES[midi_note % 12]
    octave = (midi_note // 12) - 1
    return f"{note}{octave}"


def parse_korean_melody(text):
    parsed_sequence = []

    phrases = [
        p.strip()
        for p in text.split("/")
        if p.strip()
    ]

    for phrase_index, phrase in enumerate(phrases):
        notes = phrase.split()

        for note_index, note_name in enumerate(notes):

            if note_name not in KOREAN_NOTE_MAP:
                continue

            midi_note = KOREAN_NOTE_MAP[note_name]

            # 기본 duration
            duration = 1.0

            # 마지막 phrase는 더 길게
            if phrase_index == len(phrases) - 1:
                duration = 2.0

            # 마지막 note는 가장 길게
            if (
                phrase_index == len(phrases) - 1
                and note_index == len(notes) - 1
            ):
                duration = 3.0

            # velocity shaping
            velocity = 90

            if phrase_index == len(phrases) - 1:
                velocity = 72

            parsed_sequence.append({
                "note": midi_note,
                "duration": duration,
                "velocity": velocity
            })

    return parsed_sequence


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


# ---------------- UI ---------------- #

st.title("🎼 Neo-Classical Motif Sketchpad")

st.markdown("""
A melody-first composition tool designed for:

- Korean solfege melody input
- cinematic phrasing
- neo-classical motif sketching
- expressive timing & velocity
- MIDI export
""")

col1, col2 = st.columns([2, 1])

# ---------------- LEFT ---------------- #

with col1:

    st.subheader("Korean Solfege Input")

    solfege_input = st.text_area(
        "Enter melody",
        value="라 시 도 시 / 레 도 시 라 / 파 미",
        height=120
    )

    st.caption(
        "Use spaces between notes and / for phrase separation"
    )

    parsed_sequence = parse_korean_melody(solfege_input)

    melody_data = []

    st.subheader("Parsed Melody Sequence")

    for i, note_data in enumerate(parsed_sequence):

        note_label = midi_to_name(note_data["note"])

        with st.expander(f"Note {i+1} — {note_label}"):

            c1, c2, c3 = st.columns(3)

            # 고유 key 생성
            unique_key = f"{i}_{note_data['note']}_{note_data['duration']}"

            with c1:

                pitch = st.slider(
                    "MIDI Note",
                    min_value=36,
                    max_value=96,
                    value=note_data["note"],
                    key=f"pitch_{unique_key}"
                )

            with c2:

                duration = st.slider(
                    "Duration",
                    min_value=0.25,
                    max_value=4.0,
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

# ---------------- RIGHT ---------------- #

with col2:

    st.subheader("Harmonic Direction")

    for chord in CHORD_SUGGESTIONS:
        st.markdown(f"### {chord}")

    st.divider()

    bpm = st.slider(
        "Tempo (BPM)",
        min_value=40,
        max_value=160,
        value=72
    )

    st.markdown("### Phrase Structure")

    st.markdown("""
- A B C B
- D C B A
- F → E
""")

# ---------------- TABLE ---------------- #

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

# ---------------- MIDI EXPORT ---------------- #

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

# ---------------- FOOTER ---------------- #

st.divider()

st.markdown("""
### Future Expansion Ideas

- AI chord suggestion
- motif variation engine
- orchestration layer
- cinematic tension analysis
- piano roll visualization
- MusicGen / Magenta integration
""")

st.caption(
    "Built for melody-first cinematic composition sketching."
)
