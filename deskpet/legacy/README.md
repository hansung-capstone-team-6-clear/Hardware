# legacy/ — 구버전 코드 (보존용)

기능을 지우지 않기 위해 원본을 그대로 남겨 둔 폴더다. 하드코딩된 서버 주소만 환경변수(`DESKPET_BACKEND_URL`)로 바꿨다.
새 작업은 `src/`에서 한다.

| 파일 | 대체한 파일 | 차이 |
|---|---|---|
| `deskpet_backend_voice.py` | `src/deskpet_voice.py` | 알람 연동(`register_from_backend`)과 오디오 잠금이 없는 이전 버전 |
| `voice_client.py` | `tools/voice_file_client.py` | `user_id`·`request_id`를 보내지 않는 첫 버전 |
| `voice_client_v3.py` | `tools/voice_file_pipeline.py` | 스레드로 10초 타임아웃을 거는 버전. 상태 출력은 print만 함 |
| `test_timeout.py` | — | **동작하지 않음.** `voice_client_v3`에 없는 `change_state`, `DeadlineExceeded`, `timeout_handler`를 import한다. 더 새로운 v3에서 쓰던 코드로 추정되지만 그 파일은 ZIP에 없다 |
