
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
from deskpet_env import backend_url, device_token  # noqa: E402  (.env 로드)
import argparse
import json
import os
import subprocess
import time
import uuid
import wave
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import webrtcvad


BASE_DIR = Path.home() / "deskpet"
DEFAULT_AUDIO = BASE_DIR / "test_audio/desk-pet-voice-test.wav"
OUTPUT_AUDIO = BASE_DIR / "test_audio/pipeline_voice.wav"

BACKEND_URL = backend_url() + "/api/voice"

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2
CHANNELS = 1
MAX_RECORDING_SECONDS = 15

VAD_MODE = 2
FRAME_MS = 30
MIN_SPEECH_MS = 300

CONNECT_TIMEOUT = 3
READ_TIMEOUT = 10

IDLE = "IDLE"
THINKING = "THINKING"
SPEAKING = "SPEAKING"
ERROR = "ERROR"


def set_state(state):
    print(f"\n[STATE] {state}")

    if state == IDLE:
        print("[LED] 초록색")
        print("[LCD] idle")

    elif state == THINKING:
        print("[LED] 흰색 점멸")
        print("[LCD] 생각 중...")

    elif state == SPEAKING:
        print("[LED] 파란색 점멸")
        print("[LCD] 말하는 중...")

    elif state == ERROR:
        print("[LED] 빨간색 점멸")
        print("[LCD] 오류 발생")


def make_request_id():
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    return (
        f"req_{now.strftime('%Y%m%d_%H%M%S')}_"
        f"{uuid.uuid4().hex[:4]}"
    )


def is_correct_format(path):
    try:
        with wave.open(str(path), "rb") as wav:
            return (
                wav.getframerate() == SAMPLE_RATE
                and wav.getnchannels() == CHANNELS
                and wav.getsampwidth() == SAMPLE_WIDTH
                and wav.getcomptype() == "NONE"
            )
    except (wave.Error, EOFError):
        return False


def convert_if_needed(input_path):
    print("\n[STEP 1] 오디오 형식 확인")

    if is_correct_format(input_path):
        print("[AUDIO] 이미 16kHz / 16bit / 모노입니다.")
        print("[AUDIO] 변환 생략")
        return input_path

    print("[AUDIO] 형식이 달라 변환합니다.")

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", str(input_path),
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        "-f", "wav",
        str(OUTPUT_AUDIO),
    ]

    subprocess.run(command, check=True, timeout=30)

    if not is_correct_format(OUTPUT_AUDIO):
        raise ValueError("변환 후 WAV 형식이 올바르지 않습니다.")

    print("[AUDIO] 변환 완료")
    return OUTPUT_AUDIO


def detect_speech(path):
    print("\n[STEP 2] VAD 검사")

    with wave.open(str(path), "rb") as wav:
        sample_rate = wav.getframerate()
        duration = wav.getnframes() / sample_rate

        if duration <= 0 or duration > MAX_RECORDING_SECONDS:
            raise ValueError(
                f"오디오 길이 오류: {duration:.2f}초"
            )

        audio_bytes = wav.readframes(wav.getnframes())

    vad = webrtcvad.Vad(VAD_MODE)

    frame_bytes = (
        SAMPLE_RATE * FRAME_MS // 1000
    ) * SAMPLE_WIDTH

    speech_frames = 0

    for offset in range(0, len(audio_bytes), frame_bytes):
        frame = audio_bytes[offset:offset + frame_bytes]

        if len(frame) != frame_bytes:
            break

        if vad.is_speech(frame, SAMPLE_RATE):
            speech_frames += 1

    speech_ms = speech_frames * FRAME_MS

    print(f"[AUDIO] 재생 시간: {duration:.2f}초")
    print(f"[VAD] 감지된 음성: {speech_ms}ms")

    if speech_ms < MIN_SPEECH_MS:
        print("[VAD] 말소리 없음")
        return False

    print("[VAD] 말소리 감지")
    return True


def send_to_backend(path, request_id, token):
    print("\n[STEP 3] 백엔드 전송")

    with path.open("rb") as audio:
        response = requests.post(
            BACKEND_URL,
            headers={"x-device-token": token},
            files={
                "audio": (
                    path.name,
                    audio,
                    "audio/wav",
                )
            },
            data={"request_id": request_id},
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )

    response.raise_for_status()
    return response.json()


def run_pipeline(audio_path, dry_run=False):
    set_state(IDLE)

    try:
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)

        converted_path = convert_if_needed(audio_path)

        if not detect_speech(converted_path):
            print("\n[NOTICE] 다시 말해주세요")
            print("[BACKEND] 전송하지 않음")
            return

        request_id = make_request_id()

        print("\n[REQUEST ID]", request_id)

        if dry_run:
            print("[DRY RUN] 백엔드 전송 생략")
            print("[RESULT] 음성 전처리 성공")
            return

        token = device_token()

        if not token:
            raise ValueError(
                "DESKPET_DEVICE_TOKEN 환경변수가 없습니다."
            )

        set_state(THINKING)
        start = time.monotonic()

        result = send_to_backend(
            converted_path,
            request_id,
            token,
        )

        elapsed = time.monotonic() - start

        print(f"\n[RESPONSE TIME] {elapsed:.2f}초")
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

        backend_id = result.get("request_id")

        if backend_id != request_id:
            print(
                "[WARNING] Pi 요청 ID와 "
                "백엔드 응답 ID가 다릅니다."
            )

        status = result.get("status")

        if status == "OK":
            set_state(SPEAKING)

            output = result.get("output") or {}
            lcd = output.get("lcd") or {}

            print("[STT]", result.get("stt_text"))
            print("[TTS]", output.get("tts"))
            print("[LCD TEXT]", lcd.get("text"))

            print("[NOTICE] 실제 TTS 재생은 아직 미연동")

        elif status == "NO_SPEECH":
            print("[NOTICE] 다시 말해주세요")

        else:
            set_state(ERROR)
            print("[BACKEND STATUS]", status)

    except requests.exceptions.Timeout:
        set_state(ERROR)
        print("[TIMEOUT] 백엔드 응답 지연")

    except requests.exceptions.RequestException as error:
        set_state(ERROR)
        print("[NETWORK ERROR]", error)

    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        wave.Error,
    ) as error:
        set_state(ERROR)
        print("[ERROR]", error)

    finally:
        set_state(IDLE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "audio",
        nargs="?",
        type=Path,
        default=DEFAULT_AUDIO,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="백엔드 전송 없이 전처리만 검사",
    )

    args = parser.parse_args()

    run_pipeline(args.audio, args.dry_run)
