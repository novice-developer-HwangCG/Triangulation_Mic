import time
import numpy as np
import pyaudio
import wave
from scipy.optimize import minimize
from scipy.signal import find_peaks
from datetime import datetime
import os

os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["ALSA_CARD"] = "default"

# 마이크별 pyaudio 장치 인덱스
MIC_DEVICES = {
    "left": 3,
    "middle": 2,
    "right": 1
}

MIC_POSITIONS = {
    "left": np.array([100, 0]),
    "middle": np.array([200, 100]),
    "right": np.array([300, 0])
}

RATE = 48000
DURATION = 0.1  # 100ms
CHUNK = int(RATE * DURATION)
THRESHOLD_DB = -40
RESIDUAL_THRESHOLD = 0.005
SOUND_SPEED = 343000  # mm/s

current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
LOG_FILENAME = f"sound_detection_{current_time}.txt"

def log_message(msg):
    with open(LOG_FILENAME, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

def db_from_signal(signal):
    rms = np.sqrt(np.mean(signal ** 2))
    db = 20 * np.log10(rms) if rms > 0 else -100
    return db

def record_from_device(index):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    input_device_index=index,
                    frames_per_buffer=CHUNK)
    data = stream.read(CHUNK)
    stream.stop_stream()
    stream.close()
    p.terminate()
    signal = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
    return signal

def estimate_impact_location(time_diffs, mic_positions):
    def loss(pos):
        dists = np.linalg.norm(mic_positions - pos, axis=1)
        arrivals = dists / SOUND_SPEED
        relative = arrivals - arrivals.min()
        return np.sum((relative - time_diffs) ** 2)

    guess = np.mean(mic_positions, axis=0)
    result = minimize(loss, guess, method='Nelder-Mead')
    x, y = result.x
    x = max(0, min(x, 400))
    y = max(0, min(y, 1000))
    clamped_pos = np.array([x, y])

    return clamped_pos, result.fun

print("Start monitoring... (Ctrl+C to stop)")
log_message("Monitoring started")

try:
    while True:
        signals = {}
        db_levels = {}
        detect_peaks = {}

        # 동시에 각 마이크에서 녹음
        for mic, index in MIC_DEVICES.items():
            signal = record_from_device(index)
            signals[mic] = signal
            db_levels[mic] = db_from_signal(signal)
            print(f"[DEBUG] {mic} mic level: {db_levels[mic]:.2f} dB")

        print(f"[INFO] dB levels: {db_levels}")

        # 2개 이상 마이크가 일정 dB 이상일 때만 진행
        active_mics = [mic for mic, db in db_levels.items() if db > THRESHOLD_DB]
        if len(active_mics) >= 2:
            detect_times = {}
            for mic in active_mics:
                peaks, _ = find_peaks(signals[mic], height=0.1)
                detect_time = peaks[0] / RATE if len(peaks) > 0 else 0
                detect_times[mic] = detect_time

            print(f"[DEBUG] Peak times: {detect_times}")

            if len(detect_times) >= 2:
                first = min(detect_times.values())
                time_diffs = []
                positions = []
                for mic in detect_times:
                    time_diffs.append(detect_times[mic] - first)
                    positions.append(MIC_POSITIONS[mic])
                time_diffs = np.array(time_diffs)
                positions = np.array(positions)

                pos, residual = estimate_impact_location(time_diffs, positions)
                confidence = max(0, 1 - (residual / RESIDUAL_THRESHOLD)) * 100

                if confidence >= 10:
                    impact = f"타격음 좌표(추정) = (x={pos[0]:.1f} mm, y={pos[1]:.1f} mm)"
                    conf = f"신뢰도 = {confidence:.1f}%, 오차(Residual) = {residual:.6f}"
                    print(impact)
                    print(conf)
                    log_message(impact)
                    log_message(conf)
                else:
                    print(f"[INFO] 신뢰도 낮음: {confidence:.1f}%, 좌표 무시")
        else:
            print("No impact detected.")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Monitoring stopped by user.")
    log_message("Monitoring stopped by user.")

finally:
    print("Monitoring ended.")
    log_message("Monitoring ended.")
