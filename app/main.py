"""데스크펫 Pi 프로그램 진입점. 실행: app 폴더에서 python main.py

흐름 (contracts § 1, § 2, § 5 — 팀 인터페이스 이름으로는 IDeviceStateManager):
  버튼 누름  → LISTENING, 녹음 시작                 (IDLE이 아닐 때 누름은 무시)
  버튼 뗌    → THINKING, 녹음 종료 → send_voice() → status OK면 SPEAKING, 아니면 ERROR → output.tts 재생 → IDLE
  알림 수신  → ALERT, output.tts 재생 → IDLE

지금 상태: 버튼 이벤트 연결, 백엔드 WS 연결·PING·재연결, 알림 수신 로그까지 동작한다.
노트북에서 돌릴 때는 가짜 핀을 쓴다: GPIOZERO_PIN_FACTORY=mock python main.py
"""

import asyncio
import logging

import backend_client
from devices import button
from states import STATES

log = logging.getLogger("deskpet")

state = "IDLE"


async def show(new_state: str, lcd: dict | None = None) -> None:
    """상태를 바꾸고 LED·LCD를 맞춘다. lcd가 오면 (백엔드 output.lcd) 그 표정·문구를 쓴다."""
    global state
    state = new_state
    led_color, led_mode = STATES[new_state]["led"]
    face = (lcd or {}).get("expression", STATES[new_state]["face"])
    text = (lcd or {}).get("text")
    log.info("상태 %s (LED %s %s, 표정 %s, 문구 %s)", new_state, led_color, led_mode, face, text)
    # TODO(hardware, 10/31): devices.led.show(led_color, led_mode), devices.lcd.show(face, text)


async def on_button_pressed() -> None:
    if state != "IDLE":  # THINKING·SPEAKING 중 누름은 무시
        return
    await show("LISTENING")
    # TODO(hardware, 10/31): devices.audio.start_recording()


async def on_button_released() -> None:
    if state != "LISTENING":
        return
    await show("THINKING")
    # TODO(hardware, 10/31):
    #   wav = devices.audio.stop_recording()
    #   try:
    #       res = await backend_client.send_voice(wav, backend_client.new_request_id())
    #   except Exception:
    #       await show("ERROR"); await tts.speak("연결에 문제가 있어요. 다시 말씀해 주세요.")
    #   else:
    #       await show("SPEAKING" if res["status"] == "OK" else "ERROR", res["output"].get("lcd"))
    #       await tts.speak(res["output"]["tts"])
    await show("IDLE")


async def on_message(message: dict) -> None:
    """백엔드가 먼저 보낸 메시지 (proactive_alert, output)."""
    log.info("수신 %s: %s", message["event"], message["output"]["tts"])
    # TODO(hardware, 11/14): IDLE이 아니면 지금 출력이 끝난 뒤 재생 (alertWhileBusy)
    if message["event"] == "proactive_alert":
        await show("ALERT", message["output"].get("lcd"))
    else:
        await show("ERROR" if message.get("type") == "error" else "SPEAKING", message["output"].get("lcd"))
    # TODO(hardware, 11/14): await tts.speak(message["output"]["tts"])
    await show("IDLE")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    await show("IDLE")
    button.setup(on_button_pressed, on_button_released)
    await backend_client.listen(on_message)


if __name__ == "__main__":
    asyncio.run(main())
