import numpy as np
import pyaudio
import wave
import time
from datetime import datetime

# 마이크 설정
MIC_A_INDEX = 3  # 마이크 A
MIC_B_INDEX = 2  # 마이크 B
MIC_C_INDEX = 1  # 마이크 C

# 상수 설정
CHUNK = 1024  # 오디오 버퍼 크기
RATE = 48000  # 샘플링 레이트
RECORD_SECONDS = 3600  # 최대 녹음 시간 (1시간)

# 현재 날짜 및 시간을 기반으로 파일 이름 설정
current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
LOG_FILENAME = f"sound_detection_{current_time}.log"
WAVE_FILENAME = f"recorded_combined_{current_time}.wav"

# PyAudio 초기화
p = pyaudio.PyAudio()

# 마이크 스트림 열기 (3개 마이크)
streams = [
    p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
           input_device_index=MIC_A_INDEX, frames_per_buffer=CHUNK),
    p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
           input_device_index=MIC_B_INDEX, frames_per_buffer=CHUNK),
    p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
           input_device_index=MIC_C_INDEX, frames_per_buffer=CHUNK)
]

print("Start recording... (Ctrl+C to stop)")

def log_message(message):
    """ 로그 메시지를 파일에 저장 """
    with open(LOG_FILENAME, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

try:
    frames = []
    
    start_time = time.time()
    while time.time() - start_time < RECORD_SECONDS:
        data_A = streams[0].read(CHUNK, exception_on_overflow=False)
        data_B = streams[1].read(CHUNK, exception_on_overflow=False)
        data_C = streams[2].read(CHUNK, exception_on_overflow=False)

        # 데이터를 하나의 파일에 합쳐서 저장 (단순히 이어 붙이기)
        combined_data = b''.join([data_A, data_B, data_C])
        frames.append(combined_data)

except KeyboardInterrupt:
    print("Recording stopped.")
    log_message("Recording stopped.")

finally:
    print("Saving recorded file...")

    # 하나의 파일로 저장
    wf = wave.open(WAVE_FILENAME, 'wb')
    wf.setnchannels(3)  # 3채널 오디오 파일로 저장
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # 스트림 종료
    for stream in streams:
        stream.stop_stream()
        stream.close()
    p.terminate()

    print(f"Recorded file saved: {WAVE_FILENAME}")
