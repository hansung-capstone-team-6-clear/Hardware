"""문장 → 음성 재생. edge-tts(무료, 키 불필요)로 mp3를 만들고 mpg123으로 재생한다."""


async def speak(text: str) -> None:
    """text를 config.TTS_VOICE 목소리로 읽어 준다. 재생이 끝나야 돌아온다.

    1. edge_tts.Communicate(text, config.TTS_VOICE).save("/tmp/deskpet-tts.mp3")
    2. asyncio.create_subprocess_exec("mpg123", "-q", "/tmp/deskpet-tts.mp3") 후 wait()
    명령은 parts/audio/README.md의 TTS 테스트에서 먼저 확인한다.
    edge-tts가 막히면 Google Cloud TTS로 바꾼다 (knowledge 레포 architecture.md § 1차 기술 선택).
    """
    # TODO(hardware, 10/31)
    raise NotImplementedError
