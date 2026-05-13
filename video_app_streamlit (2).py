import streamlit as st
import numpy as np
import librosa
import os
import tempfile
import shutil
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, vfx

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="Beat Video Maker",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 Music Visual Maker")
st.caption("이미지와 음악을 업로드하면 음악의 흐름에 맞춰 자동으로 영상을 만들어드립니다.")

# ── 파일 업로드 ──────────────────────────────────────────────
st.subheader("📁 파일 업로드")

uploaded_images = st.file_uploader(
    "이미지 파일 (여러 개 선택 가능)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

uploaded_audio = st.file_uploader(
    "오디오 파일",
    type=["mp3", "wav", "m4a"]
)

# ── 미리보기 ─────────────────────────────────────────────────
if uploaded_images:
    st.subheader(f"🖼️ 업로드된 이미지 ({len(uploaded_images)}장)")
    cols = st.columns(min(len(uploaded_images), 5))
    for i, img in enumerate(uploaded_images):
        cols[i % 5].image(img, use_container_width=True)

if uploaded_audio:
    st.subheader("🎵 업로드된 오디오")
    st.audio(uploaded_audio)

# ── 비트 추출 함수 ────────────────────────────────────────────
def extract_beats(audio_path):
    y, sr = librosa.load(audio_path)

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=3, delta=0.5, wait=5)
    onset_times = librosa.frames_to_time(peaks, sr=sr)

    cut_points = np.unique(np.concatenate((beat_times, onset_times)))
    return cut_points

# ── 영상 생성 ─────────────────────────────────────────────────
if st.button("🎬 영상 만들기", type="primary", use_container_width=True):

    if not uploaded_images:
        st.error("이미지를 1장 이상 업로드해주세요.")
        st.stop()
    if not uploaded_audio:
        st.error("오디오 파일을 업로드해주세요.")
        st.stop()

    with tempfile.TemporaryDirectory() as tmp_dir:
        progress = st.progress(0, text="파일 저장 중...")

        # 이미지 저장
        image_paths = []
        for i, img in enumerate(uploaded_images):
            ext = os.path.splitext(img.name)[-1]
            path = os.path.join(tmp_dir, f"img_{i}{ext}")
            with open(path, "wb") as f:
                f.write(img.read())
            image_paths.append(path)

        # 오디오 저장
        audio_path = os.path.join(tmp_dir, uploaded_audio.name)
        with open(audio_path, "wb") as f:
            f.write(uploaded_audio.read())

        progress.progress(20, text="비트 분석 중...")

        # 비트 추출
        try:
            cut_points = extract_beats(audio_path)
        except Exception as e:
            st.error(f"오디오 분석 실패: {e}")
            st.stop()

        progress.progress(40, text="클립 구성 중...")

        audio_clip = AudioFileClip(audio_path)
        n = len(image_paths)

        # cut_points를 이미지 수에 맞게 조정
        if len(cut_points) > n:
            idx = np.linspace(0, len(cut_points) - 1, n).astype(int)
            cut_points = cut_points[idx]
        elif len(cut_points) < n:
            cut_points = np.linspace(0, audio_clip.duration, n, endpoint=False)

        clips = []
        for i in range(n):
            start = cut_points[i]
            end = cut_points[i + 1] if i + 1 < len(cut_points) else audio_clip.duration
            duration = max(3.0, end - start)  # 풍경화: 최소 3초 유지

            clip = (
                ImageClip(image_paths[i])
                .with_duration(duration)
                .with_effects([vfx.FadeIn(1.0), vfx.FadeOut(1.0)])  # 부드러운 1초 전환
            )
            clips.append(clip)

        progress.progress(60, text="영상 렌더링 중... (시간이 걸릴 수 있습니다)")

        # 영상 합성
        try:
            video = concatenate_videoclips(clips, method="compose")
            video = video.with_audio(audio_clip)

            output_path = os.path.join(tmp_dir, "result.mp4")
            video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                ffmpeg_params=["-pix_fmt", "yuv420p", "-vf", "crop=trunc(iw/2)*2:trunc(ih/2)*2"],
                logger=None
            )
        except Exception as e:
            st.error(f"영상 생성 실패: {e}")
            st.stop()

        progress.progress(90, text="다운로드 준비 중...")

        # 결과 파일 읽기
        with open(output_path, "rb") as f:
            video_bytes = f.read()

        progress.progress(100, text="완료!")

    # ── 결과 출력 ──────────────────────────────────────────────
    st.success("✅ 영상이 완성됐습니다!")
    st.video(video_bytes)

    st.download_button(
        label="⬇️ 영상 다운로드",
        data=video_bytes,
        file_name="beat_video.mp4",
        mime="video/mp4",
        use_container_width=True
    )
