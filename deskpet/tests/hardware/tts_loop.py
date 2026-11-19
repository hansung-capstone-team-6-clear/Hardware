import subprocess
import time

from pathlib import Path

# 개인 음성 파일이므로 레포에 포함하지 않음
AUDIO_FILE = str(Path.home() / "deskpet" / "test_audio" / "desk-pet-voice-test.wav")
AUDIO_DEVICE = "plughw:2,0"

print("🔊 TTS 무한 반복 재생 시작")
print("종료하려면 Ctrl + C를 누르세요.\n")

try:
    while True:
        subprocess.run(
            ["aplay", "-D", AUDIO_DEVICE, AUDIO_FILE],
            check=True
        )
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 TTS 반복 재생 종료")
