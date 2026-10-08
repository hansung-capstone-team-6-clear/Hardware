"""백엔드와의 통신 (contracts § 1, § 2). 형식을 바꾸려면 knowledge 레포 contracts.md부터 고친다."""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

import config
import httpx
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed, InvalidStatus

log = logging.getLogger(__name__)

HEADERS = {"x-device-token": config.DEVICE_TOKEN}


async def send_voice(wav: bytes) -> dict:
    """POST /voice — 녹음한 WAV를 보내고 {requestId, type, text}를 받는다.

    10초 안에 응답이 없거나 실패하면 예외가 난다 → 호출한 쪽이 ERROR 상태를 보여 준다.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            f"{config.BACKEND_URL}/voice",
            headers=HEADERS,
            data={"deviceId": config.DEVICE_ID},
            files={"audio": ("voice.wav", wav, "audio/wav")},
        )
        res.raise_for_status()
        return res.json()


async def listen_alerts(on_alert: Callable[[dict], Awaitable[None]]) -> None:
    """WS에 계속 붙어 있으면서 proactive_alert가 오면 on_alert(alert)를 부른다.

    30초마다 ping, 끊기면 5초 뒤 다시 연결한다. 이 함수는 끝나지 않는다.
    """
    url = config.BACKEND_URL.replace("http", "ws", 1) + f"/ws/{config.DEVICE_ID}"
    while True:
        try:
            async with connect(url, additional_headers=HEADERS) as ws:
                log.info("백엔드 WS 연결됨: %s", url)
                pinger = asyncio.create_task(_ping_forever(ws))
                try:
                    async for raw in ws:
                        message = json.loads(raw)
                        if message.get("event") == "proactive_alert":
                            await on_alert(message)
                finally:
                    pinger.cancel()
        except (OSError, ConnectionClosed, InvalidStatus) as e:
            log.warning("백엔드 WS 끊김, 5초 뒤 재연결: %s", e)
        await asyncio.sleep(5)


async def _ping_forever(ws: ClientConnection) -> None:
    while True:
        await asyncio.sleep(30)
        await ws.send(json.dumps({"event": "ping"}))
