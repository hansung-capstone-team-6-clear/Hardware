# parts/voice_pipeline — 음성 전처리와 백엔드 통신

녹음된 WAV를 16kHz / 16bit / 모노로 맞추고, VAD로 말소리를 확인한 뒤 AWS FastAPI 백엔드로 보내 JSON 응답에 따라 상태를 전환한다.

버튼·마이크가 아직 연결되지 않아 **WAV 파일을 입력으로 쓴다.** LED·LCD 상태도 터미널 출력뿐이다. 담당 요구사항 1-5~1-8의 소프트웨어 부분이며, `app/`과는 아직 통합하지 않았다.

## 시스템 아키텍처

```text
버튼 → I2S 마이크 녹음                     (미구현, 현재는 WAV 파일 입력)
  → 오디오 형식 확인·변환 (FFmpeg)
  → VAD 음성 감지 ── 말소리 없음 → "다시 말해주세요", 전송 안 함
  → 요청 ID 생성 → POST /api/voice
  → 백엔드: STT + Gemini 명령 처리
  → JSON 응답 → 상태 전환 → LCD / LED / TTS  (현재는 터미널 출력)
```

## 파일

| 파일 | 역할 |
| --- | --- |
| `deskpet_voice_pipeline.py` | **메인.** 변환·VAD·전송·상태 전환 통합 |
| `audio_converter.py` | 오디오 변환 독립 테스트 |
| `vad_test.py` | VAD 독립 테스트 (`~/deskpet/test_audio` 아래 WAV 전체 검사) |
| `voice_client.py` | 초기 음성 전송 테스트 |
| `voice_client_v2.py` | 요청 ID 생성·전송 실험 |
| `voice_client_v3.py` | 상태 전환·Timeout 실험 (`ThreadPoolExecutor` 사용) |

## 개발 환경

- Raspberry Pi 4 Model B (RAM 8GB), 사용자 `clearpick`
- Python 3.9 이상 (`zoneinfo` 사용)
- 시스템 의존성: FFmpeg
- Python 의존성: `requests`, `webrtcvad-wheels` (`requirements.txt`, 버전 미고정)

## 설치

스크립트의 기본 경로가 `~/deskpet`으로 고정되어 있으므로 이 폴더의 파일을 그 위치에 둔다.

