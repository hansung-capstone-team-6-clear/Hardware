"""WS2812B 24구 LED 링 (GPIO12). 배선·테스트: parts/led/README.md

sudo로 실행해야 한다 (rpi_ws281x). 밝기는 30% 이하.
"""

COLORS = {  # parts/led 테스트에서 확인한 값으로 고친다
    "green": (0, 255, 0),
    "yellow": (255, 180, 0),
    "white": (255, 255, 255),
    "blue": (0, 0, 255),
    "orange": (255, 80, 0),
    "red": (255, 0, 0),
}


def show(color: str, mode: str) -> None:
    """color(COLORS의 키)로 링 전체를 켠다.

    mode: "solid" 계속 켜기 / "blink" 0.5초 간격 점멸 / "fast_blink" 0.15초 간격 점멸 (ALERT).

    blink는 다른 상태로 바뀔 때까지 계속돼야 하므로 백그라운드 작업(asyncio task)으로 돌리고,
    show()가 다시 불리면 이전 점멸을 멈춘다.
    """
    # TODO(hardware, 10/31)
    raise NotImplementedError
