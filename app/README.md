# app/ — Pi에서 실제로 도는 데스크펫 프로그램

버튼·마이크·스피커·LED·LCD를 묶고 백엔드와 통신한다. **판단은 하지 않는다** — 업무 해석·Eureka 호출은 백엔드가 한다.

## 파일

```text
app/
├── main.py            진입점: 버튼·알림 이벤트 → 상태 바꾸기 → 녹음·업로드·재생
├── states.py          상태 6개(IDLE…ERROR)별 LED 색·LCD 표정 — 여기 한 곳에서만 정한다
├── backend_client.py  백엔드 통신: send_voice() (POST /voice), listen_alerts() (WS)
├── tts.py             문장 → 음성 재생 (edge-tts + mpg123)
├── config.py          .env 읽기
├── devices/           부품 제어: button, audio, led, lcd — devices/README.md
├── assets/faces/      LCD 표정 이미지 — assets/faces/README.md
├── requirements.txt
└── .env.example
```

## 흐름

```text
버튼 누름 ──▶ LISTENING  녹음 시작
버튼 뗌   ──▶ THINKING   녹음 끝 → send_voice() ──▶ SPEAKING/ERROR  tts.speak(text) ──▶ IDLE
WS 알림   ──▶ ALERT      tts.speak(alert["text"]) ──▶ IDLE
```

## 왜 이 구조인가

- **MVC가 아니다.** 화면을 그리는 앱이 아니라 "이벤트(버튼·알림)가 오면 상태를 바꾸고 장치를 움직이는" 프로그램이라,
  `main.py`(흐름) + `states.py`(상태별 표현) + `devices/`(장치) + `backend_client.py`(통신)로 나눴다.
  굳이 비유하면 `states.py`가 View, `main.py`가 Controller, 백엔드가 Model이다.
- **부품 코드를 `devices/`에 모은 이유**: 핀·라이브러리가 바뀌어도 `main.py`를 고칠 필요가 없게 하려고.

## 실행

Pi에서 (처음이면 `../setup/README.md`부터):

```bash
cd Hardware/app
source .venv/bin/activate
cp .env.example .env          # BACKEND_URL, DEVICE_TOKEN 채우기
sudo .venv/bin/python main.py # LED(rpi_ws281x) 때문에 sudo
```

노트북에서 (Pi 없이 백엔드 연결만 확인):

```bash
cd Hardware/app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # BACKEND_URL=http://localhost:8000
GPIOZERO_PIN_FACTORY=mock python main.py
```

백엔드(`desk-pet-backend`)가 켜져 있으면 `백엔드 WS 연결됨` 로그가 나온다. 꺼져 있으면 5초마다 재연결을 시도한다.

## 지금 동작하는 것 / 할 일

| 동작함 | TODO (담당: hardware) |
| --- | --- |
| 버튼 이벤트 연결, 상태 로그, 백엔드 WS 연결·재연결·ping, 알림 수신, `send_voice()` | `devices/audio.py`·`led.py`·`lcd.py`, `tts.py`, `main.py`의 녹음·업로드·재생 연결 (10/31), 알림 음성 (11/14) |

`grep -rn "TODO(" .`로 남은 일을 모아 볼 수 있다.
