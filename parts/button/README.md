# parts/button — PTT(누르고 말하기) 버튼

누르는 동안 녹음하고, 떼면 백엔드로 보낸다. 산와 30mm 아케이드 버튼(OBSF-30) 기준.

## 배선

| 버튼 단자 | Pi (GPIO / 물리 핀) |
| --- | --- |
| 한쪽 | GPIO17 (11) |
| 다른 쪽 | GND (예: 9, 14, 20 중 빈 곳) |

저항은 필요 없다. Pi 내부 풀업을 켜서, 누르면 GPIO17이 GND와 붙는다.

## 테스트

`test_button.py`로 저장하고 `python test_button.py` (Pi OS에 `gpiozero`가 기본 설치돼 있다):

```python
from signal import pause

from gpiozero import Button

button = Button(17, bounce_time=0.05)  # 내부 풀업, 50ms 떨림 무시
button.when_pressed = lambda: print("눌림 → 녹음 시작")
button.when_released = lambda: print("뗌 → 업로드")
pause()
```

## 완료 기준

- [ ] 한 번 누르고 떼면 "눌림", "뗌"이 **한 번씩만** 출력된다 (여러 번 나오면 `bounce_time`을 늘린다)
- [ ] 15초 넘게 누르고 있어도 프로그램이 멈추지 않는다 (녹음 최대 15초는 app에서 자른다)

## 결과 기록

| 날짜 | 시도한 것 | 결과 | 메모 |
| --- | --- | --- | --- |
| | | | |

## 테스트 결과 (2026-10-15)

- 부품: 3핀 버튼 모듈 (GND / VCC / IN)
- 배선: VCC → Pin 1 (3.3V), GND → Pin 6, IN → Pin 11 (GPIO17)
- 실행: `python parts/button/test_button.py`
- 결과: 평소 1, 누르면 0 (active-low). 3회 눌러 3회 모두 정확히 감지, 채터링 없음
- 앱 코드: `Button(17, pull_up=True)` 사용 가능
- ⚠️ VCC는 반드시 3.3V (5V 연결 금지)
