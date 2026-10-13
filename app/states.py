"""상태별 LED·LCD 표현 (contracts § 5, knowledge 레포 wiki/desk-pet-device-states). 색은 여기 한 곳에서만 정한다.

THINKING·ALERT·ERROR 색은 제안값이다 (디자인 확정 전). parts/led 테스트에서 눈으로 구분되는지 확인한다.
"""

STATES = {
    "IDLE":      {"led": ("green", "solid"),       "face": "idle"},       # 부팅 완료, 출력 완료
    "LISTENING": {"led": ("yellow", "blink"),      "face": "listening"},  # 버튼 누르는 동안
    "THINKING":  {"led": ("white", "blink"),       "face": "thinking"},   # 버튼 뗀 직후 (Pi가 직접)
    "SPEAKING":  {"led": ("blue", "blink"),        "face": "speaking"},   # 응답 status OK, TTS 재생 중
    "ALERT":     {"led": ("orange", "fast_blink"), "face": "alert"},      # proactive_alert 재생 중
    "ERROR":     {"led": ("red", "blink"),         "face": "surprised"},  # status가 OK 아님, 10초 초과, 연결·장치 오류
}
