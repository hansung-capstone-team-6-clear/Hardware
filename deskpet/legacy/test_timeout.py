import time
import signal

from voice_client_v3 import (
    change_state,
    IDLE,
    THINKING,
    ERROR,
    DeadlineExceeded,
    timeout_handler,
)

TEST_TIMEOUT = 3

print("========== Timeout 테스트 ==========")

change_state(IDLE)
change_state(THINKING)

old_handler = signal.getsignal(signal.SIGALRM)
start = time.monotonic()

try:
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, TEST_TIMEOUT)

    # 서버 응답이 늦어지는 상황을 모의
    print("[TEST] 응답 지연 상황 시뮬레이션")
    time.sleep(10)

except DeadlineExceeded:
    elapsed = time.monotonic() - start
    print(f"\n[TIMEOUT] {elapsed:.2f}초 경과")
    change_state(ERROR, text="응답 시간 초과")

finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    signal.signal(signal.SIGALRM, old_handler)
    change_state(IDLE)

print("\n========== 테스트 종료 ==========")
