"""상태별 LED·LCD 표현 (contracts § 5). 색과 표정은 여기 한 곳에서만 정한다.

색값은 parts/led 테스트에서 눈으로 구분되는지 확인한 뒤 고친다.
"""

STATES = {
    "IDLE":      {"led": ("green", "solid"),  "face": "idle"},       # 대기
    "LISTENING": {"led": ("yellow", "blink"), "face": "listening"},  # 버튼 누르는 동안
    "THINKING":  {"led": ("yellow", "solid"), "face": "thinking"},   # 버튼 뗀 뒤 응답 대기
    "SPEAKING":  {"led": ("blue", "blink"),   "face": "speaking"},   # 응답 재생 중
    "ALERT":     {"led": ("orange", "blink"), "face": "alert"},      # 선제 알림 재생 중
    "ERROR":     {"led": ("red", "solid"),    "face": "error"},      # 오류·타임아웃·연결 끊김
}

# 백엔드 응답 type → 재생하는 동안의 상태 (contracts § 1)
STATE_BY_RESPONSE_TYPE = {
    "task_created": "SPEAKING",
    "task_completed": "SPEAKING",
    "task_updated": "SPEAKING",
    "task_list": "SPEAKING",
    "reminder_set": "SPEAKING",
    "clarify": "SPEAKING",
    "no_speech": "ERROR",
    "error": "ERROR",
}
