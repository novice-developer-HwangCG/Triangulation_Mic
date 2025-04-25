# import sounddevice as sd
# print(sd.query_devices())

import sounddevice as sd

# 마이크 인덱스 확인

print("\n=== Available Devices ===")
for i, dev in enumerate(sd.query_devices()):
    print(f"{i}: {dev['name']} ({dev['max_input_channels']} in)")