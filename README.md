<---HOW TO SET MIC IN RASPBERRY PI 4 ver 2--->

1. pulseaudio가 설치 되어 있을 시 생략 후 2번부터 확인
(If pulseaudio is installed, skip this step and check from step 2)

설치 되어 있는데 오류가 났을 시 pulseaudio와 ALSA를 우선 초기화 후 설치 제거

초기화
- pulseaudio --kill

- rm -rf ~/.config/pulse
- rm -rf ~/.pulse
- rm -rf ~/.asoundrc

- sudo rm -rf /var/lib/pulse
- sudo rm -f /etc/pulse/client.conf
- sudo rm -f /etc/modprobe.d/alsa-base.conf

설치 제거
- sudo apt purge pulseaudio pulseaudio-utils alsa-utils -y

- sudo reboot

만약 reboot 이후 라즈베리파이 GUI가 오류가 났을 때

로그인 화면에서 Ctrl + Alt + F2

- sudo apt update && sudo apt upgrade -y
- sudo apt install --reinstall raspberrypi-ui-mods lxsession -y

- startx

- sudo reboot

pulseaudio와 ALSA 재설치
- sudo apt install pulseaudio pulseaudio-utils alsa-utils -y

pulseaudio 실행
- pulseaudio --start

USB 연결된 마이크 확인 (pulseaudio에 연결된 마이크)
- pactl list sources | grep Name

아래와 같이 비슷한 메세지 출력 시 정상
Name: alsa_input.usb-0d8c_USB_Audio-00.analog-stereo
Name: alsa_input.usb-1d6b_USB_Microphone-00.analog-stereo


2. 마이크 인식 확인 <---OLD VER NOT USE, skip this step and check from step NEW 1--->
- arecord -l

아래 예시와 같이 비슷한 메세지 출력 시 정상
(예시)
card 1: PRO [Comica_VM10 PRO], device 0: USB Audio [USB Audio]
card 3: PRO_1 [Comica_VM10 PRO], device 0: USB Audio [USB Audio]

ALSA 설정 파일 생성
- nano ~/.asoundrc

내용 추가 이전 arecord -l에서 출력된 메세지에 card [num]값으로 card 값을 변경
pcm.mic1 {
    type hw
    card 2
    device 0
}

pcm.mic2 {
    type hw
    card 4
    device 0
}

pcm.mic3 {
    type hw
    card 5
    device 0
}

pcm.!default {
    type asym
    playback.pcm "default"
    capture.pcm "mic1"
}

설정 반영
- sudo reboot

3. 마이크 인덱스 확인
- mic_check.py 파일 실행

출력되는 메세지 중 아래 Device 메세지만 확인
Device 0: bcm2835 Headphones: - (hw:0,0) (Input channels: 0)
Device 1: Comica_VM10 PRO: USB Audio (hw:1,0) (Input channels: 2) <------ 인식된 마이크 1
Device 2: Comica_VM10 PRO: USB Audio (hw:2,0) (Input channels: 2) <------ 인식된 마이크 2
Device 3: Comica_VM10 PRO: USB Audio (hw:3,0) (Input channels: 2) <------ 인식된 마이크 3
Device 4: vc4-hdmi-0: MAI PCM i2s-hifi-0 (hw:3,0) (Input channels: 0)
Device 5: sysdefault (Input channels: 0)
Device 6: lavrate (Input channels: 0)
Device 7: samplerate (Input channels: 0)
Device 8: speexrate (Input channels: 0)
Device 9: pulse (Input channels: 32)
Device 10: upmix (Input channels: 0)
Device 11: vdownmix (Input channels: 0)
Device 12: dmix (Input channels: 0)
Device 13: default (Input channels: 32)

- sound_save_Inver3.py 파일에 MIC_LOCATIONS 값 반영
예시)
MIC_LOCATIONS = {
    "middle": "plughw:1,0",  # 마이크 A
    "left": "plughw:2,0",    # 마이크 B
    "right": "plughw:3,0"    # 마이크 C
}

- mic_test.py 파일에 MIC[NUM]_INDEX에 마이크 인덱스 반영
MIC1_INDEX = 1  # Comica_VM10 PRO (hw:1,0)
MIC2_INDEX = 2  # Comica_VM10 PRO (hw:2,0)
MIC3_INDEX = 3  # Comica_VM10 PRO (hw:2,0)

4. python3 mic_test.py 실행하여 마이크 소리 감지 확인
감지 시 1 미 감지 시 0 출력

5. 코드 실행 오류 시

연결된 마이크 샘플링 레이트 확인
- arecord -D plughw:1,0 --dump-hw-params
( arecord -D plughw:1,0 -f S16_LE --dump-hw-params )

출력되는 샘플링 레이트 값 예시
SAMPLE_RATE: [8000 16000 44100]

해당 값에 따라 mic_test.py에 RATE 값 수정

6. 수정하여도 오류 일 시 각 샘플링 데이터로 소리 녹음
- arecord -D plughw:2,0 -f S16_LE -r 8000 -c 1 test_8000.wav
( arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 test_16000.wav )
( arecord -D plughw:2,0 -f S16_LE -r 44100 -c 1 test_44100.wav )

