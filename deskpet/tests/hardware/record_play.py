#!/usr/bin/env python3

import signal
import subprocess
import time
import wave
from pathlib import Path

import board
import digitalio
import gpiod

from gpiod.line import Bias, Direction, Value
from PIL import Image, ImageDraw, ImageFont, ImageOps
from adafruit_rgb_display import st7789


# ==========================================
# 1. 기본 설정
# ==========================================

BASE = Path.home() / "deskpet"
FACES = Path(__file__).resolve().parents[2] / "assets" / "faces"
OUTPUT = BASE / "test_audio"

OUTPUT.mkdir(parents=True, exist_ok=True)

RAW_WAV = OUTPUT / "button_record_raw.wav"
PLAY_WAV = OUTPUT / "button_record_play.wav"

AUDIO_DEVICE = "plughw:2,0"

BUTTON_GPIO = 17

MAX_RECORD_SEC = 15
DEBOUNCE_SEC = 0.04


# ==========================================
# 2. LCD 초기화
# ==========================================

spi = board.SPI()

cs = digitalio.DigitalInOut(board.D5)
dc = digitalio.DigitalInOut(board.D24)
rst = digitalio.DigitalInOut(board.D25)

backlight = digitalio.DigitalInOut(board.D23)
backlight.direction = digitalio.Direction.OUTPUT
backlight.value = True

display = st7789.ST7789(
    spi,
    cs=cs,
    dc=dc,
    rst=rst,
    width=240,
    height=280,
    x_offset=0,
    y_offset=20,
    rotation=90,
    baudrate=16000000,
)


# ==========================================
# 3. LCD 표정 이미지 준비
# ==========================================

# LCD가 90도 회전하므로 이미지 크기는 280x240
IMAGE_SIZE = (display.height, display.width)

face_images = {}

for state in (
    "idle",
    "listening",
    "thinking",
    "speaking",
):

    face_path = FACES / f"{state}.png"

    if face_path.is_file():

        with Image.open(face_path) as source:

            face_images[state] = ImageOps.fit(
                source.convert("RGB"),
                IMAGE_SIZE,
            )

    else:
        # 표정 이미지가 없으면 글자로 상태 표시
        img = Image.new(
            "RGB",
            IMAGE_SIZE,
            "white",
        )

        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                27,
            )
        except OSError:
            font = ImageFont.load_default()

        text = state.upper()

        box = draw.textbbox(
            (0, 0),
            text,
            font=font,
        )

        x = (
            IMAGE_SIZE[0] - (box[2] - box[0])
        ) // 2

        y = (
            IMAGE_SIZE[1] - (box[3] - box[1])
        ) // 2

        draw.text(
            (x, y),
            text,
            font=font,
            fill="black",
        )

        face_images[state] = img

        print(f"이미지 없음: {face_path}")
        print("대신 글자로 표시합니다.")


def show_face(state):

    display.image(face_images[state])

    print(
        f"LCD: {state.upper()}",
        flush=True,
    )


# ==========================================
# 4. 마이크 녹음 시작
# ==========================================

