# Desk Pet Hardware

데스크펫 본체(Raspberry Pi 4B) 쪽 레포. 버튼을 누르고 말하면 녹음해서 백엔드로 보내고,
돌아온 답을 음성·LED·LCD로 보여 준다. 마감 알림도 백엔드에서 받아 먼저 말해 준다.

> 설계 정본은 knowledge 레포 `projects/desk-pet/`다. 하드웨어 범위·리스크는 `hardware/README.md`,
> 백엔드와 주고받는 형식은 `contracts.md`. 형식을 바꾸려면 `contracts.md` PR부터 올린다.

## 이 레포가 하는 일

| 한다 | 하지 않는다 (desk-pet-backend가 함) |
| --- | --- |
| 녹음·업로드, TTS 재생, LED·LCD 표시, 백엔드 WS 연결 유지 | 말 해석(LLM), Eureka 호출, 마감 판단 |

## 폴더 구조 — 작업 순서대로

```text
Hardware/
├── setup/      ① Pi 처음 준비: OS, 패키지, config.txt, 파이썬 환경 — 한 번만
├── parts/      ② 부품 하나씩 단독 테스트: audio → button → led → lcd (배선·테스트·결과 기록)
│   ├── audio/      마이크 + 앰프 + 스피커 (I2S 공유라 한 폴더)
│   ├── button/
│   ├── led/
│   └── lcd/
└── app/        ③ 실제로 도는 통합 프로그램: parts에서 검증한 코드를 devices/로 옮겨 연결
```

`parts/README.md`에 전체 핀맵과 부품별 완료 기준이 있다.

## 1차 일정

| 기한 | 할 일 | 완료 기준 |
| --- | --- | --- |
| 10/18 | `setup/`, `parts/audio`, `parts/button` | 5초 녹음 → 재생, 버튼 누름·뗌 출력 |
| 10/31 | `parts/led`, `parts/lcd`, `app/devices/*`, `app/tts.py` | 버튼 → 녹음 → 백엔드 → 음성 재생까지 한 번에 |
| 11/14 | 알림 음성, 백엔드와 실제 연결 | 마감 3분 뒤 업무 + 2분 전 알림이 1분 안에 들린다 |
| 11/28 | 하우징 조립 | 시나리오 리허설 |

지금 바로 할 수 있는 것: `app/`을 노트북에서 실행해 백엔드 WS 연결을 확인 (`app/README.md` § 실행).

## 작업 규칙

1. `main`에 직접 push하지 않는다. 브랜치(`feat/…`, `fix/…`) → PR → 팀원 1명 리뷰 → merge.
2. 커밋 메시지 앞에 종류를 붙인다: `feat:` `fix:` `docs:` `test:` `chore:`.
3. 부품 테스트 결과(성공·실패 모두)는 해당 `parts/<부품>/README.md`의 결과 기록 표에 남긴다. 다음 사람이 같은 데서 막히지 않게.
4. `.env`, 비밀번호, 토큰은 커밋하지 않는다.
5. 파일은 UTF-8(BOM 없음)로 저장한다 (`.editorconfig`).
