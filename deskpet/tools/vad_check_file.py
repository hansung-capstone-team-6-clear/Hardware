
import sys
import wave
from pathlib import Path

import webrtcvad


# VAD 설정
SAMPLE_RATE = 16000
FRAME_MS = 30
VAD_MODE = 2

# 전체 프레임 중 음성으로 판정된 비율이 10% 이상이면 통과
MIN_SPEECH_RATIO = 0.10
MIN_SPEECH_FRAMES = 4

AUDIO_DIR = Path.home() / "deskpet" / "test_audio"


def check_voice(wav_path):
    print(f"\n========== VAD 검사 ==========")
    print("[FILE]", wav_path.name)

    if not wav_path.exists():
        print("[ERROR] 파일이 없습니다.")
        return False

    try:
        with wave.open(str(wav_path), "rb") as wf:
            channels = wf.getnchannels()
            rate = wf.getframerate()
            width = wf.getsampwidth()
            count = wf.getnframes()
            audio = wf.readframes(count)

        if channels != 1 or rate != SAMPLE_RATE or width != 2:
            print("[ERROR] 16kHz / 16bit / 모노 WAV가 아닙니다.")
            return False

        duration = count / rate

        vad = webrtcvad.Vad(VAD_MODE)

        bytes_per_frame = int(
            SAMPLE_RATE * FRAME_MS / 1000 * width
        )

        total_frames = 0
        speech_frames = 0

        for offset in range(0, len(audio), bytes_per_frame):
            frame = audio[offset:offset + bytes_per_frame]

            # 마지막 불완전 프레임은 제외
            if len(frame) != bytes_per_frame:
                break

            total_frames += 1

            if vad.is_speech(frame, SAMPLE_RATE):
                speech_frames += 1

        ratio = (
            speech_frames / total_frames
            if total_frames > 0 else 0
        )

        print(f"[DURATION] {duration:.2f}초")
        print(f"[TOTAL FRAMES] {total_frames}")
        print(f"[SPEECH FRAMES] {speech_frames}")
        print(f"[SPEECH RATIO] {ratio:.1%}")

        has_speech = (
            speech_frames >= MIN_SPEECH_FRAMES
            and ratio >= MIN_SPEECH_RATIO
        )

        if has_speech:
            print("[RESULT] 말소리 감지 → 백엔드 전송 가능")
        else:
            print("[RESULT] 무음 또는 말소리 부족")
            print("[LCD] 다시 말해주세요")

        return has_speech

    except (OSError, EOFError, wave.Error, ValueError) as error:
        print("[ERROR]", error)
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1]).expanduser()
    else:
        file_path = AUDIO_DIR / "desk-pet-voice-test.wav"

    check_voice(file_path)
