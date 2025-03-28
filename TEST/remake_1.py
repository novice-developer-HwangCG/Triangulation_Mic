import subprocess
import time
from datetime import datetime
import numpy as np
from scipy.optimize import minimize

""" 
- dB로만 감지
- 감지만 기록
- 삼각측량 없음
- 실제 타격 위치 계산 없음
- 신뢰도 분석 없음
"""

# MIC set
MIC_LOCATIONS = {
    "middle": "mic_2",
    "left": "mic_3",
    "right": "mic_1"
}

# Microphone positions for triangulation (x, y) in mm
MIC_POSITIONS = {
    "left": np.array([0, 0]),
    "middle": np.array([100, 0]),
    "right": np.array([200, 0])
}

# set constants
RATE = 48000  # Sampling rate
FORMAT = "S16_LE"  # 16-bit Little Endian PCM
CHANNELS = 1  # Single channel recording
RECORD_SECONDS = 1200  # Maximum recording time

# Set file name based on current date and time
current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
LOG_FILENAME = f"sound_detection_{current_time}.txt"
WAVE_FILENAMES = {
    location: f"recorded_{location}_{current_time}.wav"
    for location in MIC_LOCATIONS.keys()
}

print("Start recording using arecord... (Ctrl+C to stop)")

def log_message(message):
    """ Save log messages to file """
    with open(LOG_FILENAME, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")


def get_sound_level(device):
    """ Measure RMS (dB) sound level using sox """
    try:
        command = [
            "sox", "-t", "wav", "-r", str(RATE), "-c", str(CHANNELS),
            "-e", FORMAT, "-d", "-n", "stats"
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in result.stderr.split("\n"):
            if "RMS lev dB" in line:
                return float(line.split()[-1])
    except Exception as e:
        log_message(f"Error checking sound level for {device}: {e}")
    return None

def estimate_impact_location(detected_mics, detected_times):
    detected_positions = np.array([MIC_POSITIONS[mic] for mic in detected_mics])
    detected_times = np.array(detected_times)
    time_differences = detected_times - min(detected_times)

    def loss_function(estimated_source):
        estimated_distances = np.linalg.norm(detected_positions - estimated_source, axis=1)
        estimated_times = estimated_distances / 343000.0  # Speed of sound in mm/s
        return np.sum((estimated_times - min(estimated_times) - time_differences) ** 2)

    initial_guess = np.mean(detected_positions, axis=0)
    result = minimize(loss_function, initial_guess, method='Nelder-Mead')
    return result.x

# Start recording from each microphone
processes = {}
try:
    for location, device in MIC_LOCATIONS.items():
        filename = WAVE_FILENAMES[location]
        command = [
            "arecord",
            "-D", device,      # ALSA device settings
            "-f", FORMAT,      # Format set
            "-r", str(RATE),   # Sampling rate set
            "-c", str(CHANNELS),  # Channels set
            "-t", "wav",       # Output Format
            "-d", str(RECORD_SECONDS),  # Recording time
            filename           # File name to save
        ]

        print(f"Recording {location} to {filename}...")
        log_message(f"Recording started: {location} -> {filename}")

        # Run in background
        processes[location] = subprocess.Popen(command)

    # Measure initial background noise for 10 seconds
    print("Measuring background noise level...")
    noise_levels = {loc: [] for loc in MIC_LOCATIONS.keys()}
    start_time = time.time()

    while time.time() - start_time < 10:
        for location in MIC_LOCATIONS.keys():
            level = get_sound_level(location)
            if level is not None:
                noise_levels[location].append(level)
        time.sleep(1)

    # Compute average noise level per microphone
    avg_noise_levels = {loc: sum(levels) / len(levels) for loc, levels in noise_levels.items() if levels}
    print(f"Background noise levels: {avg_noise_levels}")
    log_message(f"Background noise levels: {avg_noise_levels}")

    threshold_dB = {loc: avg_noise_levels[loc] + 5 for loc in avg_noise_levels}  # Set threshold 5dB above noise level

    # Start continuous sound detection
    print("Monitoring sound levels...")
    last_detection_time = {loc: 0 for loc in MIC_LOCATIONS.keys()}

    while True:
        detection_status = {loc: 0 for loc in MIC_LOCATIONS.keys()}
        detection_times = {}
        current_time_sec = time.time()

        for location in MIC_LOCATIONS.keys():
            sound_level = get_sound_level(location)
            if sound_level and sound_level > threshold_dB[location]:
                if current_time_sec - last_detection_time[location] > 0.1:  # Ignore too frequent detections
                    detection_status[location] = 1
                    detection_times[location] = current_time_sec
                    last_detection_time[location] = current_time_sec

        # If all three detected within 0.1s, treat as valid impact and run triangulation
        if len(detection_times) >= 2:
            estimated_location = estimate_impact_location(
                detected_mics=list(detection_times.keys()),
                detected_times=list(detection_times.values())
            )
            impact_msg = f"Estimated impact location (mm): X={estimated_location[0]:.2f}, Y={estimated_location[1]:.2f}"
            print(impact_msg)
            log_message(impact_msg)
        else:
            no_impact_msg = "No valid impact detected."
            print(no_impact_msg)
            log_message(no_impact_msg)

        time.sleep(1)  # Check every 1 second

except KeyboardInterrupt:
    print("Recording stopped by user.")
    log_message("Recording stopped by user.")

    # Force quit all recording processes
    for process in processes.values():
        process.terminate()

finally:
    print("All recordings saved successfully.")
    log_message("All recordings saved successfully.")
