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

# ── 음악 변화 감지 함수 (클래식 최적화) ──────────────────────
def extract_musical_changes(audio_path, n_images, min_sec=3.0):
    """
    beat 대신 음악의 성격 변화를 감지:
      - 스펙트럴 플럭스 : 악기 음색 변화
      - 크로마 플럭스   : 화성(코드) 변화
      - RMS 에너지      : 셈/여림 변화
    세 신호를 합산 → 가장 강한 변화 지점 n_images개 선택
    """
    y, sr = librosa.load(audio_path)
    duration = librosa.get_duration(y=y, sr=sr)
    hop = 512

    def norm(x):
        r = x.max() - x.min()
        return (x - x.min()) / r if r > 0 else x

    # 1) 스펙트럴 플럭스 (음색 변화)
    flux = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop, aggregate=np.median)

    # 2) 크로마 플럭스 (화성 변화)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    chroma_flux = np.sum(np.abs(np.diff(chroma, axis=1)), axis=0)
    chroma_flux = np.concatenate([[0], chroma_flux])

    # 3) RMS 에너지 변화량
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms_diff = np.abs(np.diff(rms))
    rms_diff = np.concatenate([[0], rms_diff])

    # 세 신호 합산 (가중치: 음색 40% + 화성 40% + 에너지 20%)
    combined = 0.4 * norm(flux) + 0.4 * norm(chroma_flux) + 0.2 * norm(rms_diff)

    # 최소 간격 = min_sec 초
    min_frames = max(1, int(sr * min_sec / hop))

    peaks = librosa.util.peak_pick(
        combined,
        pre_max=min_frames, post_max=min_frames,
        pre_avg=min_frames, post_avg=min_frames,
        delta=0.15, wait=min_frames
    )
    peak_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop)

    # 이미지 수만큼 가장 강한 변화 지점 선택
    if len(peaks) >= n_images:
        strengths = combined[peaks]
        top_idx = np.argsort(strengths)[-n_images:]
        cut_times = np.sort(peak_times[top_idx])
    else:
        # 감지된 변화가 적으면 균등 분할로 보충
        extra = np.linspace(0, duration, n_images - len(peak_times) + 2)[1:-1]
        cut_times = np.sort(np.unique(np.concatenate([peak_times, extra])))[:n_images]

    return cut_times

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

        progress.progress(20, text="음악 분석 중...")

        # 음악 변화 감지
        try:
            cut_points = extract_musical_changes(audio_path, n_images=len(image_paths), min_sec=3.0)
        except Exception as e:
            st.error(f"오디오 분석 실패: {e}")
            st.stop()

        progress.progress(40, text="클립 구성 중...")

        audio_clip = AudioFileClip(audio_path)
        n = len(image_paths)

        # cut_points가 n보다 적으면 균등 분할로 보충
        if len(cut_points) < n:
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
                ffmpeg_params=["-pix_fmt", "yuv420p"],
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
