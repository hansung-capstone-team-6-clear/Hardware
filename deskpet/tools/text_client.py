
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
from deskpet_env import backend_url, device_token  # noqa: E402  (.env 로드)
import os
import json
import uuid
import requests

BACKEND_URL = backend_url()
DEVICE_TOKEN = device_token()

def send_text(text):
    if not DEVICE_TOKEN:
        print("DEVICE_TOKEN이 설정되지 않았습니다.")
        return

    local_request_id = str(uuid.uuid4())

    print(f"[요청 생성] {local_request_id}")
    print("[LCD] 생각 중...")

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/text",
            headers={
                "x-device-token": DEVICE_TOKEN
            },
            json={"text": text},
            timeout=10
        )
        response.raise_for_status()

        result = response.json()

        print("\n[백엔드 응답]")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        output = result.get("output") or {}
        lcd = output.get("lcd") or {}

        print("\n[TTS]", output.get("tts", ""))
        print("[LCD 표정]", lcd.get("expression", "idle"))
        print("[LCD 문구]", lcd.get("text", ""))

    except requests.Timeout:
        print("[Timeout] 백엔드 응답 시간이 초과되었습니다.")
        print("[LCD] 오류 발생")

    except requests.RequestException as e:
        print("[통신 오류]", e)
        print("[LCD] 연결 오류")

if __name__ == "__main__":
    message = input("Desk Pet에게 말할 내용: ")
    send_text(message)

