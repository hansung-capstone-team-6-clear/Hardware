
import time
from pathlib import Path

import board
import digitalio
from PIL import Image
from adafruit_rgb_display.st7789 import ST7789

# =====================================
# LCD 설정
# =====================================

LCD_WIDTH = 240
LCD_HEIGHT = 280

# 가로 화면 해상도
WIDTH = 280
HEIGHT = 240

# 실제 연결한 GPIO
CS = board.D5
DC = board.D24
RESET = board.D25
BACKLIGHT = board.D23

# 표정 표시 간격 (초)
DISPLAY_TIME = 3

# 표정 순서
FACES = [
    "idle",
    "listening",
    "thinking",
    "speaking",
    "alert",
    "error",
]

# =====================================
# LCD 초기화
# =====================================

bl = digitalio.DigitalInOut(BACKLIGHT)
bl.direction = digitalio.Direction.OUTPUT
bl.value = True

spi = board.SPI()

display = ST7789(
    spi,
    cs=digitalio.DigitalInOut(CS),
    dc=digitalio.DigitalInOut(DC),
    rst=digitalio.DigitalInOut(RESET),
    width=LCD_WIDTH,
    height=LCD_HEIGHT,
    x_offset=0,
    y_offset=20,
    rotation=90,
    baudrate=16000000,
)

print("[LCD] 초기화 완료")

# =====================================
# 표정 이미지 준비
# =====================================

faces_dir = Path(__file__).resolve().parents[2] / "assets" / "faces"

images = {}

for face in FACES:
    matches = list(faces_dir.rglob(f"{face}.png"))

    if not matches:
        print(f"[WARNING] {face}.png 없음")
        continue

    image = Image.open(matches[0]).convert("RGB")

    # 이미지 비율 유지
    image.thumbnail(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS
    )

    # 흰색 배경
    canvas = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        "white"
    )

    # 이미지 중앙 정렬
    x = (WIDTH - image.width) // 2
    y = (HEIGHT - image.height) // 2

    canvas.paste(image, (x, y))

    images[face] = canvas

    print(f"[LOAD] {face}.png")

if not images:
    raise RuntimeError("출력 가능한 표정 이미지가 없습니다.")

# =====================================
# 표정 순차 출력
# =====================================

print("\n[LCD] 표정 순차 출력 시작")

try:
    while True:
        for face in FACES:
            if face not in images:
                continue

            print(f"[LCD] 현재 표정: {face.upper()}")

            display.image(images[face])

            time.sleep(DISPLAY_TIME)

except KeyboardInterrupt:
    print("\n[LCD] 테스트 종료")
