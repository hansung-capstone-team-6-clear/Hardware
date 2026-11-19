#!/usr/bin/env python3
"""DeskPet PTT -> LCD -> I2S record -> /api/voice -> Edge TTS -> MAX98357A."""
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import board
import digitalio
import edge_tts
import gpiod
import requests
from adafruit_rgb_display import st7789
from gpiod.line import Bias, Direction, Value
from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE = Path.home() / "deskpet"
FACES = BASE / "faces"
AUDIO = BASE / "test_audio"
AUDIO.mkdir(parents=True, exist_ok=True)
RAW = AUDIO / "ptt_raw.wav"
UPLOAD = AUDIO / "ptt_16k.wav"
TTS_MP3 = AUDIO / "backend_tts.mp3"
TTS_WAV = AUDIO / "backend_tts.wav"
BACKEND = os.getenv("DESKPET_BACKEND_URL", "").rstrip("/")
DEVICE_TOKEN = os.getenv("DESKPET_DEVICE_TOKEN", "")
USER_ID = os.getenv("DESKPET_USER_ID", "test-user")
AUDIO_DEVICE = "plughw:2,0"
BUTTON_GPIO = 17
MAX_RECORD_SEC = 15


def make_display():
    spi = board.SPI()
    cs = digitalio.DigitalInOut(board.D5)
    dc = digitalio.DigitalInOut(board.D24)
    rst = digitalio.DigitalInOut(board.D25)
    backlight = digitalio.DigitalInOut(board.D23)
    backlight.direction = digitalio.Direction.OUTPUT
    backlight.value = True
    lcd = st7789.ST7789(
        spi, cs=cs, dc=dc, rst=rst,
        width=240, height=280, x_offset=0, y_offset=20,
        rotation=90, baudrate=16000000,
    )
    # For rotation=90, the input image needs 280x240 pixels.
    size = (lcd.height, lcd.width)
    images = {}
    for state in ("idle", "listening", "thinking", "speaking", "error"):
        path = FACES / f"{state}.png"
        if path.exists():
            with Image.open(path) as picture:
                images[state] = ImageOps.fit(picture.convert("RGB"), size)
        else:
            picture = Image.new("RGB", size, "white")
            draw = ImageDraw.Draw(picture)
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 27
                )
            except OSError:
                font = ImageFont.load_default()
            box = draw.textbbox((0, 0), state.upper(), font=font)
            x = (size[0] - (box[2] - box[0])) // 2
            y = (size[1] - (box[3] - box[1])) // 2
            draw.text((x, y), state.upper(), font=font, fill="black")
            images[state] = picture

    def show(state):
        lcd.image(images[state])
        print("LCD:", state.upper(), flush=True)

    return show


def start_recording():
    RAW.unlink(missing_ok=True)
    cmd = [
        "arecord", "-q", "-D", AUDIO_DEVICE,
        "-f", "S32_LE", "-r", "48000", "-c", "2",
        "-t", "wav", "-d", str(MAX_RECORD_SEC), str(RAW),
    ]
    print("🎤 녹음 시작")
    return subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)


def stop_recording(proc):
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
    try:
        _, errors = proc.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        _, errors = proc.communicate()
    if not RAW.exists() or RAW.stat().st_size < 1000:
        raise RuntimeError("녹음 파일이 생성되지 않았습니다. " + (errors or "").strip())
    print("🎤 녹음 종료:", RAW)


def convert_recording():
    # INMP441 L/R -> GND selects the left channel (channel 0).
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(RAW), "-af", "pan=mono|c0=c0",
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(UPLOAD),
    ], check=True)
    print("서버 전송용 WAV 생성:", UPLOAD)


def call_backend():
    req_id = f"pi_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:6]}"
    print("백엔드 요청:", req_id)
    with UPLOAD.open("rb") as wav:
        response = requests.post(
            BACKEND + "/api/voice",
            headers={"x-device-token": DEVICE_TOKEN},
            data={"user_id": USER_ID, "request_id": req_id},
            files={"audio": ("ptt_16k.wav", wav, "audio/wav")},
            timeout=(8, 90),
        )
    if not response.ok:
        raise RuntimeError(f"백엔드 HTTP {response.status_code}: {response.text[:350]}")
    data = response.json()
    print("STT:", data.get("stt_text", ""))
    print("처리 유형:", data.get("type", ""))
    print("응답 상태:", data.get("status", ""))
    output = data.get("output") or {}
    tts = output.get("tts", "") if isinstance(output, dict) else ""
    if isinstance(tts, dict):
        tts = tts.get("text") or tts.get("message") or ""
    return str(tts).strip()


def play_tts(text):
    print("AI 응답:", text)
    edge_tts.Communicate(text, "ko-KR-SunHiNeural").save_sync(str(TTS_MP3))
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(TTS_MP3), "-af", "volume=0.35",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(TTS_WAV),
    ], check=True)
    subprocess.run(["aplay", "-q", "-D", AUDIO_DEVICE, str(TTS_WAV)], check=True)


def main():
    if not DEVICE_TOKEN:
        print("기존 장치 토큰이 필요합니다. 먼저 다음과 같이 설정하세요:")
        print("export DESKPET_DEVICE_TOKEN='기존_장치_토큰'")
        return
    show = make_display()
    show("idle")
    print("데스크펫 백엔드 음성 연동:", BACKEND)
    print("버튼 누르기=녹음, 떼기=백엔드 전송 및 음성 응답, 종료=Ctrl+C")

    settings = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP)
    with gpiod.request_lines(
        "/dev/gpiochip0", consumer="deskpet-backend-voice",
        config={BUTTON_GPIO: settings},
    ) as button:
        def pressed():
            return button.get_value(BUTTON_GPIO) == Value.INACTIVE

        raw = stable = pressed()
        changed_at = time.monotonic()
        recorder = None
        started_at = 0.0
        try:
            while True:
                now = time.monotonic()
                value = pressed()
                if value != raw:
                    raw = value
                    changed_at = now
                if value != stable and now - changed_at >= 0.05:
                    stable = value
                    if stable and recorder is None:
                        show("listening")
                        recorder = start_recording()
                        started_at = time.monotonic()
                    elif not stable and recorder is not None:
                        rec = recorder
                        recorder = None
                        try:
                            stop_recording(rec)
                            if time.monotonic() - started_at < 0.4:
                                print("0.4초 이상 눌러주세요.")
                            else:
                                show("thinking")
                                convert_recording()
                                reply = call_backend()
                                if reply:
                                    show("speaking")
                                    play_tts(reply)
                                else:
                                    print("백엔드 output.tts에 응답 문구가 없습니다.")
                        except Exception as exc:
                            print("오류:", exc)
                            show("error")
                            time.sleep(1)
                        finally:
                            show("idle")
                if recorder is not None and (
                    now - started_at >= MAX_RECORD_SEC or recorder.poll() is not None
                ):
                    rec = recorder
                    recorder = None
                    try:
                        stop_recording(rec)
                        show("thinking")
                        convert_recording()
                        reply = call_backend()
                        if reply:
                            show("speaking")
                            play_tts(reply)
                        else:
                            print("백엔드 output.tts에 응답 문구가 없습니다.")
                    except Exception as exc:
                        print("오류:", exc)
                        show("error")
                        time.sleep(1)
                    finally:
                        show("idle")
                time.sleep(0.01)
        finally:
            if recorder is not None:
                stop_recording(recorder)
            show("idle")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n종료")
