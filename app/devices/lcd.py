"""ST7789 1.69" LCD (240×280, SPI). 배선·테스트: parts/lcd/README.md"""


def show(face: str, text: str | None = None) -> None:
    """assets/faces/{face}.png를 띄우고, text가 있으면 아래쪽에 한글로 덧붙인다.

    face: idle, listening, thinking, speaking, alert, surprised, happy (contracts § 1 output.lcd.expression)

    폰트: /usr/share/fonts/truetype/nanum/NanumGothic.ttf (setup에서 fonts-nanum 설치)
    """
    # TODO(hardware, 10/31)
    raise NotImplementedError
