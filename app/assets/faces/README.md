# app/assets/faces/ — LCD 표정 이미지

팀 디자인 시안의 표정을 PNG로 만들어 여기에 둔다. 파일 이름은 `app/states.py`의 `face` 값,
그리고 백엔드가 보내는 `output.lcd.expression` 값과 같아야 한다 (contracts § 1·5).

| 파일 | 쓰이는 때 | 시안의 표정 |
| --- | --- | --- |
| `idle.png` | IDLE | 기본 (눈 뜸) |
| `listening.png` | LISTENING | 듣는 중 (눈 감음) |
| `thinking.png` | THINKING, 재질문할 때 | 생각 중 (…) |
| `speaking.png` | SPEAKING | 말하는 중 (입 열림) |
| `alert.png` | ALERT | 안내/알림 |
| `surprised.png` | ERROR | 놀람 (!) |
| `happy.png` | 업무 등록·완료 응답 | 웃음 |

- 크기 240 × 280 픽셀, PNG.
- 아래쪽 약 60픽셀은 문구(예: "마감 1시간 전")가 들어갈 자리로 비워 둔다.
