# parts/audio — 마이크 + 앰프 + 스피커

마이크(ICS-43434)와 앰프(MAX98357A)는 I2S 클럭선(BCLK, LRCLK)을 **같이 쓴다**. 그래서 둘을 한 폴더에서 같이 테스트한다.

## 배선

| 부품 | 핀 | Pi (GPIO / 물리 핀) |
| --- | --- | --- |
| 마이크 | VCC / GND | 3.3V (1) / GND (9) |
| 마이크 | SCK / WS / SD | GPIO18 (12) / GPIO19 (35) / GPIO20 (38) |
| 마이크 | L/R | GND (왼쪽 채널) — 모듈에 핀이 있을 때 |
| 앰프 | Vin / GND | 5V (2) / GND (6) |
| 앰프 | BCLK / LRC / DIN | GPIO18 (12) / GPIO19 (35) / GPIO21 (40) |
| 앰프 → 스피커 | + / − | 스피커 두 선 |

## 설정

`../../setup/README.md` § 3의 `config.txt`를 적용하고 재부팅한다. 핵심 줄:

```ini
dtparam=audio=off
dtoverlay=googlevoicehat-soundcard
```

`googlevoicehat-soundcard`는 Google AIY Voice HAT(MEMS 마이크 + MAX98357A 조합)용 overlay다.
이 조합에서 녹음·재생이 둘 다 되는지는 **아직 확인하지 않았다** — 이 폴더의 첫 번째 일이다.

## 테스트

```bash
arecord -l    # 녹음 장치 목록 — card 번호 확인
aplay -l      # 재생 장치 목록

# card 번호가 0이면 plughw:0 (다르면 숫자만 바꾼다)
arecord -D plughw:0 -c 1 -r 16000 -f S16_LE -d 5 test.wav   # 5초 녹음 (백엔드가 받는 형식)
aplay -D plughw:0 test.wav                                   # 재생
```

TTS 재생도 확인한다 (인터넷 필요, `app/` 가상환경에서):

```bash
edge-tts --voice ko-KR-SunHiNeural --text "안녕하세요, 데스크펫이에요." --write-media hello.mp3
mpg123 hello.mp3
```

## 완료 기준

- [ ] `arecord -l`, `aplay -l`에 같은 I2S 카드가 보인다
- [ ] 5초 녹음한 내 목소리가 스피커로 알아들을 수 있게 들린다
- [ ] `hello.mp3`가 스피커로 들린다
- [ ] 녹음이 너무 작으면 `alsamixer`로 조정한 값을 아래에 기록했다

## Plan B — overlay가 끝내 안 될 때

USB 마이크 + USB 스피커(또는 USB 사운드카드)를 쓴다. 드라이버 없이 `arecord -l`에 바로 잡힌다.
이 경우 I2S 배선과 `dtoverlay` 줄을 빼고, 결정 내용을 아래 결과 기록에 남긴다.

## 결과 기록

| 날짜 | 시도한 것 | 결과 | 메모 |
| --- | --- | --- | --- |
| | | | |
