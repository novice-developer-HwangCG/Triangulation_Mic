import pyaudio
import numpy as np

RATE = 48000  # 샘플링 레이트
CHUNK = 1024  # 버퍼 크기
THRESHOLD = 1000  # 소리 감지 임계값 (환경에 따라 조정)
MIC1_INDEX = 1  # Comica_VM10 PRO (hw:1,0)
MIC2_INDEX = 2  # Comica_VM10 PRO (hw:2,0)
MIC3_INDEX = 3

# PyAudio 객체 생성
p = pyaudio.PyAudio()

# 마이크 2개 스트림 열기
stream1 = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                 input_device_index=MIC1_INDEX, frames_per_buffer=CHUNK)

stream2 = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                 input_device_index=MIC2_INDEX, frames_per_buffer=CHUNK)

stream3 = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                 input_device_index=MIC3_INDEX, frames_per_buffer=CHUNK)

print("mic on")

try:
    while True:
        # mic 1 data
        data1 = np.frombuffer(stream1.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        vol1 = np.max(np.abs(data1))  # 음량 계산

        # mic 2 data
        data2 = np.frombuffer(stream2.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        vol2 = np.max(np.abs(data2))  # 음량 계산

        # mic 3 data
        data3 = np.frombuffer(stream3.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        vol3 = np.max(np.abs(data3))  # 음량 계산

        # 감지된 소리에 따라 출력
        mic1_detected = 1 if vol1 > THRESHOLD else 0
        mic2_detected = 1 if vol2 > THRESHOLD else 0
        mic3_detected = 1 if vol3 > THRESHOLD else 0

        print(f"mic 1 = {mic1_detected}, mic 2 = {mic2_detected}, mic 3 = {mic3_detected}")

except KeyboardInterrupt:
    print("mic off")

finally:
    stream1.stop_stream()
    stream1.close()
    stream2.stop_stream()
    stream2.close()
    stream3.stop_stream()
    stream3.close()
    p.terminate()
