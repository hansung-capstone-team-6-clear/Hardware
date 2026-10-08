"""녹음 (I2S 마이크). 배선·설정·테스트: parts/audio/README.md

백엔드가 받는 형식: WAV, 16kHz, mono, 16bit, 최대 15초 (contracts § 1).
parts/audio에서 확인한 arecord 명령을 그대로 쓰면 된다.
"""


def start_recording() -> None:
    """녹음을 시작한다. 예: subprocess.Popen(["arecord", "-D", "plughw:0", "-c", "1", "-r", "16000",
    "-f", "S16_LE", "-d", "15", "/tmp/deskpet-voice.wav"])  — card 번호는 parts/audio 결과대로."""
    # TODO(hardware, 10/31)
    raise NotImplementedError


def stop_recording() -> bytes:
    """녹음을 멈추고 WAV 파일 내용을 bytes로 돌려준다. 15초가 지나 arecord가 먼저 끝났어도 동작해야 한다."""
    # TODO(hardware, 10/31)
    raise NotImplementedError
