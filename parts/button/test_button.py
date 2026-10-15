from gpiozero import DigitalInputDevice
from signal import pause

pin = DigitalInputDevice(17, pull_up=None, active_state=True, bounce_time=0.05)
print("현재 값:", pin.value, "(버튼 안 누른 상태)")
pin.when_activated = lambda: print("1 (HIGH)")
pin.when_deactivated = lambda: print("0 (LOW)")
print("버튼을 눌렀다 떼 보세요 (Ctrl+C로 종료)")
pause()