def start_recording():

    print("버튼 눌림: 녹음 시작")

    show_face("listening")

    return subprocess.Popen(
        [
            "arecord",
            "-q",
            "-D", AUDIO_DEVICE,
            "-f", "S32_LE",
            "-r", "48000",
            "-c", "2",
            "-t", "wav",
            "-d", str(MAX_RECORD_SEC),
            str(RAW_WAV),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


# ==========================================
# 5. 마이크 녹음 종료
# ==========================================

def stop_recording(proc):

    if proc.poll() is None:

        proc.send_signal(signal.SIGINT)

    try:

        _, errors = proc.communicate(timeout=3)

    except subprocess.TimeoutExpired:

        proc.terminate()

        try:
            _, errors = proc.communicate(timeout=2)

        except subprocess.TimeoutExpired:

            proc.kill()
            _, errors = proc.communicate()

    if errors and proc.returncode not in (
        0,
        -signal.SIGINT,
        130,
    ):
        print(
            "녹음 장치 메시지:",
            errors.strip(),
        )


# ==========================================
# 6. 녹음한 음성 재생
# ==========================================

def play_recorded():

    # 녹음 파일 확인
    try:

        with wave.open(str(RAW_WAV), "rb") as recorded:

            frames = recorded.getnframes()

            sample_rate = recorded.getframerate()

        if frames / sample_rate < 0.3:

            print("녹음이 너무 짧습니다.")
            return

    except (
        OSError,
        EOFError,
        wave.Error,
        ZeroDivisionError,
    ) as exc:

        print("녹음 파일 오류:", exc)
        return

    # 마이크의 좌우 채널을 하나로 합친 뒤
    # 스피커용 48kHz / 16bit / 스테레오로 변환

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", str(RAW_WAV),
        "-af", "pan=mono|c0=c0+c1,volume=0.7",
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        str(PLAY_WAV),
    ]

    try:

        subprocess.run(
            cmd,
            check=True,
        )

    except subprocess.CalledProcessError:

        print("오디오 변환 실패")
        return

    print("녹음한 목소리 재생!")

    show_face("speaking")

    try:

        subprocess.run(
            [
                "aplay",
                "-q",
                "-D", AUDIO_DEVICE,
                str(PLAY_WAV),
            ],
            check=True,
        )

    except subprocess.CalledProcessError as exc:

        print("스피커 재생 오류:", exc)


# ==========================================
# 7. 버튼 + LCD + 마이크 + 스피커 통합
# ==========================================

def main():

    show_face("idle")

    print()
    print("================================")
    print("데스크펫 하드웨어 통합 테스트")
    print("================================")
    print("버튼 누름 : 녹음 시작")
    print("버튼 뗌   : 녹음 종료 및 재생")
    print("최대 녹음 : 15초")
    print("종료      : Ctrl+C")
    print("================================")
    print()

    button_settings = gpiod.LineSettings(
        direction=Direction.INPUT,
        bias=Bias.PULL_UP,
    )

    with gpiod.request_lines(
        "/dev/gpiochip0",
        consumer="deskpet-record-play",
        config={BUTTON_GPIO: button_settings},
    ) as button:

        def pressed():

            return (
                button.get_value(BUTTON_GPIO)
                == Value.INACTIVE
            )

        raw = stable = pressed()

        changed_at = time.monotonic()

        recorder = None

        started_at = 0.0

        try:

            while True:

                now = time.monotonic()

                current = pressed()

                if current != raw:

                    raw = current
                    changed_at = now

                # 버튼 디바운싱
                if (
                    current != stable
                    and now - changed_at >= DEBOUNCE_SEC
                ):

                    stable = current

                    # 버튼을 누른 경우
                    if stable and recorder is None:

                        recorder = start_recording()

                        started_at = time.monotonic()

                    # 버튼을 뗀 경우
                    elif not stable and recorder is not None:

                        print("버튼 뗌: 녹음 종료")

                        stop_recording(recorder)

                        recorder = None

                        show_face("thinking")

                        if (
                            time.monotonic() - started_at
                            >= 0.3
                        ):

                            play_recorded()

                        else:

                            print("너무 짧게 눌렀습니다.")

                        show_face("idle")

                # 최대 15초 녹음 제한
                if recorder is not None and (
                    now - started_at >= MAX_RECORD_SEC
                    or recorder.poll() is not None
                ):

                    print("녹음 시간 종료")

                    stop_recording(recorder)

                    recorder = None

                    show_face("thinking")

                    play_recorded()

                    show_face("idle")

                time.sleep(0.01)

        finally:

            if recorder is not None:

                stop_recording(recorder)


# ==========================================
# 8. 프로그램 실행
# ==========================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print("\n테스트 종료")

    finally:

        try:
            show_face("idle")

        except Exception:
            pass
