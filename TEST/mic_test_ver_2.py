import subprocess
import time
from datetime import datetime

# MIC set
MIC_LOCATIONS = {
    "mic_set": "mic_2"
}

# set constants
RATE = 48000  # sampling rate
FORMAT = "S16_LE"  # 16-bit Little Endian PCM
CHANNELS = 1  # Single channel recording
RECORD_SECONDS = 3600  # Maximum recording time (1 hour) 7200 2 

# Set file name based on current date and time
current_time = datetime.now().strftime("%d_%m_%y_%H:%M:%S")
LOG_FILENAME = f"sound_detection_{current_time}.log"
WAVE_FILENAMES = {
    location: f"recorded_{location}_{current_time}.wav"
    for location in MIC_LOCATIONS.keys()
}

print("Start recording using arecord... (Ctrl+C to stop)")

def log_message(message):
    """ Save log messages to file """
    with open(LOG_FILENAME, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# Start recording from each microphone
processes = {}
try:
    for location, device in MIC_LOCATIONS.items():
        filename = WAVE_FILENAMES[location]
        command = [
            "arecord",
            "-D", device,      # ALSA device settings
            "-f", FORMAT,      # Format set
            "-r", str(RATE),   # sampling rate set
            "-c", str(CHANNELS),  # channels set
            "-t", "wav",       # Output Format
            "-d", str(RECORD_SECONDS),  # recording time
            filename           # File name to save
        ]
        
        print(f"Recording {location} to {filename}...")
        log_message(f"Recording started: {location} -> {filename}")

        # Run in background
        processes[location] = subprocess.Popen(command)

    # Wait until all processes are terminated
    for process in processes.values():
        process.wait()

except KeyboardInterrupt:
    print("Recording stopped by user.")
    log_message("Recording stopped by user.")

    # Force quit all recording processes
    for process in processes.values():
        process.terminate()

finally:
    print("recordings saved successfully.")
    log_message("recordings saved successfully.")
