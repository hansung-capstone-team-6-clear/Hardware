# LCD 표정 에셋 (faces)

ST7789 1.69" IPS LCD (240×280, SPI)에 표시하는 표정 이미지.

## 규격
- 크기: **240 × 280 px** (세로)
- 형식: PNG, RGB 24bit, 투명도(알파) 없음
- 스타일: 밝은 배경 `#FAFAF8` + 진한 회색 `#222226` 점 눈 / 입 + 분홍 볼터치 `#FFB6C4`
- 단색 위주, 그라데이션 사용하지 않음 (LCD가 RGB565라 계단처럼 보임)

## 파일명 = lcdExpressionId
| 파일 | lcdExpressionId | 사용 시점 | LED (제안) |
|---|---|---|---|
| idle.png | idle | 대기 | 초록 · 상시 |
| listening.png | listening | Push-to-Talk 녹음 중 | 노랑 · 점멸 |
| thinking.png | thinking | STT / LLM 처리 중 | 보라 · 숨쉬기 |
| speaking.png | speaking | TTS 재생 중 | 파랑 · 점멸 |
| alert.png | alert | 마감 임박 proactive_alert | 주황 · 빠른 점멸 |
| error.png | error | 네트워크 / 장치 오류 | 빨강 · 상시 |

- 파일명은 소문자, contracts.md의 `lcdExpressionId` 값과 같아야 함
- 새 표정 추가 시 contracts.md를 먼저 수정(knowledge PR)한 뒤 여기에 추가

## 레이아웃
- 안전 여백: 가장자리 20px 안쪽에만 그림 (패널 모서리가 둥글어 잘림)
- 표정 영역: y 20 ~ 210
- 텍스트 영역: **y 210 ~ 280은 비워둠** → `lcdText`(예: "마감 1시간 전")를 코드에서 덧그림
