import numpy as np
import pyaudio
import time
from scipy.optimize import minimize

# 마이크 위치 설정 (mm 단위)
mic_positions = np.array([
    [300, 0],   # 마이크 1 (x=300mm, y=0mm)
    [600, 0],   # 마이크 2 (x=600mm, y=0mm)
])

# 상수 설정
SOUND_SPEED = 343000  # mm/s (공기 중 음속)
CHUNK = 1024  # 오디오 버퍼 크기
RATE = 48000  # 샘플링 레이트 (마이크 테스트 후 수정)
THRESHOLD = 3000  # 소리 감지 임계값

# 마이크 인덱스 설정 (mic_check.py 실행 결과 확인)
MIC1_INDEX = 1
MIC2_INDEX = 2

# PyAudio 초기화
p = pyaudio.PyAudio()

# 마이크 1, 2 스트림 열기
stream1 = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                 input_device_index=MIC1_INDEX, frames_per_buffer=CHUNK)

stream2 = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                 input_device_index=MIC2_INDEX, frames_per_buffer=CHUNK)

print("Start noise detection... (Ctrl+C to exit)")

def detect_sound():
    """ 마이크에서 소리를 감지하고 감지된 시간을 반환 """
    while True:
        # 마이크 1 데이터 읽기
        data1 = np.frombuffer(stream1.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        vol1 = np.max(np.abs(data1))

        # 마이크 2 데이터 읽기
        data2 = np.frombuffer(stream2.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        vol2 = np.max(np.abs(data2))

        # 소음 감지 여부 확인 (감지 여부 출력)
        mic1_detected = 1 if vol1 > THRESHOLD else 0
        mic2_detected = 1 if vol2 > THRESHOLD else 0

        print(f"mic 1: {mic1_detected}, mic 2: {mic2_detected}")

        if mic1_detected or mic2_detected:
            t1 = time.time() if mic1_detected else None
            t2 = time.time() if mic2_detected else None
            return mic1_detected, mic2_detected, t1, t2

def estimate_source(mic1_detected, mic2_detected, t1, t2):
    """ 감지된 시간 차이를 기반으로 소음 위치를 추정 """
    if not mic1_detected and not mic2_detected:
        return None  # 둘 다 감지 안 됨

    detected_mics = []
    detected_times = []

    if mic1_detected:
        detected_mics.append(mic_positions[0])
        detected_times.append(t1)
    
    if mic2_detected:
        detected_mics.append(mic_positions[1])
        detected_times.append(t2)

    detected_mics = np.array(detected_mics)
    detected_times = np.array(detected_times)
    time_differences = detected_times - min(detected_times)

    def loss_function(estimated_source):
        """ 최소 제곱법을 이용한 소리 발생 위치 추정 """
        estimated_distances = np.linalg.norm(detected_mics - estimated_source, axis=1)
        estimated_times = estimated_distances / SOUND_SPEED
        return np.sum((estimated_times - min(estimated_times) - time_differences) ** 2)

    # 초기 추정값 (라즈베리파이 근처에서 발생했다고 가정)
    initial_guess = np.array([400, 200])  # 초기 추정값 (x=400mm, y=200mm)
    result = minimize(loss_function, initial_guess, method='Nelder-Mead')

    return result.x  # 추정된 소리 발생 위치 반환

try:
    while True:
        mic1_detected, mic2_detected, t1, t2 = detect_sound()  # 소리 감지 후 시간 기록

        if mic1_detected or mic2_detected:
            estimated_source = estimate_source(mic1_detected, mic2_detected, t1, t2)  # 위치 추정
            print(f"Estimated noise location (mm): {estimated_source}")
        else:
            print("No noise detected (no microphones 1 and 2 detected)")

except KeyboardInterrupt:
    print("Noise detection shutdown.")

finally:
    stream1.stop_stream()
    stream1.close()
    stream2.stop_stream()
    p.terminate()
