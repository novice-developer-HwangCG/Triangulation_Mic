import pyaudio

p = pyaudio.PyAudio()
device_index = 3  # 사용 중인 마이크의 인덱스 설정

info = p.get_device_info_by_index(device_index)
print("Supported sample rates:", info)
p.terminate()
