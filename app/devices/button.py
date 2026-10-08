"""PTT 버튼 (GPIO17, 내부 풀업). 배선·테스트: parts/button/README.md"""

import asyncio
from collections.abc import Awaitable, Callable

from gpiozero import Button

BUTTON_PIN = 17

_button: Button | None = None  # 프로그램이 도는 동안 살아 있어야 이벤트가 온다


def setup(
    on_pressed: Callable[[], Awaitable[None]],
    on_released: Callable[[], Awaitable[None]],
) -> None:
    """버튼 누름·뗌에 async 함수를 연결한다. main()의 이벤트 루프 안에서 불러야 한다.

    gpiozero 콜백은 별도 스레드에서 불리므로, run_coroutine_threadsafe로 asyncio 루프에 넘긴다.
    (콜백에서 async 함수를 그냥 부르면 아무 일도 일어나지 않는다 — 자주 하는 실수)
    """
    global _button
    loop = asyncio.get_running_loop()
    _button = Button(BUTTON_PIN, bounce_time=0.05)
    _button.when_pressed = lambda: asyncio.run_coroutine_threadsafe(on_pressed(), loop)
    _button.when_released = lambda: asyncio.run_coroutine_threadsafe(on_released(), loop)
