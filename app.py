import streamlit as st
from moviepy import (
    AudioFileClip,
    ImageClip,
    concatenate_videoclips
)
import tempfile
import librosa
import numpy as np

st.title("🎵 Beat Sync Video Maker")

uploaded_images = st.file_uploader(
    "사진 업로드",
    type=["jpg", "png"],
    accept_multiple_files=True
)

uploaded_audio = st.file_uploader(
    "음악 업로드",
    type=["mp3", "wav"]
)

if st.button("영상 만들기"):

    if uploaded_images and uploaded_audio:

        # 오디오 임시 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
            tmp_audio.write(uploaded_audio.read())
            audio_path = tmp_audio.name

        audio_clip = AudioFileClip(audio_path)

        # 비트 추출
        y, sr = librosa.load(audio_path)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)

        # 이미지 처리
        clips = []

        duration = audio_clip.duration / len(uploaded_images)

        for img in uploaded_images:

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
                tmp_img.write(img.read())

                clip = (
                    ImageClip(tmp_img.name)
                    .set_duration(duration)
                    .fadein(0.3)
                    .fadeout(0.3)
                )

                clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(audio_clip)

        output_path = "output.mp4"

        video.write_videofile(output_path, fps=24)

        st.success("완료!")

        st.video(output_path)
