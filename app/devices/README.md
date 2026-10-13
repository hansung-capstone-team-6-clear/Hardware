# app/devices/ — 부품 제어

부품 하나에 파일 하나. `parts/`에서 단독 테스트를 통과한 코드를 함수로 정리해 여기에 옮긴다.
`main.py`는 이 함수들만 부르고, 핀 번호나 라이브러리를 직접 다루지 않는다.

| 파일 | 함수 | 부품 테스트 | 상태 |
| --- | --- | --- | --- |
| `button.py` | `setup(on_pressed, on_released)` | `parts/button` | 동작함 (gpiozero ↔ asyncio 연결 포함) |
| `audio.py` | `start_recording()`, `stop_recording() -> bytes` | `parts/audio` | TODO(10/31) |
| `led.py` | `show(color, mode)` | `parts/led` | TODO(10/31) |
| `lcd.py` | `show(face, text=None)` | `parts/lcd` | TODO(10/31) |

TTS 재생은 부품이 아니라 서비스 호출이라 `app/tts.py`에 있다.

## 규칙

1. 함수 이름과 인자는 바꾸지 않는다. 바꿔야 하면 `main.py`도 같이 고치고 PR에 적는다.
2. 핀 번호는 파일 맨 위 상수로 둔다 (예: `BUTTON_PIN = 17`). 전체 핀맵은 `parts/README.md`.
3. 색과 표정의 "의미"(어떤 상태에 무슨 색)는 `app/states.py`에서 정한다. 여기서는 "어떻게 켜는지"만.

## Pi 없이 확인하기

gpiozero는 가짜 핀으로 노트북에서도 돌릴 수 있다:

```bash
GPIOZERO_PIN_FACTORY=mock python -c "import devices.button"
```
