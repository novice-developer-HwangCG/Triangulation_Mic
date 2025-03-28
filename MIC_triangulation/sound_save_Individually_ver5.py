import subprocess
import time
import numpy as np
from scipy.optimize import minimize
from datetime import datetime

""" 
- 실제 소리 감지 시간 기록
- estimate_impact_location() 함수 Residual 계산 추가
- 신뢰도 계산 추가
- 출력 = 타격음 좌표 (mm 단위), 신뢰도와 Residual 오차 함께 출력
"""

# ALSA mic alias
MIC_LOCATIONS = {
    "left": "mic_3",
    "middle": "mic_2",
    "right": "mic_1"
}

MIC_POSITIONS = {
    "left": np.array([100, 0]),
    "middle": np.array([200, 0]),
    "right": np.array([300, 0])
}

RATE = 48000
FORMAT = "S16_LE"
CHANNELS = 1
SOUND_SPEED = 343000  # mm/s
THRESHOLD_DB = -30
RESIDUAL_THRESHOLD = 0.00005
RECORD_SECONDS = 1200  # 20 min

current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
LOG_FILENAME = f"sound_detection_{current_time}.txt"
WAVE_FILENAMES = {loc: f"recorded_{loc}_{current_time}.wav" for loc in MIC_LOCATIONS.keys()}

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
    def loss(source_pos):
        distances = np.linalg.norm(mic_positions - source_pos, axis=1)
        arrival_times = distances / SOUND_SPEED
        relative_times = arrival_times - arrival_times.min()
        return np.sum((relative_times - time_diffs) ** 2)

    initial_guess = np.mean(mic_positions, axis=0)
    result = minimize(loss, initial_guess, method='Nelder-Mead')
    return result.x, result.fun

print("Start recording and monitoring... (Ctrl+C to stop)")
log_message("Recording and monitoring started")

# 🎙 Start recording all microphones
record_processes = {}
try:
    for loc, device in MIC_LOCATIONS.items():
        filename = WAVE_FILENAMES[loc]
        command = [
            "arecord", "-D", device, "-f", FORMAT, "-r", str(RATE),
            "-c", str(CHANNELS), "-t", "wav", "-d", str(RECORD_SECONDS), filename
        ]
        print(f"Recording {loc} to {filename}...")
        log_message(f"Recording started: {loc} -> {filename}")
        record_processes[loc] = subprocess.Popen(command)

    # 🔎 Start detection loop
    while True:
        detected, detect_times = {}, {}
        for mic, device in MIC_LOCATIONS.items():
            sound_db = get_sound_level(device)
            if sound_db > THRESHOLD_DB:
                detected[mic] = True
                detect_times[mic] = time.time()
            else:
                detected[mic] = False

        if sum(detected.values()) >= 2:
            first_time = min([t for m, t in detect_times.items() if detected.get(m)])
            time_diffs, positions = [], []

            for mic in MIC_LOCATIONS:
                if mic in detect_times:
                    t_diff = detect_times[mic] - first_time
                    time_diffs.append(t_diff)
                    positions.append(MIC_POSITIONS[mic])

            time_diffs = np.array(time_diffs)
            positions = np.array(positions)

            # Triangulation & residual
            estimated_pos, residual = estimate_impact_location(time_diffs, positions)
            confidence = max(0, 1 - (residual / RESIDUAL_THRESHOLD)) * 100

            # Print results
            impact_msg = f"타격음 좌표(추정) = (x={estimated_pos[0]:.1f} mm, y={estimated_pos[1]:.1f} mm)"
            confidence_msg = f"신뢰도 = {confidence:.1f}%, 오차(Residual) = {residual:.6f}"
            print(impact_msg)
            print(confidence_msg)
            log_message(impact_msg)
            log_message(confidence_msg)

            time.sleep(0.5)
        else:
            print("No impact detected.")
            time.sleep(1)

except KeyboardInterrupt:
    print("Monitoring stopped by user.")
    log_message("Monitoring stopped by user.")
    for process in record_processes.values():
        process.terminate()

finally:
    print("All recordings saved successfully.")
    log_message("All recordings saved successfully.")
