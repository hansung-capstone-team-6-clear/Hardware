
import os
import uuid
import json
import requests

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


# ==================================
# 1. 기본 설정
# ==================================

BACKEND_URL = "http://3.104.122.146:8000/api/voice"

WAV_PATH = (
    Path.home()
    / "deskpet"
    / "test_audio"
    / "desk-pet-voice-test.wav"
)

# 팀 백엔드 테스트 사용자 ID (확인 필요)
USER_ID = "test-user"

TIMEOUT = 10


# ==================================
# 2. 요청 ID 생성
# ==================================

def generate_request_id():
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    random_part = uuid.uuid4().hex[:4]

    return f"req_{timestamp}_{random_part}"


# ==================================
# 3. 음성 파일 전송
# ==================================

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
    print("[USER ID]", USER_ID)
    print("[AUDIO]", WAV_PATH.name)
    print("[LCD] 생각 중...")

    try:
        with WAV_PATH.open("rb") as audio:
            response = requests.post(
                BACKEND_URL,
                headers={
                    "x-device-token": token
                },
                files={
                    "audio": (
                        WAV_PATH.name,
                        audio,
                        "audio/wav"
                    )
                },
                data={
                    "user_id": USER_ID,
                    "request_id": request_id
                },
                timeout=TIMEOUT
            )

        response.raise_for_status()
        result = response.json()

        print("\n========== 백엔드 응답 ==========")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 요청 ID 비교
        server_request_id = result.get("request_id")

        print("\n[Pi 요청 ID]", request_id)
        print("[서버 요청 ID]", server_request_id)

        if request_id == server_request_id:
            print("[SUCCESS] 요청 ID 일치")
        else:
            print("[WARNING] 요청 ID 불일치")
            print("백엔드 request_id 처리 확인 필요")

        # 음성 처리 결과
        status = result.get("status")
        output = result.get("output") or {}

        print("\n[STATUS]", status)
        print("[STT]", result.get("stt_text"))
        print("[TYPE]", result.get("type"))
        print("[TTS]", output.get("tts"))
        print("[LCD]", output.get("lcd"))

        if status == "NO_SPEECH":
            print("[NOTICE] 다시 말해주세요")

        elif status in ("STT_ERROR", "ERROR"):
            print("[ERROR] 음성 처리 실패")

    except requests.exceptions.Timeout:
        print("[TIMEOUT] 백엔드 응답 대기 시간 초과")

    except requests.exceptions.HTTPError as error:
        print("[HTTP ERROR]", error)
        if error.response is not None:
            print("[RESPONSE]", error.response.text[:500])

    except requests.exceptions.RequestException as error:
        print("[NETWORK ERROR]", error)

    except (OSError, ValueError) as error:
        print("[ERROR] 파일 또는 응답 처리 오류:", error)


# ==================================
# 4. 프로그램 실행
# ==================================

if __name__ == "__main__":
    send_voice()
