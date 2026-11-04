
import wave
from pathlib import Path

import webrtcvad

AUDIO_DIR = Path.home() / "deskpet" / "test_audio"
VAD_MODE = 2
FRAME_MS = 30
MIN_SPEECH_MS = 300


def check_voice(path):
    with wave.open(str(path), "rb") as wav:
        sample_rate = wav.getframerate()
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        frames = wav.readframes(wav.getnframes())

    if sample_rate != 16000 or channels != 1 or sample_width != 2:
        raise ValueError(
            "WAV 형식 오류: 16kHz / 16bit / 모노가 필요합니다."
        )

    vad = webrtcvad.Vad(VAD_MODE)

    bytes_per_frame = (
        sample_rate * FRAME_MS // 1000
    ) * sample_width

    speech_frames = 0
    total_frames = 0

    for offset in range(0, len(frames), bytes_per_frame):
        frame = frames[offset:offset + bytes_per_frame]

        if len(frame) != bytes_per_frame:
            break

        total_frames += 1

        if vad.is_speech(frame, sample_rate):
            speech_frames += 1

    speech_ms = speech_frames * FRAME_MS
    speech_detected = speech_ms >= MIN_SPEECH_MS

    return speech_detected, speech_ms, total_frames


def main():
    files = sorted(AUDIO_DIR.rglob("*.wav"))

    if not files:
        print("[ERROR] WAV 파일이 없습니다.")
        return

    for path in files:
        print(f"\n===== {path.name} =====")

        try:
            detected, speech_ms, total = check_voice(path)

            print("검사 프레임:", total)
            print("음성 감지 시간:", speech_ms, "ms")

            if detected:
                print("[VAD] 말소리 감지")
                print("[NEXT] 백엔드 전송 가능")
            else:
                print("[VAD] 말소리 없음")
                print("[NOTICE] 다시 말해주세요")

        except (ValueError, wave.Error) as error:
            print("[ERROR]", error)


if __name__ == "__main__":
    main()
