#!/bin/bash
# ══════════════════════════════════════════════════
#  SPY Auto Report — 원클릭 설치
#  실행: chmod +x setup.sh && ./setup.sh
# ══════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=$(which python3)

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   SPY Auto Report — Setup            ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# ─── 1. Python 패키지 ───
echo "📦 Python 패키지 설치..."
pip3 install yfinance pandas playwright --quiet 2>/dev/null || \
pip3 install yfinance pandas playwright --break-system-packages --quiet
echo "   ✅ yfinance, pandas, playwright"

# Playwright 브라우저 설치 (스크린샷용)
echo "🌐 Playwright Chromium 설치..."
python3 -m playwright install chromium --with-deps 2>/dev/null || \
python3 -m playwright install chromium
echo "   ✅ Chromium 설치 완료"

# ─── 2. GitHub Pages 리포 초기화 ───
echo ""
echo "🔗 GitHub Pages 설정..."
REPO_PATH="$HOME/spy-report-site"

if [ ! -d "$REPO_PATH/.git" ]; then
    echo "   GitHub Pages 리포를 설정하시겠습니까?"
    echo "   (카톡 링크 공유에 필요합니다)"
    echo ""
    echo "   순서:"
    echo "   1. github.com에서 'spy-report' 리포 생성 (Public)"
    echo "   2. Settings → Pages → Source: main branch"
    echo "   3. 아래에 리포 URL 입력"
    echo ""
    read -p "   GitHub 리포 URL (또는 Enter로 스킵): " REPO_URL

    if [ -n "$REPO_URL" ]; then
        git clone "$REPO_URL" "$REPO_PATH" 2>/dev/null || {
            mkdir -p "$REPO_PATH"
            cd "$REPO_PATH"
            git init
            git remote add origin "$REPO_URL"
            echo "# SPY Auto Report" > README.md
            git add -A && git commit -m "init" && git push -u origin main 2>/dev/null || true
        }
        echo "   ✅ GitHub Pages 리포 준비: $REPO_PATH"

        # config.json에 URL 반영
        read -p "   GitHub username: " GH_USER
        if [ -n "$GH_USER" ]; then
            cd "$SCRIPT_DIR"
            python3 -c "
import json
with open('config.json') as f: c = json.load(f)
c['github_pages']['repo_path'] = '$REPO_PATH'
c['github_pages']['repo_url'] = '$REPO_URL'
c['github_pages']['base_url'] = 'https://$GH_USER.github.io/spy-report'
with open('config.json','w') as f: json.dump(c, f, indent=2)
print('   ✅ config.json GitHub Pages 설정 완료')
"
        fi
    else
        echo "   ⏭️  GitHub Pages 스킵 (나중에 설정 가능)"
    fi
else
    echo "   ✅ GitHub Pages 리포 존재: $REPO_PATH"
fi

# ─── 3. Gmail 설정 ───
echo ""
echo "📧 Gmail 설정..."
echo "   Gmail App Password가 필요합니다."
echo "   생성 방법: Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호"
echo ""
read -p "   Gmail 주소 (또는 Enter로 스킵): " GMAIL_ADDR

if [ -n "$GMAIL_ADDR" ]; then
    read -p "   App Password (xxxx-xxxx-xxxx-xxxx): " GMAIL_PW
    cd "$SCRIPT_DIR"
    python3 -c "
import json
with open('config.json') as f: c = json.load(f)
c['email']['sender'] = '$GMAIL_ADDR'
c['email']['recipient'] = '$GMAIL_ADDR'
c['email']['app_password'] = '$GMAIL_PW'
c['email']['enabled'] = True
with open('config.json','w') as f: json.dump(c, f, indent=2)
print('   ✅ Gmail 설정 완료')
"
else
    echo "   ⏭️  Gmail 스킵"
fi

# ─── 4. iMessage 설정 ───
echo ""
echo "💬 iMessage 설정..."
read -p "   iMessage 받을 전화번호 (+1... 또는 Enter로 스킵): " PHONE

if [ -n "$PHONE" ]; then
    cd "$SCRIPT_DIR"
    python3 -c "
import json
with open('config.json') as f: c = json.load(f)
c['imessage']['phone'] = '$PHONE'
c['imessage']['enabled'] = True
with open('config.json','w') as f: json.dump(c, f, indent=2)
print('   ✅ iMessage 설정 완료')
"
else
    echo "   ⏭️  iMessage 스킵"
fi

# ─── 5. cron/launchd 등록 ───
echo ""
echo "⏰ 스케줄 등록 (월-금 하루 3회)..."
echo "   09:00 ET — 프리마켓 브리핑"
echo "   12:30 ET — 미드데이 체크"
echo "   21:00 ET — 데일리 리캡"
echo ""

