import subprocess
import time
import numpy as np
from scipy.optimize import minimize
from datetime import datetime

""" 
- 이중 필터링(직사각형 범위 + Residual 기반)을 적용
"""

# ALSA 장치 이름
MIC_LOCATIONS = {
    "left": "mic_3",
    "middle": "mic_2",
    "right": "mic_1"
}

# 마이크 좌표 (mm)
MIC_POSITIONS = {
    "left": np.array([100, 0]),
    "middle": np.array([200, 0]),
    "right": np.array([300, 0])
}

# 녹음용 wave 파일
current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
WAVE_FILENAMES = {
    loc: f"recorded_{loc}_{current_time}.wav" for loc in MIC_LOCATIONS.keys()
}


# 상수
RATE = 48000
FORMAT = "S16_LE"
CHANNELS = 1
RECORD_SECONDS = 1200  # Maximum recording time (1 hour = 3600 / file size = approximately 330mb, 2 hour = 7200) 
SOUND_SPEED = 343000  # mm/s
THRESHOLD_DB = -20   # dB 기준 감지 임계값
RESIDUAL_THRESHOLD = 0.00005  # 오차 기준 (해당 값을 낮추면 신뢰도가 더 높은 충격만 인정함 예시 0.00003)
RECT_X_LIMIT = (0, 400)  # mm
RECT_Y_LIMIT = (0, 1000)  # mm

"""
필터링 조절 현재
신뢰도: 0.00005
x 영역: 0 ≤ x ≤ 400 mm
y 영역: 0 ≤ y ≤ 1000 mm

해당 값을 아래 예시 처럼 변경 시 신뢰도가 더 높은 충격만 인정하고, 좁은 구역에서만 인정
신뢰도: 0.00003
x 영역: 50 ≤ x ≤ 350 mm
y 영역: 0 ≤ y ≤ 800 mm
"""

LOG_FILENAME = f"sound_detection_{current_time}.txt"

def log_message(message):
    with open(LOG_FILENAME, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def get_sound_level(device):
    try:
        command = ["sox", "-t", "alsa", device, "-n", "stat"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1)
        for line in result.stderr.split("\n"):
            if "RMS     amplitude" in line:
                amplitude = float(line.split()[-1])
                db = 20 * np.log10(amplitude) if amplitude > 0 else -100
                return db
    except Exception:
        pass
    return -100

def estimate_impact_location(time_diffs, mic_positions):
    """ 삼각측량 및 오차 분석 """
    def loss(source_pos):
        distances = np.linalg.norm(mic_positions - source_pos, axis=1)
        arrival_times = distances / SOUND_SPEED
        relative_times = arrival_times - arrival_times.min()
        return np.sum((relative_times - time_diffs) ** 2)

    initial_guess = np.mean(mic_positions, axis=0)
    result = minimize(loss, initial_guess, method='Nelder-Mead')
    return result.x, result.fun

print("Start monitoring with dual filtering... (Ctrl+C to stop)")
log_message("Monitoring with dual filtering started")

processes = {}

try:
    for location, device in MIC_LOCATIONS.items():
        filename = WAVE_FILENAMES[location]
        command = [
            "arecord",
            "-D", device,
            "-f", FORMAT,
            "-r", str(RATE),
            "-c", str(CHANNELS),
            "-t", "wav",
            "-d", str(RECORD_SECONDS),
            filename
        ]
        print(f"Recording {location} to {filename}...")
        log_message(f"Recording started: {location} -> {filename}")
        processes[location] = subprocess.Popen(command)

    while True:
        detected = {}
        detect_times = {}

        # 각 마이크 소리 감지
        for mic, device in MIC_LOCATIONS.items():
            sound_db = get_sound_level(device)
            if sound_db > THRESHOLD_DB:
                detected[mic] = True
                detect_times[mic] = time.time()
            else:
                detected[mic] = False

        if sum(detected.values()) >= 2:
            # 삼각측량 수행
            first_time = min([t for m, t in detect_times.items() if detected.get(m)])
            time_diffs = []
            mic_order = []
            positions = []

            for mic in MIC_LOCATIONS:
                if mic in detect_times:
                    t_diff = detect_times[mic] - first_time
                    time_diffs.append(t_diff)
                    mic_order.append(mic)
                    positions.append(MIC_POSITIONS[mic])

            time_diffs = np.array(time_diffs)
            positions = np.array(positions)

            # 삼각측량 계산
            estimated_pos, residual = estimate_impact_location(time_diffs, positions)
            confidence = max(0, 1 - (residual / RESIDUAL_THRESHOLD)) * 100

            # 필터링 조건
            within_rect = (RECT_X_LIMIT[0] <= estimated_pos[0] <= RECT_X_LIMIT[1]) and \
                          (RECT_Y_LIMIT[0] <= estimated_pos[1] <= RECT_Y_LIMIT[1])
            residual_ok = residual <= RESIDUAL_THRESHOLD

            if within_rect and residual_ok:
                impact_msg = f"타격음 좌표(추정) = (x={estimated_pos[0]:.1f} mm, y={estimated_pos[1]:.1f} mm)"
                confidence_msg = f"신뢰도 = {confidence:.1f}%, 오차(Residual) = {residual:.6f}"
                print(impact_msg)
                print(confidence_msg)
                log_message(impact_msg)
                log_message(confidence_msg)
            else:
                print("Invalid hit (out of range or large error)")
                log_message("무효 타격 (범위 초과 또는 오차 큼)")

            time.sleep(0.5)

        else:
            print("No impact detected.")
            time.sleep(1)

except KeyboardInterrupt:
    print("Monitoring stopped by user.")
    log_message("Monitoring stopped by user.")
