# DeskPet 마감 1시간 전 로컬 알람

## 기능

- 로컬 SQLite: `~/deskpet/reminders.sqlite3`에 제목/마감/알림/재생 여부 저장 (재부팅 후에도 보존)
- 마감 **정확히 한 시간 전** 부저음 + 한국어 음성으로 알림. 시스템 서비스가 4초마다 확인하므로 수초 오차 가능.
- Pi 전원이 켜져 있어야 작동. 한 시간 전을 지난 후 부팅했더라도 **마감 전이면** 즉시 늦은 알림. 마감 뒤에는 알리지 않고 `expired`로 처리.
- 알림이 정상 완료되면 `alerted`로 기록하고 반복하지 않음.
- Task 등록할 때 edge-tts로 wav를 미리 생성하여 저장. 등록 시 인터넷이 안 되면 부저음으로만 알림.
- 스피커 ALSA 카드 2 `plughw:2,0`을 사용. 기존 GPIO, LCD, I2S 설정 건드리지 않음.
- LCD 표정은 이번 서비스에서 직접 만지지 않음 (메인 앱과 동시 LCD 접근 충돌 방지).

## Pi 설치

Windows에서 받은 ZIP을 Pi의 `~/deskpet/`로 `scp` 한 다음:

```bash
cd ~/deskpet
unzip -o deskpet_alarm_bundle.zip
source .venv/bin/activate
python -m pip install edge-tts  # 이미 설치했으면 생략 가능
bash install_alarm.sh
```

서비스 상태:

```bash
systemctl status deskpet-alarm --no-pager
sudo journalctl -u deskpet-alarm -n 40 --no-pager
```

## 직접 명령어

```bash
cd ~/deskpet
source .venv/bin/activate
python deskpet_alarm.py test
python deskpet_alarm.py add "보고서 작성" "2026-11-20 15:00"
python deskpet_alarm.py list
python deskpet_alarm.py add "테스트" "+61m"
python deskpet_alarm.py remove <알림ID>
```

`+61m`은 지금부터 61분 후 마감으로 등록하므로, 실행 중인 서비스가 **약 1분 후** 알림을 재생한다. 실험 후 `list`로 확인한다.

## 백엔드와 연동

`deskpet_backend_voice_alarm.py`는 기존 `deskpet_backend_voice.py` 기반이며 원본을 **덮어쓰지 않음**.

```bash
cd ~/deskpet
source .venv/bin/activate
# 기존 터미널에 백엔드 URL과 DESKPET_DEVICE_TOKEN 환경변수가 설정되어 있어야 함.
python deskpet_backend_voice_alarm.py
```

`task_created` 응답에 **구조화된 마감 시각**(예: `task.deadline`, `task.due_at`, `data.task.deadline`)이 있어야 자동으로 Pi에 등록된다. 해당 필드 없이 TTS 문장만 있으면 날짜를 추측해서 등록하지 않는다. 그 경우 서버 응답 JSON 스키마에 마감 필드를 추가하거나 `deskpet_alarm.py add` 명령으로 입력해야 한다. 서버의 기존 작업을 자동으로 내려받는 기능(동기화)은 별도로 구현해야 한다. 백엔드가 작업 생성을 완료해도 Pi에서 자동 등록했다는 로그가 없으면 알람이 저장됐다고 판단하면 안 된다.

## 안전/오디오 동시성

- 음성 출력과 알람은 `.audio_playback.lock` 파일을 공유해 `aplay` 충돌을 줄임.
- 다만 종전의 `speaker-test`, 별도 무한 반복 `aplay`, 녹음 중 출력과는 충돌할 수 있으므로 테스트 시 기존 재생을 정지.
- `Ctrl+Z` 대신 `Ctrl+C`로 중단.
- 스피커에서 삐 소리가 길게 남으면 이전 테스트의 `speaker-test`/`aplay`를 종료.
- 시스템 시간이 올바르지 않으면 알람 시점도 틀어짐: `timedatectl` 확인. 입력 시각은 한국시간(Asia/Seoul).
