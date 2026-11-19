
import os
import uuid
import json
import time
import threading
import requests

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

# ==========================================
# 1. 기본 설정
# ==========================================

BACKEND_URL = os.environ.get("DESKPET_BACKEND_URL", "").rstrip("/") + "/api/voice"

WAV_PATH = (
    Path.home()
    / "deskpet"
    / "test_audio"
    / "desk-pet-voice-test.wav"
)

TIMEOUT_SECONDS = 10

# 상태 정의
IDLE = "IDLE"
THINKING = "THINKING"
SPEAKING = "SPEAKING"
ERROR = "ERROR"

current_state = IDLE


# ==========================================
# 2. 요청 ID 생성
# ==========================================

def generate_request_id():
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    random_part = uuid.uuid4().hex[:4]

    return f"req_{timestamp}_{random_part}"


# ==========================================
# 3. 상태 변경
# ==========================================

def set_state(state):
    global current_state

    current_state = state

    if state == IDLE:
        print("\n[STATE] IDLE")
        print("[LED] 초록색 켜짐")
        print("[LCD] idle")

    elif state == THINKING:
        print("\n[STATE] THINKING")
        print("[LED] 흰색 점멸")
        print("[LCD] 생각 중...")

    elif state == SPEAKING:
        print("\n[STATE] SPEAKING")
        print("[LED] 파란색 점멸")
        print("[LCD] 말하는 중...")

    elif state == ERROR:
        print("\n[STATE] ERROR")
        print("[LED] 빨간색 점멸")
        print("[LCD] 오류 발생")


# ==========================================
# 4. 백엔드 음성 전송
# ==========================================

def upload_voice(request_id, token):
    with WAV_PATH.open("rb") as audio:
        response = requests.post(
            BACKEND_URL,
            headers={"x-device-token": token},
            files={
                "audio": (
                    WAV_PATH.name,
                    audio,
                    "audio/wav"
                )
            },
            data={"request_id": request_id},
            timeout=(3, 9)
        )

    response.raise_for_status()
    return response.json()


# ==========================================
# 5. 음성 요청 및 응답 대기
# ==========================================

def send_voice():
    token = os.environ.get("DESKPET_DEVICE_TOKEN")

    if not token:
        print("[ERROR] 디바이스 토큰이 없습니다.")
        return

    if not WAV_PATH.exists():
        print("[ERROR] WAV 파일이 없습니다.")
        return

    request_id = generate_request_id()

    print("\n========== 음성 요청 ==========")
    print("[Pi 요청 ID]", request_id)
    print("[AUDIO]", WAV_PATH.name)

    set_state(THINKING)

    start_time = time.monotonic()

    # 요청을 별도 스레드에서 수행
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(upload_voice, request_id, token)

    try:
        result = future.result(timeout=TIMEOUT_SECONDS)

        elapsed = time.monotonic() - start_time

        print(f"\n[RESPONSE TIME] {elapsed:.2f}초")
        print("\n========== 백엔드 응답 ==========")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        server_id = result.get("request_id")

        if server_id != request_id:
            print("[WARNING] Pi/서버 요청 ID 불일치")
            print("백엔드 인터페이스 수정 대기 중")

        status = result.get("status")

        if status == "OK":
            set_state(SPEAKING)

            output = result.get("output") or {}

            print("[STT]", result.get("stt_text"))
            print("[TTS]", output.get("tts"))
            print("[LCD RESPONSE]", output.get("lcd"))

        elif status == "NO_SPEECH":
            print("[NOTICE] 다시 말해주세요")

        else:
            set_state(ERROR)
            print("[ERROR STATUS]", status)

    except FutureTimeout:
        print("\n[TIMEOUT] 10초 초과")
        set_state(ERROR)
        print("[NOTICE] 서버 응답이 늦어지고 있어요.")

    except requests.exceptions.RequestException as e:
        set_state(ERROR)
        print("[NETWORK ERROR]", e)

    except (OSError, ValueError) as e:
        set_state(ERROR)
        print("[ERROR]", e)

    finally:
        # 실행 중인 네트워크 작업을 기다리지 않음
        executor.shutdown(wait=False, cancel_futures=True)
        set_state(IDLE)


# ==========================================
# 6. 프로그램 시작
# ==========================================

if __name__ == "__main__":
    set_state(IDLE)
    send_voice()
