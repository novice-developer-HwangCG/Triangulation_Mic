import os
import subprocess
import re
import time

# 마이크 자동 감지 함수
def get_mic_indices():
    """ Automatically search microphone index after running arecord -l """
    result = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
    lines = result.stdout.split("\n")

    mic_indices = []
    for line in lines:
        # "Comica_VM10 PRO", "Comica_VM10 PRO_1", "Comica_VM10 PRO_2" 모두 인식
        match = re.search(r"card (\d+): PRO(?:_\d+)? \[Comica_VM10 PRO", line)
        if match:
            mic_indices.append(int(match.group(1)))  # card 번호 저장

    if len(mic_indices) < 3:
        print("3개의 마이크를 찾지 못했습니다. arecord -l을 실행하여 확인하세요.")
        return None
    
    return mic_indices

# ALSA 설정 파일 생성 (plughw 별칭 추가)
def create_asoundrc(mic_indices):
    """ Create a ~/.asoundrc file to apply ALSA microphone settings and assign a plughw alias """
    asoundrc_content = f"""
pcm.mic_1 {{
    type plug
    slave {{
        pcm "hw:{mic_indices[0]},0"
    }}
}}

pcm.mic_2 {{
    type plug
    slave {{
        pcm "hw:{mic_indices[1]},0"
    }}
}}

pcm.mic_3 {{
    type plug
    slave {{
        pcm "hw:{mic_indices[2]},0"
    }}
}}

pcm.!default {{
    type asym
    playback.pcm "default"
    capture.pcm "mic_middle"
}}
"""
    asoundrc_path = os.path.expanduser("~/.asoundrc")
    
    with open(asoundrc_path, "w") as f:
        f.write(asoundrc_content)
    
    print("ALSA 설정 파일이 생성되었습니다. 설정을 반영합니다...")

    # ALSA settings are reflected immediately (applied without reboot)
    subprocess.run(["sudo", "alsactl", "nrestore"])
    subprocess.run(["sudo", "systemctl", "restart", "alsa-restore"])
    subprocess.run(["sudo", "systemctl", "restart", "alsa-state"])

    print("ALSA 설정이 적용되었습니다. 'arecord -L'을 실행하여 확인하세요.")

# 마이크 자동 설정 실행
mic_indices = get_mic_indices()
if mic_indices:
    create_asoundrc(mic_indices)
