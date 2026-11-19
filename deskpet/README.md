# DeskPet (Raspberry Pi 4B)

버튼을 누르고 말하면 녹음해서 백엔드(`/api/voice`)로 보내고, 돌아온 답을 한국어 음성으로 읽어 주는 데스크펫.
LCD에 상태별 표정을 띄우고, 저장한 작업은 **마감 1시간 전**에 스피커로 알려 준다.

> 이 문서는 ZIP 안의 실제 코드에서 확인한 내용만 "동작함"으로 적었다.
> 코드가 없거나 확인하지 못한 부분은 아래 [구현 현황](#구현-현황)에 따로 적었다.

## 폴더 구조

```text
deskpet/
├── src/                     실제 실행 코드
│   ├── deskpet_voice.py     메인 앱: 버튼 → LCD → 녹음 → /api/voice → TTS 재생 (+ 알람 자동 등록)
│   ├── deskpet_alarm.py     마감 1시간 전 알람: SQLite 저장, 등록·목록·삭제 명령, systemd 상시 감시
│   └── deskpet_env.py       .env 로더, 백엔드 주소·토큰 읽기
├── assets/faces/            LCD 표정 PNG 6개 (idle, listening, thinking, speaking, alert, error)
├── scripts/install_alarm.sh 알람 systemd 서비스 설치
├── tools/                   개발용 도구 (하드웨어 없이 파일로 실행)
├── tests/
│   ├── unit/                오프라인 자동 테스트 (알람·SQLite) — PC에서도 실행 가능
│   └── hardware/            Pi에서 손으로 돌리는 부품 테스트 (LCD·버튼·마이크·스피커)
├── legacy/                  구버전 코드 (기능 보존용, legacy/README.md 참고)
├── docs/                    원본 알람 메모, 정리 내역
├── requirements.txt
├── .env.example
└── .gitignore
```

## 하드웨어

| 부품 | 모델 (코드 기준) | 연결 |
|---|---|---|
| Pi | Raspberry Pi 4B | |
| LCD | ST7789 1.69" 240×280 IPS (SPI) | SPI0 |
| 버튼 | 푸시 버튼 1개 | GPIO17 ↔ GND |
| 마이크 | INMP441 (I2S) | I2S, L/R 핀은 GND (왼쪽 채널 사용) |
| 앰프 + 스피커 | MAX98357A (I2S) | I2S |

### GPIO 배선표

**코드에서 확인한 핀** (`src/deskpet_voice.py`, `tests/hardware/*.py`):

| 기능 | BCM GPIO | 물리 핀 | 비고 |
|---|---|---|---|
| 버튼 | GPIO17 | 11 | 다른 쪽 다리는 GND. 내부 풀업 사용 → 누르면 LOW |
| LCD CS | GPIO5 | 29 | `board.D5` |
| LCD DC | GPIO24 | 18 | `board.D24` |
| LCD RST | GPIO25 | 22 | `board.D25` |
| LCD 백라이트(BL) | GPIO23 | 16 | `board.D23`, 시작할 때 켬 |
| LCD SDA(MOSI) | GPIO10 | 19 | SPI0 고정 핀 (`board.SPI()`) |
| LCD SCL(SCLK) | GPIO11 | 23 | SPI0 고정 핀 |
| LCD VCC / GND | — | 1 (3.3V) / 6 | |

LCD 설정: `width=240, height=280, y_offset=20, rotation=90, baudrate=16MHz` → 가로 280×240으로 그린다.

**코드에 없는 핀 (확인 필요)**: I2S 핀은 `arecord`/`aplay`가 ALSA 장치(`plughw:2,0`)로만 접근하기 때문에 코드에 적혀 있지 않다.
아래는 Pi 4B의 **표준 I2S 핀**이다. 실제 배선과 `/boot/firmware/config.txt`의 오버레이 설정을 확인한 뒤 이 표를 고쳐 주세요.

| 신호 | BCM GPIO | 물리 핀 | INMP441 | MAX98357A |
|---|---|---|---|---|
| BCLK | GPIO18 | 12 | SCK | BCLK |
| LRCLK(WS) | GPIO19 | 35 | WS | LRC |
| 마이크 데이터 입력 | GPIO20 | 38 | SD | — |
| 스피커 데이터 출력 | GPIO21 | 40 | — | DIN |
| 전원 | — | 1 (3.3V) / 2 (5V) | VDD 3.3V | VIN 5V |
| GND | — | 6, 9 등 | GND, L/R | GND |

### 오디오 형식 (코드 기준)
- 녹음: `arecord -D plughw:2,0 -f S32_LE -r 48000 -c 2`, 최대 15초
- 업로드: ffmpeg로 왼쪽 채널만 뽑아 **16kHz / 16bit / 모노 WAV**
- 재생: edge-tts mp3 → ffmpeg로 48kHz 스테레오 WAV(볼륨 0.35) → `aplay -D plughw:2,0`

## 설치 (Pi)

```bash
sudo apt update
sudo apt install -y python3-venv ffmpeg alsa-utils fonts-dejavu-core
# SPI 켜기: sudo raspi-config → Interface Options → SPI → Enable
# I2S 오버레이는 사용 중인 설정을 그대로 쓴다 (이 레포에 config.txt 설정 파일은 없음)

git clone <이 레포 주소> ~/deskpet-app
cd ~/deskpet-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env        # DESKPET_BACKEND_URL, DESKPET_DEVICE_TOKEN 채우기
```

사운드 카드 번호 확인: `aplay -l`, `arecord -l`. `plughw:2,0`이 아니면 `.env`의 `DESKPET_AUDIO_DEVICE`를 고친다.

## 실행

### 1. 메인 앱 (음성 대화)

```bash
cd ~/deskpet-app && source .venv/bin/activate
python src/deskpet_voice.py
```

- 버튼 누르는 동안 녹음(LCD `listening`) → 떼면 `thinking` → 백엔드 응답 → `speaking` → `idle`
- 0.4초보다 짧게 누르면 무시한다. 15초가 지나면 자동으로 녹음을 끝낸다.
- 오류가 나면 LCD `error`를 1초 보여 주고 `idle`로 돌아간다.
- 종료: `Ctrl+C`
- 메인 앱은 systemd 서비스로 등록되어 있지 않다. 필요하면 직접 실행하거나 서비스를 새로 만들어야 한다.

### 2. 마감 알람 직접 사용

```bash
python src/deskpet_alarm.py add "보고서 작성" "2026-11-20 15:00"   # 한국시간
python src/deskpet_alarm.py add "테스트" "+61m"                      # 61분 뒤 마감 → 약 1분 뒤 알림
python src/deskpet_alarm.py list
python src/deskpet_alarm.py remove <알림ID>
python src/deskpet_alarm.py test                                     # 지금 바로 알림음 + 음성
python src/deskpet_alarm.py run                                      # 상시 감시 (보통 systemd가 실행)
```

### 3. systemd 알람 서비스 설치

```bash
cd ~/deskpet-app
bash scripts/install_alarm.sh        # sudo 없이 실행 (스크립트 안에서 필요한 곳만 sudo)
```

스크립트가 하는 일:
1. `/etc/systemd/system/deskpet-alarm.service` 생성
   (`ExecStart=<레포>/.venv/bin/python -u <레포>/src/deskpet_alarm.py run`, `Restart=always`)
2. `systemctl enable --now`로 부팅할 때 자동 시작

확인과 관리:

```bash
systemctl status deskpet-alarm --no-pager
sudo journalctl -u deskpet-alarm -n 40 --no-pager
sudo systemctl restart deskpet-alarm
sudo systemctl disable --now deskpet-alarm     # 끄기
```

## 마감 1시간 전 알림과 SQLite 구조

- DB 위치: `~/deskpet/reminders.sqlite3` (`DESKPET_HOME`으로 바꿀 수 있음). 재부팅해도 남는다.
- 서비스가 **4초마다** 확인한다. 그래서 알림이 몇 초 늦을 수 있다.
- 알림 시각은 **마감 − 3600초**이다 (`ALERT_BEFORE_SEC`).
- 1시간 전 시점이 지난 뒤에 부팅했어도, 아직 마감 전이면 바로 늦은 알림을 한다. 마감이 지났으면 알리지 않고 `expired`로 바꾼다.
- 재생에 실패하면 `pending`으로 되돌려 다음 주기에 다시 시도한다. 성공하면 `alerted`로 바꾸고 다시 울리지 않는다.
- 알림 음성은 **등록할 때** edge-tts로 미리 만들어 `reminder_audio/<id>.wav`에 저장한다. 그래서 알림 시점에는 인터넷이 필요 없다. 등록할 때 만들지 못했으면 부저음만 울린다.
- 메인 앱과 알람이 스피커를 동시에 쓰지 않도록 `.audio_playback.lock` 파일 잠금을 같이 쓴다.

```sql
CREATE TABLE reminders (
    id          TEXT PRIMARY KEY,      -- uuid 10자리
    title       TEXT NOT NULL,         -- 최대 150자
    deadline_ts INTEGER NOT NULL,      -- 마감 (epoch 초)
    alert_ts    INTEGER NOT NULL,      -- 알림 = deadline_ts - 3600
    state       TEXT NOT NULL DEFAULT 'pending',  -- pending | notifying | alerted | expired
    source_key  TEXT UNIQUE,           -- backend:<task id> 또는 local:<해시> (중복 방지)
    voice_file  TEXT,                  -- 미리 만든 음성 wav 경로
    created_ts  INTEGER NOT NULL,
    alerted_ts  INTEGER
);
CREATE INDEX idx_due ON reminders(state, alert_ts);
```

**백엔드 응답으로 자동 등록되는 조건**: 응답의 `type`이 `task_created` 또는 `task_updated` 등이고, JSON 안에 **구조화된 마감 필드**가 있어야 한다
(`deadline`, `due_at`, `due_date`, `deadlineAt` 등, 안쪽 객체까지 찾음).
TTS 문장만 있으면 날짜를 추측하지 않고 등록하지 않는다. 지금 백엔드가 이 필드를 보내는지는 확인하지 못했다.

## 테스트

| 종류 | 위치 | 실행 |
|---|---|---|
| 자동 (오프라인) | `tests/unit/test_alarm.py` | `python -m unittest discover -s tests/unit -v` — PC(Windows 포함)에서도 됨 |
| 하드웨어 (수동, Pi) | `tests/hardware/` | 아래 표 |
| 개발 도구 (파일 기반) | `tools/` | 아래 표 |

자동 테스트가 확인하는 것: 1시간 전 계산, 알림 1회만 재생, 마감 지나면 `expired`, 재생 실패 시 재시도, 중복 등록 방지, 날짜 형식, 백엔드 응답에서 자동 등록·건너뛰기.

| `tests/hardware/` | 확인하는 것 |
|---|---|
| `lcd_test.py` | LCD 색 4개 (빨강·초록·파랑·흰색) |
| `lcd_face_test.py` | idle 표정 1장 |
| `lcd_faces_cycle.py` | 표정 6개를 3초씩 돌아가며 표시 |
| `button_face_beep.py` | 버튼 누르면 표정이 바뀌고 삐 소리 |
| `record_play.py` | 버튼 누름 녹음 → 뗌 → 내 목소리 재생 (버튼+LCD+마이크+스피커 통합) |
| `speaker_loop.py`, `tts_loop.py` | 저장된 wav 무한 반복 재생 (`~/deskpet/test_audio/`의 개인 파일 필요) |
| `lcd_speaker_together.py` | LCD 순환 + 스피커 재생을 동시에 |

| `tools/` | 용도 |
|---|---|
| `text_client.py` | `/api/text`에 글자로 질문 |
| `voice_file_client.py` | wav 파일 하나를 `/api/voice`로 전송 |
| `voice_file_pipeline.py` | 형식 변환 → VAD(말소리 검사) → 전송. `--dry-run`이면 전송하지 않음 |
| `audio_converter.py` | 48kHz 스테레오 → 16kHz 모노 변환·검사 |
| `vad_check_file.py`, `vad_check_folder.py` | 파일 하나 / 폴더 전체 VAD 검사 |

## 구현 현황

| 기능 | 상태 | 근거 |
|---|---|---|
| 버튼 PTT 녹음 (디바운스 50ms, 최대 15초) | 코드 있음 | `src/deskpet_voice.py` |
| LCD 상태 표정 (idle/listening/thinking/speaking/error) | 코드 있음 | 같은 파일 |
| `/api/voice` 업로드, `output.tts` 음성 재생 | 코드 있음 | 같은 파일 |
| 마감 1시간 전 알람 + SQLite + systemd | 코드 있음, 오프라인 테스트 통과 | `src/deskpet_alarm.py`, `tests/unit` |
| 백엔드 응답으로 알람 자동 등록 | 코드 있음 / **실제 백엔드 응답으로는 확인 못 함** | `register_from_backend` |
| 알림할 때 LCD `alert` 표정 | **없음** | 알람 서비스는 LCD를 건드리지 않음 (메인 앱과 충돌 방지) |
| 백엔드 WebSocket 알림 (`/ws/hardware/...`) | **없음** | 이 ZIP에 WS 코드가 없음 |
| 상태 LED | **없음** | LED 코드가 없음 (`voice_file_pipeline.py`는 print만 함) |
| VAD로 무음 걸러내기 | 도구에만 있음 | 메인 앱에는 연결되어 있지 않음 |
| 메인 앱 자동 시작 (systemd) | **없음** | 알람 서비스만 있음 |

## 주의할 점

- **타임아웃이 두 가지다.** 메인 앱은 원본 값인 연결 8초 / 응답 **90초**를 유지했다. 도구(`voice_file_pipeline.py`)는 3초 / 10초이다.
  팀에서 정한 10초 정책에 맞추려면 `.env`에서 `DESKPET_HTTP_READ_TIMEOUT=10`으로 바꾼다.
- 시스템 시간이 틀리면 알림 시각도 틀어진다. `timedatectl`로 확인한다. 입력하는 시각은 한국시간(Asia/Seoul)이다.
- 이전에 실행한 `speaker-test`나 무한 반복 `aplay`가 돌고 있으면 스피커가 충돌한다. 먼저 끈다.

## GitHub에 올리지 않는 것 (`.gitignore`)
`.env`(토큰·서버 주소), `*.sqlite3`(알람 DB), `reminder_audio/`, `test_audio/`, `*.wav`, `*.mp3`(개인 음성), `.venv/`, `__pycache__/`