녹음 이후 Ctrl+C 키로 종료 시 자동으로 녹음된 파일이 저장
- 저장된 파일 이름 test_8000.wav (test_16000, test_44100)

녹음된 파일을 확인 소리 감지 시 문제 없을 시 mic_test.py 코드 재 실행

7. 위 확인 사항이 모두 끝나면 mic_record 디렉터리 이동 
sound_save_Individually_ver2.py 파일에 MIC[NUM]_INDEX 값을 이전 mic_test.py에 맞춰 수정 후 저장

8. sound_save_Individually_ver2.py 실행하여 소리 녹음



<-----HOW TO SET MIC IN RASPBERRY PI 4 ver 3----->


NEW 1. mic_setup.py 실행 자동 ./asoundrc 생성 및 ALSA 재설정 -> sudo reboot 필요 없음

NEW 2. arecord -L 명령어로 적용 확인
(예시)
pi@raspberrypi:~/Desktop/mic_test/mic_record $ arecord -L
null
    Discard all samples (playback) or generate zero samples (capture)
lavrate
    Rate Converter Plugin Using Libav/FFmpeg Library
samplerate
    Rate Converter Plugin Using Samplerate Library
speexrate
    Rate Converter Plugin Using Speex Resampler
jack
    JACK Audio Connection Kit
oss
    Open Sound System
pulse
    PulseAudio Sound Server
upmix
    Plugin for channel upmix (4,6,8)
vdownmix
    Plugin for channel downmix (stereo) with a simple spacialization
mic_1  <------ 인식된 mic 1
mic_2  <------ 인식된 mic 2
mic_3  <------ 인식된 mic 3
default

NEW 3. 마이크 테스트
- arecord -D mic_2 -f S16_LE -r 48000 -c 1 test_middle.wav
- arecord -D mic_3 -f S16_LE -r 48000 -c 1 test_left.wav
- arecord -D mic_1 -f S16_LE -r 48000 -c 1 test_right.wav

<!> NEW 3-1. 실행 파일로 확인을 원할 시 mic_test/mic_test 디렉터리 내부에서 아래 명령어 실행
- python3 mic_test_ver_2.py
- 'mic_set'의 설정 값을 mic_1, mic_2, mic_3로 변경 하여 테스트

NEW 4. 녹음된 소리 파일 확인이 끝나면 sound_save_Individually_ver3.py 실행하여 소리 녹음

※※※ sound_save_Individually_ver3.py 파일 문제점 필독 ※※※
- 해당 코드 원격이 아닌 라즈베리파이 UI에서 실행 시 라즈베리파이 먹통 현상 발생 (추 후 수정 예정)
- 다만, 원격 접속 및 원격 실행 시 문제는 없음
-> 셋팅이 끝나면 실행 및 종료는 원격 접속으로 해야 함

● 번 외

- 녹음 이후 Ctrl+c 키로 강제 종료 시 출력되는 오류 메세지가 아래 내용이라면 이는 녹음이 실행 중인 상태에서 강제 종료했을 때 발생하는 일반적인 오류로, 무시해도 됨

arecord: pcm_read:2152: read error: Interrupted system call
arecord: pcm_read:2152: read error: Interrupted system call


""" 25.03.17 Updated """

<!> 마이크 녹음 검토
- 하부 또는 특정범위 밖의 인식 제거방안
- 특정 시간 간격 내에 발생하는 신호 필터링 방안 (ex. 3개의 센서에 거의 동시에 신호가 들어오는 상황)

-> sox 사용 해결 검토
= sox (Sound eXchange)는 오디오 파일을 처리하고 변환하는 범용 명령어 기반 오디오 툴

- 각 마이크에서 입력되는 소리의 크기를 측정하기 위해 sox의 stat 옵션을 활용, 각 마이크에서 소리 감지를 위해 sox를 사용하여 일정 시간 간격으로 음량을 측정

A = 결과 코드 sound_save_Individually_test_ver4.py

1. 배경 소음 학습 기능
- 실행 후 10초 동안 배경 노이즈를 측정하고, 그 값에 맞는 감지 임계값 설정

2. RMS(dB) 기준 감지 설정
- sox를 이용한 RMS(dB) 값이 배경 소음보다 5dB 이상 크면 충격음 감지, 소리가 작아도 감지되는 문제를 해결해보려 함

3. 특정 시간 내 동시 감지 필터링
- 0.1초 이내에 3개 마이크가 동시에 감지하면 환경 소음으로 간주하고 무시

4. 소리 감지 시 메세지 출력 및 log 저장
- Sound detection: middle = 1, left = 0, right = 1 형식
- .txt 파일에 log 메세지 저장 추가

""" 25.03.21 Updated """

<!> 삼각측량 검토

A = 결과 코드 sound_save_Individually_ver5.py / sound_save_Individually_ver6.py

1. sound_save_Individually_ver5.py
- 실제 소리 감지 시간 기록
- estimate_impact_location() 함수 Residual 계산 추가
- 신뢰도 계산 추가
- 출력 = 타격음 좌표 (mm 단위), 신뢰도와 Residual 오차 함께 출력

2. sound_save_Individually_ver6.py
- 이중 필터링(직사각형 범위 + Residual 기반)을 적용