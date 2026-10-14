# app/ — Pi에서 실제로 도는 데스크펫 프로그램

버튼·마이크·스피커·LED·LCD를 묶고 백엔드와 통신한다. **판단은 하지 않는다** — 업무 해석·Eureka 호출은 백엔드가 한다.

## 파일

```text
app/
├── main.py            진입점: 버튼·알림 이벤트 → 상태 바꾸기 → 녹음·업로드·재생
├── states.py          상태 6개(IDLE…ERROR)별 LED 색·LCD 표정 — 여기 한 곳에서만 정한다
├── backend_client.py  백엔드 통신: send_voice() (POST /api/voice), listen() (WS /ws/hardware/{user_id})
├── tts.py             문장 → 음성 재생 (edge-tts + mpg123)
├── config.py          .env 읽기
├── devices/           부품 제어: button, audio, led, lcd — devices/README.md
├── assets/faces/      LCD 표정 이미지 — assets/faces/README.md
├── requirements.txt
└── .env.example
```

## 흐름

```text
버튼 누름 ──▶ LISTENING  녹음 시작 (IDLE이 아니면 무시)
버튼 뗌   ──▶ THINKING   녹음 끝 → send_voice() ──▶ status OK면 SPEAKING, 아니면 ERROR → output.tts 재생 ──▶ IDLE
WS 알림   ──▶ ALERT      output.tts 재생 ──▶ IDLE
```

백엔드와 주고받는 주소·메시지는 2026-10-07 하드웨어 결정(MVP Mock Server 형식) 그대로다:
`POST /api/voice`, `WS /ws/hardware/{user_id}`, 텍스트 `PING` → `{"event": "PONG"}`, 응답·알림의 `output.tts`·`output.lcd`.
정본은 knowledge 레포 `projects/eureka-desk-pet/contracts.md`.

## 팀 문서의 인터페이스 이름과 파일

| 인터페이스 (wiki `desk-pet-hardware-interfaces`) | 코드 |
| --- | --- |
| `IButtonInput` | `devices/button.py` |
| `IAudioCapture` | `devices/audio.py` |
| `IHardwareOutput` | `devices/led.py`, `devices/lcd.py`, `tts.py` |
| `IVoiceUpload` | `backend_client.send_voice()` |
| `IBackendConnection` | `backend_client.listen()` |
| `IDeviceStateManager` | `main.py` (흐름) + `states.py` (상태표) |
| `IDeviceStatusMonitor` | 1차: WS 끊김 로그. Wi-Fi 60초 점검 → ERROR 표시는 TODO |

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

Windows(PowerShell)에서는 이렇게 실행한다:

```powershell
cd Hardware\app
py -m venv .venv
.venv\Scripts\Activate.ps1      # 막히면: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
cp .env.example .env            # BACKEND_URL=http://127.0.0.1:8000
$env:GPIOZERO_PIN_FACTORY="mock"
python main.py
```

> Windows에서는 `BACKEND_URL`에 `localhost` 대신 `127.0.0.1`을 쓴다.
> `localhost`가 IPv6 주소로 먼저 연결되면, 8000번 포트에 떠 있는 다른 서버에서 `HTTP 400`을 받을 수 있다.

백엔드(`desk-pet-backend`)가 켜져 있으면 `백엔드 WS 연결됨` 로그가 나온다. 꺼져 있으면 3초마다 재연결을 시도한다.
## 지금 동작하는 것 / 할 일

| 동작함 | TODO (담당: hardware) |
| --- | --- |
| 버튼 이벤트 연결, 상태 로그, 백엔드 WS 연결·3초 재연결·PING, 알림 수신, `send_voice()` | `devices/audio.py`·`led.py`·`lcd.py`, `tts.py`, `main.py`의 녹음·업로드·재생 연결 (10/31), 알림 음성 (11/14) |

`grep -rn "TODO(" .`로 남은 일을 모아 볼 수 있다.