```bash
sudo apt install -y ffmpeg
mkdir -p ~/deskpet && cp parts/voice_pipeline/*.py parts/voice_pipeline/requirements.txt ~/deskpet/
cd ~/deskpet
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

테스트 WAV는 저장소에 없다. `~/deskpet/test_audio/`에 따로 넣는다.

## 환경변수

디바이스 토큰은 코드나 파일에 적지 않고 환경변수로만 전달한다. 실제 백엔드 전송에만 필요하고 `--dry-run`에는 필요 없다.

```bash
read -rs DESKPET_DEVICE_TOKEN && export DESKPET_DEVICE_TOKEN
```

## 실행

```bash
python3 deskpet_voice_pipeline.py                                   # 기본 WAV, 실제 전송
python3 deskpet_voice_pipeline.py test_audio/desk-pet-voice-test.wav
python3 deskpet_voice_pipeline.py test_audio/silence_test.wav --dry-run   # 전송 없이 전처리만
```

## 오디오 변환

입력이 16kHz / 16bit / 모노 / 비압축이면 변환을 생략하고, 아니면 FFmpeg로 변환한 뒤 형식을 다시 검사한다.

```bash
ffmpeg -i <입력> -vn -ar 16000 -ac 1 -c:a pcm_s16le -f wav <출력>
```

## VAD

`webrtcvad`로 30ms 프레임마다 판정하고, 음성 프레임 누적이 300ms 이상이면 말소리로 본다 (`VAD_MODE = 2`). 말소리가 없으면 백엔드로 보내지 않는다. 파이프라인은 15초를 넘는 오디오를 오류로 처리한다.

## 백엔드 연동

| 항목 | 값 |
| --- | --- |
| API | `POST /api/voice` (Multipart Form Data) |
| 주소 | 코드의 `BACKEND_URL` (개발용 EC2라 바뀔 수 있음) |
| 인증 | `x-device-token` 헤더 |
| 폼 필드 | `audio` (WAV), `request_id` |
| 요청 ID | `req_YYYYMMDD_HHMMSS_XXXX` (KST + uuid 4자리) |
| Timeout | 연결 3초, 읽기 10초 |

| 응답 `status` | 동작 |
| --- | --- |
| `OK` | THINKING → SPEAKING → IDLE |
| `NO_SPEECH` | "다시 말해주세요" 출력 → IDLE |
| 그 외, Timeout, 네트워크 오류 | ERROR → IDLE |

## 테스트 결과

**재확인 (2026-11-05, 백업 파일을 Windows에서 실행):** VAD 수치와 WAV 형식, 표의 `--dry-run` 2건

| 파일 | 감지된 음성 | 판정 |
| --- | ---: | --- |
| desk-pet-voice-ambiguous.wav | 990ms | 말소리 |
| desk-pet-voice-answer.wav | 1,620ms | 말소리 |
| desk-pet-voice-no-due.wav | 1,770ms | 말소리 |
| desk-pet-voice-no-name.wav | 3,030ms | 말소리 |
| desk-pet-voice-test.wav | 1,290ms | 말소리 (`--dry-run` 통과) |
| desk-pet-voice-tomorrow.wav | 1,560ms | 말소리 |
| desk-pet-voice-week.wav | 1,440ms | 말소리 |
| silence_test.wav | 0ms | 무음, 전송 차단 (`--dry-run` 통과) |

**Pi에서 실행한 기록 (개발 기록 기준, 이번에 재실행하지 않음):**

- 48kHz 스테레오 입력 → 16kHz 모노 변환 후 VAD 통과
- 실제 백엔드 요청 1건 `req_20261105_001410_5a7b`: 8.36초 만에 응답, 요청 ID 일치, `status: ERROR`, `stt_text: null`, THINKING → ERROR → IDLE 전환 확인

실제 소음 환경이나 여러 화자에 대한 VAD 정확도는 검증하지 않았다.

## 구현 현황

| 번호 | 요구사항 | 상태 |
| --- | --- | --- |
| 1-1 | GPIO17 버튼 입력·디바운싱 | 이 폴더에 미구현 (`parts/button` 참고) |
| 1-2 | 버튼 입력 후 100ms 이내 LED/LCD 반응 | 미구현 |
| 1-3 | I2S 마이크 녹음 시작 | 미구현 |
| 1-4 | 버튼 해제 또는 15초 경과 시 녹음 종료 | 미구현 |
| 1-5 | VAD 음성 감지·무음 처리 | 로컬 테스트 완료 |
| 1-6 | 16kHz / 16bit / 모노 변환 | 테스트 완료 |
| 1-7 | 요청 ID 생성·백엔드 전송 | 실제 통신 1건 확인 |
| 1-8 | THINKING / SPEAKING / ERROR / IDLE | 일부 검증 (ERROR 경로만) |

## 알려진 문제

- **백엔드 오류:** 위 요청이 `ERROR`로 끝났다. 처리 제한이 9초에서 7초로 줄어 Gemini 지연에 걸렸을 가능성이 있지만, 서버 로그를 보기 전에는 확정할 수 없다.
- **10초 제한:** 파이프라인의 `timeout=(3, 10)`은 연결과 읽기 제한이라 전체 시간을 10초로 보장하지 않는다.
- **중복 요청:** 클라이언트가 Timeout으로 끝나도 서버는 처리를 계속할 수 있어 중복 방지 정책을 백엔드와 협의해야 한다.
- **SPEAKING 미검증:** 통합 프로그램에서 `THINKING → SPEAKING → IDLE` 흐름은 실제로 확인하지 못했다.
- **HTTP 평문:** 백엔드 주소가 `http://`라 토큰과 음성이 암호화되지 않은 채 전송된다.

## 향후 계획

1. GPIO17 버튼 입력
2. I2S 마이크 녹음, 버튼 해제·15초 종료
3. LED·LCD 실제 연동
4. 녹음 결과를 이 파이프라인에 연결
5. 백엔드 지연 원인 확인
6. SPEAKING 검증과 TTS 재생
7. 전체 통합 테스트, `app/`으로 이전
