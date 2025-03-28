import subprocess
import time
from datetime import datetime
import numpy as np

""" 
- 삼각측량 함수 추가
- 좌표 출력 추가
- 실제 도달 시간 측정 로직 없음 (time_diffs는 하드코딩)
- 신뢰도 / 오차 계산 없음
"""

# 마이크 ALSA device 설정
MIC_LOCATIONS = {
    "middle": "mic_2",
    "left": "mic_3",
    "right": "mic_1"
}

# 삼각측량용 마이크 좌표 (단위 cm)
MIC_POSITIONS = {
    "left": np.array([10, 10]),   # 좌측 마이크 (x=10, y=10)
    "middle": np.array([20, 10]), # 중앙 마이크 (x=20, y=10)
    "right": np.array([30, 10])   # 우측 마이크 (x=30, y=10)
}

SOUND_SPEED = 34300  # 공기 중 음속 (cm/s)
RATE = 48000  # 샘플링 레이트
FORMAT = "S16_LE"
CHANNELS = 1
RECORD_SECONDS = 1200  # 녹음 시간 (초)

current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
LOG_FILENAME = f"sound_detection_{current_time}.txt"

print("Start recording using arecord... (Ctrl+C to stop)")

def log_message(message):
    with open(LOG_FILENAME, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def estimate_impact_location(time_diffs):
    """ 삼각측량으로 타격 위치 추정 """
    def loss_func(impact_point):
        estimated_times = np.linalg.norm(np.array(list(MIC_POSITIONS.values())) - impact_point, axis=1) / SOUND_SPEED
        estimated_diffs = estimated_times - estimated_times[1]  # middle 기준으로 시간 차 계산
        return np.sum((estimated_diffs - time_diffs) ** 2)

    from scipy.optimize import minimize
    initial_guess = np.array([20, 50])  # 중앙 쯤에서 시작
    result = minimize(loss_func, initial_guess, method='Nelder-Mead')
    return result.x

# arecord로 녹음 시작
processes = {}
try:
    for location, device in MIC_LOCATIONS.items():
        command = [
            "arecord", "-D", device, "-f", FORMAT,
            "-r", str(RATE), "-c", str(CHANNELS),
            "-t", "wav", "-d", str(RECORD_SECONDS), 
            f"recorded_{location}_{current_time}.wav"
        ]
        print(f"Recording {location}...")
        log_message(f"Recording started: {location}")
        processes[location] = subprocess.Popen(command)

    # 소리 감지 및 삼각측량 모드
    print("Monitoring sound levels and calculating impact location...")
    while True:
        # 더미 값: 각 마이크 도달 시간 차 (실제는 분석해야 함)
        # 예시로 middle 도달 후 left/right 시간차 설정
        time_diffs = np.array([0.001, 0.0, -0.0008])  # 예시용 (left, middle 기준 0, right)

        # 삼각측량 계산
        impact_location = estimate_impact_location(time_diffs)
        impact_msg = f"타격음 좌표(추정) = (x={impact_location[0]:.1f}cm, y={impact_location[1]:.1f}cm)"

        print(impact_msg)
        log_message(impact_msg)

        time.sleep(1)  # 1초 간격 측정

except KeyboardInterrupt:
    print("Recording stopped by user.")
    log_message("Recording stopped by user.")
    for process in processes.values():
        process.terminate()

finally:
    print("All recordings saved successfully.")
    log_message("All recordings saved successfully.")
