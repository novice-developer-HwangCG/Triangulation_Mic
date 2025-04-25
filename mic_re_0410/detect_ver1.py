import time
import numpy as np
import sounddevice as sd
from scipy.optimize import minimize
from datetime import datetime

# 마이크 설정 (sounddevice 인덱스 기준)
MIC_LOCATIONS = {
    "left": 3,
    "middle": 2,
    "right": 1
}

MIC_POSITIONS = {
    "left": np.array([100, 0]),
    "middle": np.array([200, 0]),
    "right": np.array([300, 0])
}

RATE = 48000
THRESHOLD_DB = -40
RESIDUAL_THRESHOLD = 0.005
SOUND_SPEED = 343000  # mm/s

global_record_start = time.time()

current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
LOG_FILENAME = f"sound_detection_{current_time}.txt"

def log_message(message):
    with open(LOG_FILENAME, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def get_sound_level(device_index):
    try:
        device_info = sd.query_devices(device_index)
        if device_info['max_input_channels'] < 1:
            raise ValueError("Unable to determine number of input channels")

        channels = min(2, device_info['max_input_channels'])

        duration = 0.05  # 50ms
        start_time = time.time()
        recording = sd.rec(int(RATE * duration), samplerate=RATE, channels=channels,
                           dtype='float32', device=device_index)
        sd.wait()
        end_time = time.time()
        detect_time = (start_time + end_time) / 2

        rms = np.sqrt(np.mean(recording**2))
        db = 20 * np.log10(rms) if rms > 0 else -100
        return db, detect_time

    except Exception as e:
        print(f"[ERROR] get_sound_level failed: {e}")
        return -100, time.time()  # 항상 튜플 반환

# def get_sound_level(device_index):
#     try:
#         device_info = sd.query_devices(device_index, 'input')
#         supported_channels = device_info['max_input_channels']
#         channels = 1 if supported_channels >= 1 else supported_channels

#         start_time = time.time()
#         recording = sd.rec(...)
#         sd.wait()
#         end_time = time.time()
#         detect_time = (start_time + end_time) / 2  # 녹음 중간 시점 추정

#         duration = 0.02  # 초
#         recording = sd.rec(int(RATE * duration), samplerate=RATE, channels=channels, dtype='float32', device=device_index)
#         sd.wait()
#         rms = np.sqrt(np.mean(recording**2))
#         db = 20 * np.log10(rms) if rms > 0 else -100
#         return db, detect_time
#     except Exception as e:
#         print(f"[ERROR] get_sound_level failed: {e}")
#         return -100, time.time()

def estimate_impact_location(time_diffs, mic_positions):
    def loss(source_pos):
        distances = np.linalg.norm(mic_positions - source_pos, axis=1)
        arrival_times = distances / SOUND_SPEED
        relative_times = arrival_times - arrival_times.min()
        return np.sum((relative_times - time_diffs) ** 2)

    initial_guess = np.mean(mic_positions, axis=0)
    result = minimize(loss, initial_guess, method='Nelder-Mead')
    return result.x, result.fun

print("Start monitoring... (Ctrl+C to stop)")
log_message("Monitoring started")

try:
    while True:
        detected, detect_times = {}, {}
        sound_levels = {}

        for mic, device_index in MIC_LOCATIONS.items():
            sound_db, _ = get_sound_level(device_index)
            sound_levels[mic] = sound_db
            print(f"[DEBUG] {mic} mic sound level: {sound_db:.2f} dB")

            if sound_db > THRESHOLD_DB:
                detected[mic] = True
                detect_times[mic] = global_record_start
            else:
                detected[mic] = False

        print(f"[INFO] Detected mics: {[m for m in detected if detected[m]]}")
        print(f"[INFO] Sound levels: {sound_levels}")

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

            estimated_pos, residual = estimate_impact_location(time_diffs, positions)
            confidence = max(0, 1 - (residual / RESIDUAL_THRESHOLD)) * 100

            print(f"[DEBUG] Detect times: {detect_times}")
            if confidence >= 10:
                impact_msg = f"타격음 좌표(추정) = (x={estimated_pos[0]:.1f} mm, y={estimated_pos[1]:.1f} mm)"
                confidence_msg = f"신뢰도 = {confidence:.1f}%, 오차(Residual) = {residual:.6f}"
                print(impact_msg)
                print(confidence_msg)
                log_message(impact_msg)
                log_message(confidence_msg)
            else:
                print(f"[INFO] 신뢰도 낮음: {confidence:.1f}%, 좌표 무시")

            time.sleep(0.5)
        else:
            print("No impact detected.")
            time.sleep(1)

except KeyboardInterrupt:
    print("Monitoring stopped by user.")
    log_message("Monitoring stopped by user.")

finally:
    print("Monitoring ended.")
    log_message("Monitoring ended.")