CRON_TAG="# SPY-AUTO-REPORT"

# 기존 제거
crontab -l 2>/dev/null | grep -v "$CRON_TAG" | grep -v "spy_report.py" > /tmp/cron_clean || true

# 새로 추가
cat >> /tmp/cron_clean << CEOF
$CRON_TAG
0 9 * * 1-5 cd $SCRIPT_DIR && TZ=America/New_York $PYTHON spy_report.py --session pre >> $SCRIPT_DIR/reports/cron.log 2>&1 $CRON_TAG
30 12 * * 1-5 cd $SCRIPT_DIR && TZ=America/New_York $PYTHON spy_report.py --session mid >> $SCRIPT_DIR/reports/cron.log 2>&1 $CRON_TAG
0 21 * * 1-5 cd $SCRIPT_DIR && TZ=America/New_York $PYTHON spy_report.py --session post >> $SCRIPT_DIR/reports/cron.log 2>&1 $CRON_TAG
CEOF

crontab /tmp/cron_clean && rm /tmp/cron_clean
echo "   ✅ cron 등록 완료"

# macOS launchd (더 안정적)
if [[ "$(uname)" == "Darwin" ]]; then
    echo ""
    echo "🍎 macOS launchd 등록..."
    PLIST_DIR="$HOME/Library/LaunchAgents"
    mkdir -p "$PLIST_DIR"

    for session in pre mid post; do
        case $session in
            pre)  hour=9;  minute=0;  label="premarket" ;;
            mid)  hour=12; minute=30; label="midday" ;;
            post) hour=21; minute=0;  label="recap" ;;
        esac

        PLIST="$PLIST_DIR/com.spy.report.$label.plist"
        cat > "$PLIST" << PEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.spy.report.$label</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$SCRIPT_DIR/spy_report.py</string>
        <string>--session</string>
        <string>$session</string>
    </array>
    <key>WorkingDirectory</key><string>$SCRIPT_DIR</string>
    <key>StartCalendarInterval</key>
    <array>
$(for day in 1 2 3 4 5; do
echo "        <dict><key>Weekday</key><integer>$day</integer><key>Hour</key><integer>$hour</integer><key>Minute</key><integer>$minute</integer></dict>"
done)
    </array>
    <key>StandardOutPath</key><string>$SCRIPT_DIR/reports/launchd_$label.log</string>
    <key>StandardErrorPath</key><string>$SCRIPT_DIR/reports/launchd_$label_err.log</string>
    <key>EnvironmentVariables</key>
    <dict><key>TZ</key><string>America/New_York</string><key>PATH</key><string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string></dict>
</dict>
</plist>
PEOF
        launchctl unload "$PLIST" 2>/dev/null || true
        launchctl load "$PLIST"
        echo "   ✅ launchd: $label ($hour:$(printf '%02d' $minute) ET, 월-금)"
    done
fi

# ─── 6. 테스트 실행 ───
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "🧪 테스트 실행할까요? (y/n): " DO_TEST
if [[ "$DO_TEST" == "y" || "$DO_TEST" == "Y" ]]; then
    echo ""
    cd "$SCRIPT_DIR"
    python3 spy_report.py --session post --no-deploy
fi

# ─── 완료 ───
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   ✅ 설치 완료!                      ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
echo "  파일 구조:"
echo "  $SCRIPT_DIR/"
echo "  ├── config.json         ← 설정 (이메일/iMessage/GitHub)"
echo "  ├── spy_report.py       ← 메인 실행기"
echo "  ├── spy_engine.py       ← 데이터 + 지표 계산"
echo "  ├── spy_template.py     ← 3종 템플릿 (pre/mid/post)"
echo "  └── reports/            ← 생성된 리포트"
echo ""
echo "  스케줄:"
echo "  ⏰ 09:00 ET (월-금) — 프리마켓 브리핑"
echo "  ⏰ 12:30 ET (월-금) — 미드데이 체크"
echo "  ⏰ 21:00 ET (월-금) — 데일리 리캡"
echo ""
echo "  딜리버리:"
echo "  📧 Gmail → 풀 리포트 이메일 본문"
echo "  💬 iMessage → 텍스트 요약 (Action/Entry/TP/SL)"
echo "  🔗 GitHub Pages → 카톡 공유용 링크"
echo "  📸 스크린샷 → 카톡 공유용 이미지"
echo "  📋 클립보드 → 텍스트+링크 자동 복사 → 카톡 붙여넣기"
echo ""
echo "  수동 실행:"
echo "  python3 spy_report.py                # 자동 세션"
echo "  python3 spy_report.py --session pre  # 프리마켓 강제"
echo ""
