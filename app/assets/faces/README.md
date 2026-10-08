# app/assets/faces/ — LCD 표정 이미지

팀 디자인 시안의 표정을 PNG로 만들어 여기에 둔다. `app/states.py`의 `face` 값과 파일 이름이 같아야 한다.

| 파일 | 상태 | 시안의 표정 |
| --- | --- | --- |
| `idle.png` | IDLE | 기본 (눈 뜸) |
| `listening.png` | LISTENING | 듣는 중 (눈 감음) |
| `thinking.png` | THINKING | 생각 중 (…) |
| `speaking.png` | SPEAKING | 말하는 중 (입 열림) |
| `alert.png` | ALERT | 안내/알림 |
| `error.png` | ERROR | 놀람 (!) |

- 크기 240 × 280 픽셀, PNG.
- 아래쪽 약 60픽셀은 문구(예: "마감 1시간 전")가 들어갈 자리로 비워 둔다.
