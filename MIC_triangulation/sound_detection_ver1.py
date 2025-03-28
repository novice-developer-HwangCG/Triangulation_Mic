"""LOG 메세지 저장만 가능"""
import numpy as np
import pyaudio
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

# 현재 날짜 및 시간을 기반으로 파일 이름 설정
current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
LOG_FILENAME = f"sound_detection_{current_time}.log"

# 마이크 인덱스 설정
MIC_A_INDEX = 3
MIC_B_INDEX = 2
MIC_C_INDEX = 1

# PyAudio 초기화
p = pyaudio.PyAudio()

# 마이크 스트림 열기
streams = [
    p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
           input_device_index=MIC_A_INDEX, frames_per_buffer=CHUNK),
    p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
           input_device_index=MIC_B_INDEX, frames_per_buffer=CHUNK),
    p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
           input_device_index=MIC_C_INDEX, frames_per_buffer=CHUNK)
]

print("Start noise detection... (Ctrl+C to exit)")

def log_message(message):
    """ 로그 메시지를 파일에 저장 """
    with open(LOG_FILENAME, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def detect_sound():
    """ 마이크에서 소리를 감지하고 감지된 마이크 위치 및 시간을 반환 """
    while True:
        volumes = [np.max(np.abs(np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16))) for stream in streams]
        detected = [1 if vol > THRESHOLD else 0 for vol in volumes]
        detected_mics = [mic_positions[i] for i in range(3) if detected[i]]
        detected_times = [time.time() for i in range(3) if detected[i]]
        
        print(f"Mic states: {detected}")
        log_message(f"Mic states: {detected}")
        
        if detected_mics:
            return detected_mics, detected_times

def estimate_impact_location(detected_mics, detected_times):
    """ 감지된 마이크 데이터를 기반으로 충격음 위치를 추정 """
    detected_mics = np.array(detected_mics)
    detected_times = np.array(detected_times)
    time_differences = detected_times - min(detected_times)

    def loss_function(estimated_source):
        estimated_distances = np.linalg.norm(detected_mics - estimated_source, axis=1)
        estimated_times = estimated_distances / SOUND_SPEED
        return np.sum((estimated_times - min(estimated_times) - time_differences) ** 2)

    initial_guess = np.mean(detected_mics, axis=0)
    result = minimize(loss_function, initial_guess, method='Nelder-Mead')
    return result.x

try:
    start_time = time.time()
    while True:
        detected_mics, detected_times = detect_sound()
        if detected_mics:
            estimated_location = estimate_impact_location(detected_mics, detected_times)
            print(f"Estimated impact location (mm): {estimated_location}")
            log_message(f"Estimated impact location (mm): {estimated_location}")
except KeyboardInterrupt:
    print("Noise detection shutdown.")
    log_message("Noise detection shutdown.")
finally:
    for stream in streams:
        stream.stop_stream()
        stream.close()
    p.terminate()
