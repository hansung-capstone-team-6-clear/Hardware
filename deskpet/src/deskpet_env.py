"""환경 변수 로더.

레포 루트의 `.env`를 읽어 os.environ에 넣는다. 이미 셸이나 systemd에 설정된 값이 있으면
그 값을 그대로 둔다 (덮어쓰지 않음). 외부 패키지(python-dotenv) 없이 동작한다.

값 형식: KEY=VALUE  (한 줄에 하나, # 로 시작하면 주석, 값의 앞뒤 따옴표는 제거)
"""
import os
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent


def load_env(path=REPO_DIR / ".env"):
    path = Path(path)
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def backend_url():
    """백엔드 주소. 코드에 주소를 두지 않고 DESKPET_BACKEND_URL에서만 읽는다."""
    url = os.environ.get("DESKPET_BACKEND_URL", "").strip().rstrip("/")
    if not url:
        raise SystemExit(
            "DESKPET_BACKEND_URL이 없습니다. .env에 설정하세요 (.env.example 참고)."
        )
    return url


def device_token():
    """장치 토큰. DESKPET_DEVICE_TOKEN, 없으면 예전 이름 DEVICE_TOKEN."""
    return os.environ.get("DESKPET_DEVICE_TOKEN") or os.environ.get("DEVICE_TOKEN", "")


load_env()
