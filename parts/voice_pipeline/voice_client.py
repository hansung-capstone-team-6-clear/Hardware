
import os
import json
import requests

BACKEND_URL = "http://3.104.122.146:8000/api/voice"
WAV_PATH = "test_audio/desk-pet-voice-test.wav"


def send_voice():
    token = os.environ.get("DESKPET_DEVICE_TOKEN")

    if not token:
        print("오류: 디바이스 토큰이 설정되지 않았습니다.")
        return

    print("[LCD] 생각 중...")
    print("[VOICE] 백엔드 전송 시작")

    try:
        with open(WAV_PATH, "rb") as audio:
            response = requests.post(
                BACKEND_URL,
                headers={"x-device-token": token},
                files={"audio": ("voice.wav", audio, "audio/wav")},
                timeout=10
            )

        response.raise_for_status()
        result = response.json()

        print("\n=== 백엔드 응답 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        status = result.get("status")

        if status == "OK":
            print("\n[STT]", result.get("stt_text"))
            output = result.get("output") or {}
            print("[TTS]", output.get("tts"))
            print("[LCD]", output.get("lcd"))

        elif status == "NO_SPEECH":
            print("[LCD] 다시 말해주세요")

        else:
            print("[ERROR] 처리 실패:", status)

    except requests.exceptions.Timeout:
        print("[TIMEOUT] 백엔드 응답 시간 초과")

    except requests.exceptions.RequestException as e:
        print("[ERROR] 통신 오류:", e)

    except (OSError, ValueError) as e:
        print("[ERROR] 파일 또는 응답 오류:", e)


if __name__ == "__main__":
    send_voice()
