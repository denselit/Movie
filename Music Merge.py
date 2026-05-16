import streamlit as st
from pydub import AudioSegment
import io

st.set_page_config(page_title="MP3 자연스럽게 합치기", page_icon="🎵")

st.title("🎵 자연스러운 MP3 병합기 (Crossfade)")
st.write("스마트폰이나 PC에서 여러 MP3 파일을 부드럽게 이어 붙여보세요.")

# 1. 파일 업로드
uploaded_files = st.file_uploader(
    "합칠 MP3 파일들을 업로드하세요 (선택한 순서대로 합쳐집니다)", 
    type=["mp3"], 
    accept_multiple_files=True
)

# 2. 크로스페이드 시간 설정 (사용자 편의를 위해 초 단위 슬라이더 제공)
crossfade_sec = st.slider("크로스페이드 시간 (초)", min_value=0.0, max_value=5.0, value=2.0, step=0.5)
crossfade_ms = int(crossfade_sec * 1000)

# 3. 병합 로직
if uploaded_files:
    if len(uploaded_files) < 2:
        st.warning("병합을 위해 2개 이상의 파일을 업로드해 주세요.")
    else:
        st.info(f"총 {len(uploaded_files)}개의 파일이 대기 중입니다.")
        
        if st.button("✨ 크로스페이드로 병합하기"):
            with st.spinner("음원을 자연스럽게 섞는 중입니다... 잠시만 기다려주세요!"):
                try:
                    # 첫 번째 음원 로드
                    combined = AudioSegment.from_file(uploaded_files[0], format="mp3")
                    
                    # 두 번째 음원부터 순차적으로 병합
                    for file in uploaded_files[1:]:
                        next_audio = AudioSegment.from_file(file, format="mp3")
                        combined = combined.append(next_audio, crossfade=crossfade_ms)
                    
                    # 스트림으로 변환하여 메모리에 저장 (서버 용량 차지 방지)
                    buffer = io.BytesIO()
                    combined.export(buffer, format="mp3")
                    buffer.seek(0)
                    
                    st.success("성공적으로 병합되었습니다! 아래 버튼을 눌러 다운로드하세요.")
                    
                    # 다운로드 버튼 생성
                    st.download_button(
                        label="📥 병합된 MP3 다운로드",
                        data=buffer,
                        file_name="merged_crossfade.mp3",
                        mime="audio/mpeg"
                    )
                    
                except Exception as e:
                    st.error(f"병합 중 오류가 발생했습니다: {e}")
