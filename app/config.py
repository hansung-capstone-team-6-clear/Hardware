"""환경 변수 설정. 값은 app/.env에서 읽는다 (.env.example 참고)."""

import os

from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")  # 백엔드 노트북 주소
DEVICE_ID = os.environ.get("DEVICE_ID", "pet-01")
DEVICE_TOKEN = os.environ.get("DEVICE_TOKEN", "")  # 백엔드 .env의 DEVICE_TOKEN과 같은 값
TTS_VOICE = os.environ.get("TTS_VOICE", "ko-KR-SunHiNeural")
