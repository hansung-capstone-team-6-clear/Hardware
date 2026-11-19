import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "deskpet"

# 기존 LCD 표정 테스트 코드
LCD_SCRIPT = Path(__file__).resolve().parent / "lcd_faces_cycle.py"

# 기존 음성 파일
AUDIO_FILE = BASE / "test_audio" / "pipeline_voice.wav"

# MAX98357A 오디오 장치
AUDIO_DEVICE = "plughw:2,0"

lcd_process = None

try:
    if not LCD_SCRIPT.exists():
        raise FileNotFoundError(f"LCD 코드 없음: {LCD_SCRIPT}")

    if not AUDIO_FILE.exists():
        raise FileNotFoundError(f"음성 파일 없음: {AUDIO_FILE}")

    print("LCD + 스피커 동시 테스트 시작")
    print("종료: Ctrl+C")

    # LCD 표정 출력 시작
    lcd_process = subprocess.Popen(
        [sys.executable, str(LCD_SCRIPT)],
        cwd=str(BASE)
    )

    time.sleep(1)

    # 말소리 무한 반복
    while lcd_process.poll() is None:
        result = subprocess.run([
            "aplay",
            "-q",
            "-D", AUDIO_DEVICE,
            str(AUDIO_FILE)
        ])

        if result.returncode != 0:
            print("스피커 재생 오류")
            break

        time.sleep(0.5)

    if lcd_process.poll() is not None:
        print("LCD 프로그램이 종료되었습니다.")

except KeyboardInterrupt:
    print("\n테스트 종료")

except Exception as e:
    print(f"오류: {e}")

finally:
    if lcd_process is not None and lcd_process.poll() is None:
        lcd_process.terminate()
        try:
            lcd_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            lcd_process.kill()
            lcd_process.wait()

print("프로그램 종료")
