# setup/ — Raspberry Pi 처음 준비하기

Pi 한 대를 "app/을 실행할 수 있는 상태"로 만드는 순서다. 한 번만 하면 된다. 끝나면 `../parts/`로 간다.

## 1. OS 설치 (PC에서)

1. Raspberry Pi Imager로 **Raspberry Pi OS (64-bit, Bookworm)**를 microSD에 굽는다.
2. Imager의 설정(톱니바퀴)에서 미리 지정한다: 호스트 이름(예: `deskpet`), 사용자·비밀번호, Wi-Fi, **SSH 사용**.
3. Pi에 꽂고 전원을 켠 뒤 같은 Wi-Fi의 PC에서 접속한다.

```bash
ssh <사용자>@deskpet.local
```

학교 Wi-Fi가 웹 로그인이나 기업용 인증(아이디·비밀번호 입력)을 요구하면 Pi가 붙지 못할 수 있다.
그때는 휴대폰 핫스팟에 Pi와 백엔드 노트북을 같이 붙인다 (시연 때도 같은 방법).

## 2. 패키지 설치 (Pi에서)

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git python3-venv mpg123 fonts-nanum
```

| 패키지 | 쓰는 곳 |
| --- | --- |
| `git` | 레포 클론 |
| `python3-venv` | 파이썬 가상환경 |
| `mpg123` | TTS(mp3) 재생 |
| `fonts-nanum` | LCD에 한글 표시 |

## 3. 하드웨어 설정 (`config.txt`)

Bookworm은 `/boot/firmware/config.txt`, 이전 OS는 `/boot/config.txt`를 연다.

```bash
sudo nano /boot/firmware/config.txt
```

맨 아래에 추가하고 재부팅한다 (`sudo reboot`):

```ini
# desk-pet
dtparam=spi=on                        # LCD (ST7789, SPI)
dtparam=audio=off                     # 온보드 오디오 끄기 — LED(PWM)와 충돌 방지
dtoverlay=googlevoicehat-soundcard    # I2S 마이크+앰프 (후보, parts/audio에서 검증)
```

이미 `dtparam=audio=on` 줄이 있으면 그 줄을 지운다. 오디오 overlay가 안 맞으면 `../parts/audio/README.md`의 Plan B를 본다.

## 4. 레포와 파이썬 환경

```bash
git clone https://github.com/hansung-capstone-team-6-clear/Hardware.git
cd Hardware/app
python3 -m venv --system-site-packages .venv   # Pi OS에 기본 설치된 gpiozero를 같이 쓰려고
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                            # BACKEND_URL, DEVICE_TOKEN 채우기
```

## 완료 기준

- [ ] PC에서 `ssh`로 접속된다
- [ ] `arecord -l`과 `aplay -l`에 I2S 사운드카드가 보인다 (재부팅 후)
- [ ] `ls /dev/spidev0.0`이 있다
- [ ] `app/` 가상환경에서 `pip install -r requirements.txt`가 끝난다
