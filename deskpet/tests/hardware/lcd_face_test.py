
import time
from pathlib import Path

import board
import digitalio
from PIL import Image
from adafruit_rgb_display.st7789 import ST7789

# 기존에 성공한 GPIO 연결
CS = board.D5
DC = board.D24
RESET = board.D25
BACKLIGHT = board.D23

# LCD 실제 패널 크기
LCD_WIDTH = 240
LCD_HEIGHT = 280

# 가로 화면 크기
WIDTH = 280
HEIGHT = 240

# 백라이트
bl = digitalio.DigitalInOut(BACKLIGHT)
bl.direction = digitalio.Direction.OUTPUT
bl.value = True

# SPI 초기화
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

# 이미지 찾기
faces_dir = Path(__file__).resolve().parents[2] / "assets" / "faces"
matches = list(faces_dir.rglob("idle.png"))

if not matches:
    raise FileNotFoundError("idle.png를 찾을 수 없습니다.")

image = Image.open(matches[0]).convert("RGB")

# 세로 원본을 비율 유지하면서 가로 화면에 배치
image.thumbnail((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
x = (WIDTH - image.width) // 2
y = (HEIGHT - image.height) // 2

canvas.paste(image, (x, y))

# 드라이버가 회전하므로 이미지 자체는 회전하지 않음
display.image(canvas)

print("[LCD] 가로 출력 완료")
print("[LCD] 이미지 크기:", canvas.size)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("[LCD] 종료")
