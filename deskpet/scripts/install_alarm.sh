#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -eq 0 ]]; then
  echo '일반 사용자(sudo 없이)로 실행하세요: bash install_alarm.sh (sudo 붙이지 않음)'
  exit 1
fi

PI_USER="$(id -un)"
PI_HOME="$HOME"
# 레포 위치 (이 스크립트의 상위 폴더). 데이터(SQLite·음성)는 DESKPET_HOME(기본 ~/deskpet)에 저장된다.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="${DESKPET_HOME:-$PI_HOME/deskpet}"
VENV_PY="$REPO/.venv/bin/python"
AUDIO_DEV="${DESKPET_AUDIO_DEVICE:-plughw:2,0}"

if [[ ! -f "$REPO/src/deskpet_alarm.py" ]]; then
  echo "파일이 없습니다: $REPO/src/deskpet_alarm.py"
  exit 1
fi
if [[ ! -x "$VENV_PY" ]]; then
  echo "파이썬 가상환경이 없습니다: $VENV_PY"
  exit 1
fi

mkdir -p "$DATA/reminder_audio"

sudo tee /etc/systemd/system/deskpet-alarm.service > /dev/null <<EOF
[Unit]
Description=DeskPet deadline reminder (1 hour before)
After=sound.target

[Service]
Type=simple
User=$PI_USER
WorkingDirectory=$REPO
Environment=HOME=$PI_HOME
Environment=DESKPET_HOME=$DATA
Environment=DESKPET_AUDIO_DEVICE=$AUDIO_DEV
ExecStart=$VENV_PY -u $REPO/src/deskpet_alarm.py run
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now deskpet-alarm.service
sudo systemctl --no-pager --full status deskpet-alarm.service || true

echo
printf '%s\n' "설치 완료. 저장 목록: $VENV_PY $REPO/src/deskpet_alarm.py list" \
  "즉시 소리 시험: $VENV_PY $REPO/src/deskpet_alarm.py test" \
  '서비스 로그: sudo journalctl -u deskpet-alarm -n 40 --no-pager'
