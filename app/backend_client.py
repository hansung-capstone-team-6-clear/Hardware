"""백엔드와의 통신 (contracts § 1, § 2). 형식을 바꾸려면 knowledge 레포 contracts.md부터 고친다.

팀 인터페이스 이름으로는 IVoiceUpload(send_voice)와 IBackendConnection(listen)이다.
"""

import asyncio
import json
import logging
import secrets
import time
from collections.abc import Awaitable, Callable

import httpx
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed, InvalidStatus

import config

log = logging.getLogger(__name__)

HEADERS = {"x-device-token": config.DEVICE_TOKEN}


def new_request_id() -> str:
    """음성 요청마다 새로 만든다. 예: req_20261008_153000_a1b2"""
    return f"req_{time.strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(2)}"


async def send_voice(wav: bytes, request_id: str) -> dict:
    """POST /api/voice — 녹음한 WAV를 보내고 {request_id, status, stt_text, type, output}을 받는다.

    10초 안에 응답이 없거나 실패하면 예외가 난다 → 호출한 쪽이 ERROR 상태를 보여 준다.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            f"{config.BACKEND_URL}/api/voice",
            headers=HEADERS,
            data={"user_id": config.USER_ID, "request_id": request_id},
            files={"audio": ("voice.wav", wav, "audio/wav")},
        )
        res.raise_for_status()
        return res.json()


async def listen(on_message: Callable[[dict], Awaitable[None]]) -> None:
    """WS에 계속 붙어 있으면서 proactive_alert·output 메시지가 오면 on_message(message)를 부른다.

    30초마다 텍스트 PING을 보내고, 끊기면 3초 뒤 다시 연결한다. 이 함수는 끝나지 않는다.
    """
    url = config.BACKEND_URL.replace("http", "ws", 1) + f"/ws/hardware/{config.USER_ID}"
    while True:
        try:
            async with connect(url, additional_headers=HEADERS) as ws:
                pinger = asyncio.create_task(_ping_forever(ws))
                try:
                    async for raw in ws:
                        await _dispatch(raw, on_message)
                finally:
                    pinger.cancel()
        except (OSError, ConnectionClosed, InvalidStatus) as e:
            log.warning("백엔드 WS 끊김, 3초 뒤 재연결: %s", e)
        await asyncio.sleep(3)


async def _dispatch(raw: str | bytes, on_message: Callable[[dict], Awaitable[None]]) -> None:
    try:
        message = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("JSON이 아닌 메시지를 버림: %r", raw[:100])
        return
    event = message.get("event")
    if event == "connected":
        log.info("백엔드 WS 연결됨: user_id=%s", message.get("user_id"))
    elif event in ("proactive_alert", "output"):
        await on_message(message)


async def _ping_forever(ws: ClientConnection) -> None:
    while True:
        await asyncio.sleep(30)
        await ws.send("PING")
