"""데스크펫 Pi 프로그램 진입점. 실행: app 폴더에서 python main.py

흐름 (contracts § 1, § 2, § 5):
  버튼 누름  → LISTENING, 녹음 시작
  버튼 뗌    → THINKING, 녹음 종료 → backend_client.send_voice() → 응답 type에 맞는 상태로 tts.speak() → IDLE
  알림 수신  → ALERT 상태로 tts.speak(alert["text"]) → IDLE

지금 상태: 버튼 이벤트 연결, 백엔드 WS 연결, 알림 수신 로그까지 동작한다.
노트북에서 돌릴 때는 가짜 핀을 쓴다: GPIOZERO_PIN_FACTORY=mock python main.py
"""

import asyncio
import logging

import backend_client
from devices import button
from states import STATES

log = logging.getLogger("deskpet")


async def show(state: str) -> None:
    """상태에 맞춰 LED·LCD를 바꾼다."""
    led_color, led_mode = STATES[state]["led"]
    face = STATES[state]["face"]
    log.info("상태 %s (LED %s %s, 표정 %s)", state, led_color, led_mode, face)
    # TODO(hardware, 10/31): devices.led.show(led_color, led_mode), devices.lcd.show(face)


async def on_button_pressed() -> None:
    await show("LISTENING")
    # TODO(hardware, 10/31): devices.audio.start_recording()


async def on_button_released() -> None:
    await show("THINKING")
    # TODO(hardware, 10/31):
    #   wav = devices.audio.stop_recording()
    #   try: res = await backend_client.send_voice(wav)  /  except: ERROR 상태 + 안내 문구
    #   await show(STATE_BY_RESPONSE_TYPE[res["type"]]); await tts.speak(res["text"])
    await show("IDLE")


async def on_alert(alert: dict) -> None:
    log.info("알림 수신: %s", alert["text"])
    await show("ALERT")
    # TODO(hardware, 11/14): await tts.speak(alert["text"])
    await show("IDLE")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    await show("IDLE")
    button.setup(on_button_pressed, on_button_released)
    await backend_client.listen_alerts(on_alert)


if __name__ == "__main__":
    asyncio.run(main())
