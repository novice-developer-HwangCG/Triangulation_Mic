import numpy as np
import pyaudio
import wave
import time
from datetime import datetime
from scipy.optimize import minimize

# 마이크 위치 설정 (mm 단위)
mic_positions = np.array([
    [250, 1000],  # 마이크 A (x=25cm, y=100cm)
    [0, 0],       # 마이크 B (x=0cm, y=0cm)
    [500, 0]      # 마이크 C (x=50cm, y=0cm)
])

# 상수 설정
SOUND_SPEED = 343000  # mm/s (공기 중 음속)
CHUNK = 1024  # 오디오 버퍼 크기
RATE = 48000  # 샘플링 레이트 (마이크 테스트 후 수정)
THRESHOLD = 3000  # 소리 감지 임계값
RECORD_SECONDS = 3600  # 최대 녹음 시간 (1시간)

# 현재 날짜 및 시간을 기반으로 파일 이름 설정
current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
LOG_FILENAME = f"sound_detection_{current_time}.log"
WAVE_OUTPUT_FILENAME = f"recorded_sound_{current_time}.wav"

# 마이크 인덱스 설정
MIC_A_INDEX = 1
MIC_B_INDEX = 2
MIC_C_INDEX = 3

# PyAudio 초기화
p = pyaudio.PyAudio()

# 마이크 스트림 열기
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                input_device_index=MIC_A_INDEX, frames_per_buffer=CHUNK)

print("Start noise detection... (Ctrl+C to exit)")

def log_message(message):
    """ 로그 메시지를 파일에 저장 """
    with open(LOG_FILENAME, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

try:
    frames = []
    start_time = time.time()
    
    while time.time() - start_time < RECORD_SECONDS:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

except KeyboardInterrupt:
    print("Noise detection shutdown.")
    log_message("Noise detection shutdown.")
    
finally:
    print("Saving recorded audio...")
    
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    print(f"녹음된 파일 저장 완료: {WAVE_OUTPUT_FILENAME}")
