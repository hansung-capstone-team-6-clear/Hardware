import time
import math
import wave
import struct
import subprocess
from pathlib import Path

import board
import digitalio
import gpiod

from gpiod.line import Direction, Bias, Value
from PIL import Image, ImageOps
from adafruit_rgb_display import st7789


# ==========================================
# 기본 설정
# ==========================================

BASE_DIR = Path.home() / "deskpet"
FACE_DIR = Path(__file__).resolve().parents[2] / "assets" / "faces"

AUDIO_DEVICE = "plughw:2,0"
BEEP_FILE = BASE_DIR / "test_audio" / "button_beep.wav"

BUTTON_GPIO = 17

FACES = [
    "idle.png",
    "listening.png",
    "thinking.png",
    "speaking.png",
    "alert.png",
    "error.png",
]

# ==========================================
# 1. LCD 초기화
# ==========================================

spi = board.SPI()

cs = digitalio.DigitalInOut(board.D5)
dc = digitalio.DigitalInOut(board.D24)
rst = digitalio.DigitalInOut(board.D25)

display = st7789.ST7789(
    spi,
    cs=cs,
    dc=dc,
    rst=rst,
    width=240,
    height=280,
    x_offset=0,
    y_offset=20,
    rotation=90,
    baudrate=16000000,
)

# LCD 백라이트
backlight = digitalio.DigitalInOut(board.D23)
backlight.direction = digitalio.Direction.OUTPUT
backlight.value = True


# ==========================================
# 2. 표정 이미지 불러오기
# ==========================================

images = []
names = []

for filename in FACES:
    path = FACE_DIR / filename

    if not path.exists():
        print(f"이미지 없음, 건너뜀: {path}")
        continue

    with Image.open(path) as img:
        image = ImageOps.fit(
            img.convert("RGB"),
            (display.height, display.width),
        )

    images.append(image)
    names.append(filename)

if not images:
    raise RuntimeError("표정 이미지가 없습니다. ~/deskpet/faces 확인!")


def show_face(index):
    display.image(images[index])
    print(f"LCD 표정: {names[index]}")


# ==========================================
# 3. 짧은 부저음 WAV 생성
# ==========================================

def make_beep():
    BEEP_FILE.parent.mkdir(parents=True, exist_ok=True)

    sample_rate = 48000
    frequency = 880
    duration = 0.15
    volume = 0.18

    total = int(sample_rate * duration)
    audio = bytearray()

    for i in range(total):
        t = i / sample_rate

        # 시작과 끝에서 소리가 자연스럽게 작아지도록 처리
        fade_in = min(1.0, i / (sample_rate * 0.01))
        fade_out = min(1.0, (total - 1 - i) / (sample_rate * 0.02))
        envelope = max(0.0, min(fade_in, fade_out))

        value = int(
            32767
            * volume
            * envelope
            * math.sin(2 * math.pi * frequency * t)
        )

        # 스테레오: 왼쪽과 오른쪽에 동일한 신호
        audio.extend(struct.pack("<hh", value, value))

    with wave.open(str(BEEP_FILE), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio)


def play_beep():
    subprocess.run(
        [
            "aplay",
            "-q",
            "-D", AUDIO_DEVICE,
            str(BEEP_FILE),
        ],
        check=False,
    )


# ==========================================
# 4. 버튼 입력 처리
# ==========================================

def main():
    make_beep()

    face_index = 0
    show_face(face_index)

    print("\n================================")
    print("데스크펫 버튼 + LCD + 스피커 테스트")
    print("버튼 GPIO17 / 물리 핀 11번")
    print("버튼을 누르면 표정 변경 + 삐 소리")
    print("종료: Ctrl+C")
    print("================================\n")

    # Raspberry Pi 4B GPIO17 입력 + 내부 풀업
    settings = gpiod.LineSettings(
        direction=Direction.INPUT,
        bias=Bias.PULL_UP,
    )

    with gpiod.request_lines(
        "/dev/gpiochip0",
        consumer="deskpet-button",
        config={BUTTON_GPIO: settings},
    ) as button:

        def is_pressed():
            # 버튼을 누르면 GND에 연결되어 LOW가 됨
            return button.get_value(BUTTON_GPIO) == Value.INACTIVE

        previous_pressed = is_pressed()
        last_press_time = 0

        while True:
            pressed = is_pressed()
            now = time.monotonic()

            # 눌리는 순간에만 실행
            if pressed and not previous_pressed:
                if now - last_press_time >= 0.2:

                    last_press_time = now

                    # 다음 표정
                    face_index = (face_index + 1) % len(images)

                    show_face(face_index)
                    play_beep()

            previous_pressed = pressed

            time.sleep(0.01)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n테스트 종료")
