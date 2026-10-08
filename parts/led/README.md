# parts/led — WS2812B 24구 LED 링

데스크펫 상태(대기·듣는 중·생각 중·말하는 중·알림·오류)를 색으로 보여 준다.

## 배선

| LED 링 | Pi (GPIO / 물리 핀) |
| --- | --- |
| 5V | 5V (4) |
| GND | GND (20) |
| DIN | GPIO12 (32) — PWM0 |

## 주의

1. **밝기는 30% 이하.** 24개를 최대로 켜면 약 1.4A(개당 약 60mA)이고, Pi 5V 핀을 앰프와 같이 쓴다. 너무 밝으면 Pi가 재부팅될 수 있다.
2. `config.txt`에 `dtparam=audio=off`가 있어야 한다. 온보드 오디오가 같은 PWM을 쓴다.
3. Pi 신호는 3.3V라 LED가 깜빡이거나 색이 틀리면 레벨 시프터(예: 74AHCT125)를 단다.
4. `rpi_ws281x`는 하드웨어에 직접 접근해서 `sudo`로 실행해야 한다.

## 테스트

```bash
pip install rpi_ws281x      # app/ 가상환경에서
```

`test_led.py`로 저장하고 `sudo .venv/bin/python test_led.py`:

```python
import time

from rpi_ws281x import Color, PixelStrip

strip = PixelStrip(24, 12, brightness=64)  # 24개, GPIO12, 밝기 64/255 ≈ 25%
strip.begin()

colors = {  # 상태별 색 — app/states.py와 같아야 한다
    "IDLE 초록": Color(0, 255, 0),
    "LISTENING·THINKING 노랑": Color(255, 180, 0),
    "SPEAKING 파랑": Color(0, 0, 255),
    "ALERT 주황": Color(255, 80, 0),
    "ERROR 빨강": Color(255, 0, 0),
}
for name, color in colors.items():
    print(name)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()
    time.sleep(1.5)
```

## 완료 기준

- [ ] 5가지 색이 순서대로 보이고, 노랑과 주황이 눈으로 구분된다 (안 되면 색값을 조정해 `app/states.py`에 반영)
- [ ] 점멸(켜기 0.5초 / 끄기 0.5초)도 확인했다
- [ ] 오디오 재생과 LED를 동시에 켜도 소리가 끊기지 않는다

## 결과 기록

| 날짜 | 시도한 것 | 결과 | 메모 |
| --- | --- | --- | --- |
| | | | |
