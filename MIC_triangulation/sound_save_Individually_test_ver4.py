import subprocess
import time
from datetime import datetime

# MIC set
MIC_LOCATIONS = {
    "middle": "mic_2",
    "left": "mic_3",
    "right": "mic_1"
}

# set constants
RATE = 48000  # Sampling rate
FORMAT = "S16_LE"  # 16-bit Little Endian PCM
CHANNELS = 1  # Single channel recording
RECORD_SECONDS = 1200  # Maximum recording time (1 hour = 3600 / file size = approximately 330MB)

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
        current_time = time.time()

        for location in MIC_LOCATIONS.keys():
            sound_level = get_sound_level(location)
            if sound_level and sound_level > threshold_dB[location]:
                if current_time - last_detection_time[location] > 0.1:  # Ignore too frequent detections
                    detection_status[location] = 1
                    last_detection_time[location] = current_time

        # If all three detected within 0.1s, ignore (environmental noise)
        if sum(detection_status.values()) == 3:
            detection_status = {loc: 0 for loc in MIC_LOCATIONS.keys()}

        detection_msg = f"Sound detection: middle = {detection_status['middle']}, left = {detection_status['left']}, right = {detection_status['right']}"
        print(detection_msg)
        log_message(detection_msg)

        time.sleep(1)  # Check every 5 seconds

except KeyboardInterrupt:
    print("Recording stopped by user.")
    log_message("Recording stopped by user.")

    # Force quit all recording processes
    for process in processes.values():
        process.terminate()

finally:
    print("All recordings saved successfully.")
    log_message("All recordings saved successfully.")
