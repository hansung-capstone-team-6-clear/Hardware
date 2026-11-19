import subprocess
import time
import signal
import sys

# 기존에 테스트했던 음성 파일
from pathlib import Path

# 기존에 테스트했던 음성 파일 (개인 음성이므로 레포에 포함하지 않음)
AUDIO_FILE = str(Path.home() / "deskpet" / "test_audio" / "pipeline_voice.wav")

# MAX98357A 앰프 (기존 card 2)
AUDIO_DEVICE = "plughw:2,0"

running = True

def stop_handler(sig, frame):
    global running
    running = False
    print("\n스피커 테스트 종료")

signal.signal(signal.SIGINT, stop_handler)

print("MAX98357A 스피커 무한 반복 테스트")
print("종료하려면 Ctrl+C\n")

while running:
    try:
        result = subprocess.run(
            ["aplay", "-q", "-D", AUDIO_DEVICE, AUDIO_FILE]
        )

        if result.returncode != 0:
            print("오디오 재생 실패")
            break

        time.sleep(0.3)

    except KeyboardInterrupt:
        break

print("프로그램 종료")
