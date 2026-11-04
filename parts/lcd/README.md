# parts/lcd — ST7789V2 1.69" LCD (240×280, SPI)

Raspberry Pi 4B에 LCD를 연결해 가로 방향(280×240)으로 표정 6가지를 순차 출력하는 데 성공했다. **단독 테스트까지 완료했고, 음성 파이프라인과 `app/` 연동은 아직 하지 않았다.**

## 하드웨어

| 항목 | 내용 |
| --- | --- |
| 보드 | Raspberry Pi 4B (8GB) |
| LCD | 1.69" IPS, ST7789V2, 240×280, 4-Wire SPI |
| 연결 | 브레드보드 + 암수 점퍼선 (개발·테스트용) |
| 장착 | 물리적으로 가로 방향 |

## 배선

실제 출력에 성공한 배선이다. 배선을 바꿀 때는 Pi 전원을 끈다.

| LCD 핀 | BCM GPIO | 물리 핀 | 기능 |
| --- | --- | --- | --- |
| GND | GND | 6 | 접지 |
| VCC | 3.3V | 1 | 전원 |
| SCL | GPIO11 | 23 | SPI Clock |
| SDA | GPIO10 | 19 | SPI MOSI |
| RES | GPIO25 | 22 | Reset |
| DC | GPIO24 | 18 | Data/Command |
| CS | GPIO5 | 29 | Chip Select |
| BLK | GPIO23 | 16 | 백라이트 |

브레드보드의 가운데 홈을 기준으로 A~E와 F~J는 연결되지 않으므로, LCD 핀과 점퍼선을 같은 연결 구역에 꽂는다.

**통합 시 주의:** 전체 핀맵은 마이크 3.3V에 물리 핀 1번, 앰프 GND에 6번을 배정했다. 지금 LCD도 같은 핀을 쓰므로, 전체 조립 때 핀맵대로 LCD 전원을 17번·14번으로 옮기거나 전원을 나눠 연결해야 한다. 17번·14번 연결은 아직 테스트하지 않았다.

## 설치

SPI를 켠다: `sudo raspi-config` → Interface Options → SPI → Yes

```bash
ls /dev/spidev*    # /dev/spidev0.0, /dev/spidev0.1이 보여야 한다
```

스크립트가 표정을 `~/deskpet/faces`에서 읽으므로 그 위치에 복사한다.

```bash
mkdir -p ~/deskpet/faces
cp parts/lcd/*.py parts/lcd/requirements.txt ~/deskpet/
cp app/assets/faces/*.png ~/deskpet/faces/
cd ~/deskpet
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt`에서 버전을 고정한 두 패키지(Adafruit-Blinka, gpiod)만 설치 버전이 확인된 값이다. 나머지는 Pi에서 `python -m pip freeze`로 확인한 뒤 고정한다.

## 실행

| 파일 | 동작 | 명령 |
| --- | --- | --- |
| `lcd_test.py` | 빨강·초록·파랑·흰색 출력 (세로, 각 2초) | `python lcd_test.py` |
| `lcd_face_test.py` | `idle.png` 가로 출력, Ctrl+C로 종료 | `python lcd_face_test.py` |
| `lcd_faces_cycle.py` | 표정 6개를 3초 간격으로 반복, Ctrl+C로 종료 | `python lcd_faces_cycle.py` |

`lcd_faces_cycle.py`는 동작이 확인된 기준 코드이므로 고치지 않고 보존한다. 3초 간격은 테스트용이며, 실제로는 상태 변경에 따라 표정이 바뀌어야 한다.

## 검증된 드라이버 설정

```python
CS, DC, RESET, BACKLIGHT = board.D5, board.D24, board.D25, board.D23

display = ST7789(
    spi,
    cs=digitalio.DigitalInOut(CS),
    dc=digitalio.DigitalInOut(DC),
    rst=digitalio.DigitalInOut(RESET),
    width=240,      # 드라이버에는 패널 실제 크기를 준다
    height=280,
    x_offset=0,
    y_offset=20,
    rotation=90,    # 회전은 드라이버에서만 한다
    baudrate=16000000,
)
```

이미지는 회전하지 않고, 비율을 유지해 280×240 흰색 캔버스 중앙에 놓는다.

## 오류 해결 이력

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 백라이트 GPIO18에서 `ValueError: (22, 'Invalid argument')` | `gpioinfo`에서 GPIO18이 커널 점유로 표시됨 | BLK를 GPIO23(16번)으로 이동 |
| CS GPIO8에서 `OSError: [Errno 16] Device or resource busy` | 리눅스 SPI 드라이버가 GPIO8을 `spi0 CS0`로 점유 | CS를 GPIO5(29번)로 이동 |
| 가로 전환 시 화면 깨짐 | 드라이버에 `width=280, height=240`을 지정 | 드라이버는 240×280 유지, 캔버스만 280×240 |
| 가로 출력 방향이 맞지 않음 | `image.rotate(270)`과 드라이버 회전이 겹침 | 이미지 회전 제거, `rotation=90`만 사용 |
| 표정 옆 검은 여백 | 세로 이미지를 가로 캔버스에 배치 | 캔버스 배경을 흰색으로 변경 (PNG 내부는 그대로) |

GPIO8 충돌 때문에 `board.CE0`/`board.D8`로 CS를 직접 잡는 예제는 이 환경에서 그대로 쓸 수 없다.

## 완료 기준

- [x] `app/assets/faces/`의 표정 PNG를 띄웠다 (6개 순차 출력)
- [ ] 화면 전체가 빈틈없이 채워진다 — 색상 테스트와 가로 출력은 정상이었지만 밀림·잘림 여부는 별도로 기록하지 않음
- [ ] 한글이 깨지지 않고 보인다 — 미테스트

## 결과 기록

| 날짜 | 시도한 것 | 결과 | 메모 |
| --- | --- | --- | --- |
| 2026-11-05 | RGB 색상, 가로 출력, 표정 6개 순차 출력 | 성공 | 실제 LCD에서 눈으로 확인. 위 배선 기준 |

## 앱 연동 전 결정할 점

연동은 아직 하지 않았다. 기존 코드를 검토한 결과는 다음과 같다.

1. **연결 위치:** `app/devices/README.md` 규칙에 따라 `app/devices/lcd.py`의 `show(face, text=None)`을 구현한다. 별도 컨트롤러를 만들기보다 이 함수 안에서 LCD를 한 번만 초기화하고 이미지를 캐싱하는 편이 팀 구조에 맞다.
2. **ERROR 표정:** `app/states.py`는 ERROR에 `surprised`를 쓰는데, 이번 이미지는 `error.png`다. `surprised.png`와 `happy.png`는 이번 이미지에 없어 지금 연동하면 해당 표정을 찾지 못한다. contracts와 함께 정해야 한다.
3. **화면 방향:** 팀 표정 문서는 세로 240×280과 아래쪽 문구 영역을 전제로 한다. 가로 출력에서는 이미지가 축소되고 좌우에 여백이 생기므로 문구 위치를 다시 정해야 한다.
4. **GPIO18:** 오디오 BCLK로 배정된 핀인데, 이번 환경에서 커널 점유로 표시됐다. 오디오 테스트 때 함께 확인한다.
5. **음성 파이프라인:** `deskpet_voice_pipeline.py`의 `set_state()`는 터미널 출력만 하며 LISTENING·ALERT 상태가 없다. 응답 대기 중에도 THINKING 표정이 유지되는지 실제로 확인해야 한다.
6. **안정성:** LCD 오류가 음성 처리를 멈추지 않게 예외를 처리하고, 한 곳에서만 LCD에 접근하게 한다.
