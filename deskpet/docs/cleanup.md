# 정리 내역 (원본 ZIP → 이 레포)

## 파일 위치 변경

| 원본 | 새 위치 | 분류 |
|---|---|---|
| deskpet_backend_voice_alarm.py | src/deskpet_voice.py | 실행 (최신 버전) |
| deskpet_alarm.py | src/deskpet_alarm.py | 실행 |
| install_alarm.sh | scripts/install_alarm.sh | 설치 |
| faces/*.png, faces/README.md | assets/faces/ | 에셋 |
| README_deskpet_alarm_KO.md | docs/alarm_original_notes.md | 문서 (원본 보존) |
| deskpet_record_play.py | tests/hardware/record_play.py | 하드웨어 테스트 |
| button_face_beep.py, lcd_test.py, lcd_face_test.py, lcd_faces_cycle.py, speaker_loop.py, tts_loop.py | tests/hardware/ (이름 그대로) | 하드웨어 테스트 |
| test_lcd_speaker.py | tests/hardware/lcd_speaker_together.py | 하드웨어 테스트 (pytest가 실수로 수집하지 않게 이름 변경) |
| deskpet_voice_pipeline.py | tools/voice_file_pipeline.py | 개발 도구 |
| voice_client_v2.py | tools/voice_file_client.py | 개발 도구 |
| deskpet_client.py | tools/text_client.py | 개발 도구 |
| audio_converter.py | tools/audio_converter.py | 개발 도구 |
| test_vad.py / vad_test.py | tools/vad_check_file.py / tools/vad_check_folder.py | 개발 도구 (판정 기준이 달라서 둘 다 보존: 비율 10% / 300ms) |
| deskpet_backend_voice.py, voice_client.py, voice_client_v3.py, test_timeout.py | legacy/ | 구버전 (legacy/README.md) |
| (새 파일) | src/deskpet_env.py, tests/unit/test_alarm.py, README.md, .env.example, .gitignore, requirements.txt | |

## 코드 수정 (동작은 그대로 두는 최소 수정)

1. 하드코딩된 백엔드 IP를 **모든 파일에서 제거**했다. 이제 `DESKPET_BACKEND_URL`에서만 읽는다.
2. `/home/<사용자>` 절대경로를 `Path.home()`으로 바꿨다. 설치 스크립트 메시지에 있던 사용자 이름도 지웠다.
3. 표정 이미지 경로를 `~/deskpet/faces`에서 레포의 `assets/faces`로 바꿨다. `DESKPET_FACES_DIR`로 다른 경로를 지정할 수 있다.
4. 오디오 장치, 버튼 GPIO, 녹음 시간, HTTP 타임아웃, TTS 음성을 환경변수로 뺐다. **기본값은 원본 값 그대로**다.
5. `deskpet_alarm.py`: `fcntl` import를 선택 사항으로 바꿨다 (Windows에서 단위 테스트하려고). 데이터 경로를 `DESKPET_HOME`으로 지정할 수 있게 했다. 3600초를 `ALERT_BEFORE_SEC` 상수로 뺐다.
6. `install_alarm.sh`: `~/deskpet/deskpet_alarm.py` 고정 경로 대신 레포 위치를 기준으로 실행하고, `DESKPET_HOME`을 서비스에 넘긴다.
7. 토큰 환경변수 이름을 `DESKPET_DEVICE_TOKEN`으로 통일했다. 예전 이름 `DEVICE_TOKEN`도 계속 읽는다.

## 원본에서 발견한 문제 (고치지 않고 기록만 함)

- `test_timeout.py`가 `voice_client_v3`에 없는 이름을 import해서 실행되지 않는다 → legacy로 옮겼다.
- 메인 앱의 응답 타임아웃이 90초다. 팀 정책(10초)과 다르다 → `.env`로 바꿀 수 있게만 했다.
- 메인 앱의 녹음 종료 처리 코드가 두 곳에 중복되어 있다 (버튼 뗌 / 15초 초과). 동작에 영향이 없어서 그대로 뒀다.
