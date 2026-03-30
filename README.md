# SPY Auto Report Engine v3 🇺🇸📊

하루 3번 자동 SPY 테크니컬 분석 리포트 — Gmail, iMessage, 카톡(GitHub Pages) 멀티채널 딜리버리

## 5분 설치

```bash
cd ~/spy-auto-report
chmod +x setup.sh
./setup.sh
```

대화형으로 Gmail, iMessage, GitHub Pages 설정을 물어봅니다.
설치 완료 후 **월-금 하루 3번 자동 실행**됩니다.

## 리포트 스케줄

| 시간 (ET) | 세션 | 내용 |
|-----------|------|------|
| **09:00** | 🌅 프리마켓 | ES 선물 갭, 글로벌 마켓, 갭 시나리오별 플랜, Key Levels |
| **12:30** | 📊 미드데이 | 장중 스코어보드, VWAP/볼륨 체크, 오후 전략 조정 |
| **21:00** | 🌙 리캡 | 풀 테크니컬 (MA 7개, RSI/MACD/Stoch, S/R, BB, 시나리오) |

## 딜리버리 채널

| 채널 | 내용 | 설정 |
|------|------|------|
| 📧 Gmail | 풀 리포트 이메일 본문 | config.json → email |
| 💬 iMessage | 텍스트 요약 (Action/Entry/TP/SL) | config.json → imessage |
| 🔗 GitHub Pages | 카톡 공유용 웹 링크 | config.json → github_pages |
| 📸 Screenshot | 카톡 공유용 이미지 캡처 | 자동 (Playwright) |
| 📋 Clipboard | 텍스트 + 링크 클립보드 복사 | 자동 (macOS) |

### 카톡 공유 플로우
1. 리포트 생성 시 자동으로 이미지 캡처 + 텍스트가 클립보드에 복사됨
2. macOS 알림 뜨면 → 카톡 열고 → 붙여넣기 (텍스트)
3. Finder가 이미지를 보여줌 → 카톡에 드래그앤드롭
4. 링크 포함되어 있으니 받는 사람이 탭하면 풀 리포트 확인

## 수동 실행

```bash
python3 spy_report.py                    # 시간대 자동 감지
python3 spy_report.py --session pre      # 프리마켓 강제
python3 spy_report.py --session mid      # 미드데이 강제
python3 spy_report.py --session post     # 데일리 리캡 강제
python3 spy_report.py --no-email         # 이메일 스킵
python3 spy_report.py --no-imessage      # iMessage 스킵
python3 spy_report.py --no-deploy        # GitHub Pages 스킵
python3 spy_report.py --no-kakao         # 카톡 준비 스킵
```

## Composite Signal 로직

### 단기 (1-5일)
EMA 5/8/9/21 vs 현재가, RSI 14 (과매도/과매수 영역 구분), MACD + histogram 방향,
Stochastic, VWAP 위/아래, 볼륨 컨펌 (가격 방향 + 볼륨 방향 일치 여부)
→ 각 항목 +1/-1 스코어링 → Strong Sell ~ Strong Buy

### 중기 (1-4주)
SMA 50 위치 (1.5x 가중), SMA 200 위치 (2x 가중), Golden/Death Cross (1.5x),
SMA 50/200 기울기, RSI 50 기준
→ 가중 스코어링 → Strong Sell ~ Strong Buy

### Today's Action
단기 + 중기 종합 → CALL / PUT / WAIT
- 둘 다 같은 방향 → 확신도 높음, 1/2 Kelly
- 엇갈림 → 확신도 보통, 1/4 Kelly (counter-trend)
- 불명확 → WAIT
- Entry/Target/Stop은 지지/저항 레벨에서 자동 산출

## 요구사항
- macOS (iMessage, 클립보드, launchd)
- Python 3.9+
- `yfinance`, `pandas`, `playwright`
- Gmail App Password
- GitHub 계정 (Pages 링크용)
