
import time
import board
import digitalio
from PIL import Image
from adafruit_rgb_display.st7789 import ST7789

# Raspberry Pi GPIO 번호 (BCM)
CS = board.D5
DC = board.D24
RESET = board.D25
BACKLIGHT = board.D23

# LCD 백라이트 켜기
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
    width=240,
    height=280,
    x_offset=0,
    y_offset=20,
    rotation=0,
    baudrate=16000000,
)

print("LCD 색상 테스트 시작")

for color in ["RED", "GREEN", "BLUE", "WHITE"]:
    print("출력:", color)
    image = Image.new("RGB", (240, 280), color)
    display.image(image)
    time.sleep(2)

print("색상 테스트 완료")
