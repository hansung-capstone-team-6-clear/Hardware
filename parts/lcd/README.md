# parts/lcd — ST7789 1.69" LCD (240×280, SPI)

표정 이미지와 짧은 문구(예: "보고서 검토 마감 1시간 전")를 보여 준다.

## 배선

| LCD 핀 | Pi (GPIO / 물리 핀) |
| --- | --- |
| VCC / GND | 3.3V (17) / GND (14) |
| SCL / SDA | GPIO11 (23) / GPIO10 (19) |
| CS / DC / RST | GPIO8 (24) / GPIO24 (18) / GPIO25 (22) |
| BL (백라이트, 있으면) | 3.3V |

`config.txt`에 `dtparam=spi=on`이 있어야 한다 (`ls /dev/spidev0.0`으로 확인).

## 라이브러리 (후보)

`adafruit-circuitpython-rgb-display`의 ST7789 드라이버가 240×280 패널을 `y_offset`으로 지원한다 (추정 — 테스트로 확인).
화면이 한쪽으로 밀리거나 잘리면 `x_offset`·`y_offset`·`rotation`을 바꿔 가며 맞추고 결과를 기록한다.

```bash
pip install adafruit-circuitpython-rgb-display pillow   # app/ 가상환경에서
```

## 테스트

`test_lcd.py`로 저장하고 `python test_lcd.py`:

```python
import board
import digitalio
from adafruit_rgb_display import st7789
from PIL import Image, ImageDraw, ImageFont

display = st7789.ST7789(
    board.SPI(),
    cs=digitalio.DigitalInOut(board.CE0),
    dc=digitalio.DigitalInOut(board.D24),
    rst=digitalio.DigitalInOut(board.D25),
    width=240,
    height=280,
    y_offset=20,
    baudrate=24_000_000,
)

image = Image.new("RGB", (240, 280), "white")
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", 22)  # setup에서 fonts-nanum 설치
draw.text((20, 120), "마감 1시간 전", font=font, fill="black")
display.image(image)
```

## 완료 기준

- [ ] 화면 전체가 빈틈없이 흰색으로 채워진다 (밀림·잘림 없음)
- [ ] 한글이 깨지지 않고 보인다
- [ ] `../../app/assets/faces/`의 표정 PNG 하나를 띄웠다

## 결과 기록

| 날짜 | 시도한 것 | 결과 | 메모 |
| --- | --- | --- | --- |
| | | | |
