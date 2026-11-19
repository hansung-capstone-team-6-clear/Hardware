
import subprocess
import wave
from pathlib import Path

# 기본 경로
BASE_DIR = Path.home() / "deskpet"
INPUT_FILE = BASE_DIR / "test_audio/input_48k_stereo.wav"
OUTPUT_FILE = BASE_DIR / "test_audio/converted_voice.wav"

# 백엔드 요구사항
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2


def convert_audio(input_path, output_path):
    """음성을 16kHz / 16bit / 모노 WAV로 변환"""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", str(input_path),
        "-vn",
        "-ar", str(SAMPLE_RATE),
        "-ac", str(CHANNELS),
        "-c:a", "pcm_s16le",
        "-f", "wav",
        str(output_path)
    ]

    print("[CONVERT] 오디오 변환 시작")

    try:
        subprocess.run(
            command,
            check=True,
            timeout=30
        )
    except FileNotFoundError:
        print("[ERROR] FFmpeg를 찾을 수 없습니다.")
        return False
    except subprocess.TimeoutExpired:
        print("[ERROR] 변환 시간 초과")
        return False
    except subprocess.CalledProcessError as error:
        print("[ERROR] FFmpeg 변환 실패:", error)
        return False

    print("[CONVERT] 변환 완료")
    return True


def verify_audio(path):
    """변환된 WAV 파일 규격 검사"""

    with wave.open(str(path), "rb") as wav:
        sample_rate = wav.getframerate()
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        duration = wav.getnframes() / sample_rate

    print("\n========== WAV 검사 ==========")
    print("샘플레이트:", sample_rate, "Hz")
    print("채널:", channels)
    print("비트 깊이:", sample_width * 8, "bit")
    print("재생 시간:", round(duration, 2), "초")

    valid = (
        sample_rate == SAMPLE_RATE
        and channels == CHANNELS
        and sample_width == SAMPLE_WIDTH
        and 0 < duration <= 15
    )

    print("[RESULT]", "PASS" if valid else "FAIL")
    return valid


if __name__ == "__main__":
    if convert_audio(INPUT_FILE, OUTPUT_FILE):
        verify_audio(OUTPUT_FILE)
