#!/usr/bin/env python3
"""
SPY Auto Report — 하루 3번 자동 분석 + 멀티채널 딜리버리
══════════════════════════════════════════════════════════
Channels:
  📧 Gmail      — 풀 리포트 이메일 본문
  💬 iMessage   — 텍스트 요약
  🔗 GitHub Pages — 웹 링크 (카톡 공유용)
  📸 Screenshot — 카톡용 이미지 캡처
  📋 Clipboard  — 이미지 경로 + 링크 클립보드 복사

Usage:
  python spy_report.py                    # 세션 자동 감지
  python spy_report.py --session pre      # 프리마켓 강제
  python spy_report.py --session mid      # 미드데이 강제
  python spy_report.py --session post     # 데일리 리캡 강제
  python spy_report.py --no-email
  python spy_report.py --no-imessage
  python spy_report.py --no-deploy
"""

import argparse, json, os, platform, smtplib, ssl, subprocess, sys, webbrowser
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(exist_ok=True)
ET = ZoneInfo("America/New_York")

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def log(msg):
    ts = datetime.now(ET).strftime("%H:%M:%S")
    print(f"  [{ts}] {msg}")


# ══════════════════════════════════
#  1. SAVE HTML
# ══════════════════════════════════

def save_html(html, session):
    ts = datetime.now(ET).strftime("%Y%m%d_%H%M")
    filename = f"spy_{session}_{ts}.html"
    path = REPORT_DIR / filename
    path.write_text(html, encoding="utf-8")
    latest = REPORT_DIR / "latest.html"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    latest.symlink_to(path.name)
    log(f"💾 HTML 저장: {path.name}")
    return path


# ══════════════════════════════════
#  2. GMAIL
# ══════════════════════════════════

def send_email(config, subject, html):
    ec = config.get("email", {})
    if not ec.get("enabled"):
        log("📧 이메일 비활성화 — 스킵")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = ec["sender"]
        msg["To"] = ec["recipient"]
        msg.attach(MIMEText(html, "html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP(ec["smtp_server"], ec["smtp_port"]) as s:
            s.starttls(context=ctx)
            s.login(ec["sender"], ec["app_password"])
            s.sendmail(ec["sender"], ec["recipient"], msg.as_string())
        log(f"📧 이메일 발송 → {ec['recipient']}")
    except Exception as e:
        log(f"📧 이메일 실패: {e}")


# ══════════════════════════════════
#  3. iMESSAGE (macOS)
# ══════════════════════════════════

def send_imessage(config, text):
    ic = config.get("imessage", {})
    if not ic.get("enabled"):
        log("💬 iMessage 비활성화 — 스킵")
        return
    if platform.system() != "Darwin":
        log("💬 iMessage는 macOS만 지원")
        return
    try:
        phone = ic["phone"]
        escaped = text.replace('\\', '\\\\').replace('"', '\\"')
        script = f'''tell application "Messages"
            set targetService to 1st account whose service type = iMessage
            set targetBuddy to participant "{phone}" of targetService
            send "{escaped}" to targetBuddy
        end tell'''
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        log(f"💬 iMessage 발송 → {phone}")
    except Exception as e:
        log(f"💬 iMessage 실패: {e}")


# ══════════════════════════════════
#  4. SCREENSHOT (카톡용 이미지)
# ══════════════════════════════════

def take_screenshot(html_path):
    """Playwright로 HTML → PNG 캡처"""
    png_path = html_path.with_suffix(".png")
    try:
        # Playwright 우선 시도
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 720, "height": 1280})
            page.goto(f"file://{html_path.resolve()}")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(png_path), full_page=True)
            browser.close()
        log(f"📸 스크린샷 생성: {png_path.name}")
        return png_path
    except ImportError:
        pass

    # Fallback: wkhtmltoimage
    try:
        subprocess.run([
            "wkhtmltoimage", "--width", "720", "--quality", "90",
            str(html_path), str(png_path)
        ], check=True, capture_output=True)
        log(f"📸 스크린샷 생성 (wkhtmltoimage): {png_path.name}")
        return png_path
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    log("📸 스크린샷 도구 없음 — pip install playwright && playwright install chromium")
    return None


# ══════════════════════════════════
#  5. GITHUB PAGES 배포
# ══════════════════════════════════

def deploy_github_pages(config, html_path, session):
    """GitHub Pages 리포에 HTML 자동 푸시"""
    gp = config.get("github_pages", {})
    if not gp.get("enabled"):
        log("🔗 GitHub Pages 비활성화 — 스킵")
        return None

    repo_path = Path(gp["repo_path"]).expanduser()
    base_url = gp.get("base_url", "")
    ts = datetime.now(ET).strftime("%Y%m%d_%H%M")

    try:
        # 리포 없으면 클론
        if not (repo_path / ".git").exists():
            repo_url = gp.get("repo_url", "")
            if repo_url:
                subprocess.run(["git", "clone", repo_url, str(repo_path)],
                               check=True, capture_output=True)
                log(f"🔗 리포 클론: {repo_path}")
            else:
                repo_path.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "init"], cwd=str(repo_path),
                               check=True, capture_output=True)

        # HTML 복사
        import shutil

        # index.html = 항상 최신
        shutil.copy2(str(html_path), str(repo_path / "index.html"))

        # 세션별 최신 파일
        session_file = f"{session}.html"
        shutil.copy2(str(html_path), str(repo_path / session_file))

        # 아카이브
        archive_dir = repo_path / "archive"
        archive_dir.mkdir(exist_ok=True)
        archive_name = f"spy_{session}_{ts}.html"
        shutil.copy2(str(html_path), str(archive_dir / archive_name))

        # 스크린샷도 복사
        png = html_path.with_suffix(".png")
        if png.exists():
            shutil.copy2(str(png), str(repo_path / f"{session}.png"))
            shutil.copy2(str(png), str(repo_path / "latest.png"))

        # Git push
        cmds = [
            ["git", "add", "-A"],
            ["git", "commit", "-m", f"SPY {session} report {ts}"],
            ["git", "push", "origin", "main"],
        ]
        for cmd in cmds:
            subprocess.run(cmd, cwd=str(repo_path), capture_output=True)

        report_url = f"{base_url}/{session_file}" if base_url else ""
        log(f"🔗 GitHub Pages 배포 완료: {report_url}")
        return report_url

    except Exception as e:
        log(f"🔗 GitHub Pages 실패: {e}")
        return None


# ══════════════════════════════════
#  6. CLIPBOARD (카톡 공유 준비)
# ══════════════════════════════════

def copy_to_clipboard_mac(text):
    """macOS 클립보드에 텍스트 복사"""
    if platform.system() != "Darwin":
        return
    try:
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
    except Exception:
        pass


def send_kakao_ready(config, png_path, report_url, data):
    """카톡 공유 준비 — 클립보드 + 알림"""
    if not config.get("kakao_clipboard"):
        return

    if platform.system() != "Darwin":
        log("📋 클립보드 기능은 macOS만 지원")
        return

    p = data["price"]
    comp = data.get("composite", {})
    act = comp.get("action", {})
    session_kr = {"pre": "프리마켓", "mid": "미드데이", "post": "데일리 리캡"}.get(data["session"], "리포트")

    # 카톡에 보낼 텍스트 구성
    s = "+" if p["chg"] > 0 else ""
    kakao_text = f"""📊 SPY {session_kr} — {data['timestamp']}

SPY ${p['last']} ({s}{p['chg_pct']}%)
📍 Action: {act.get('direction', '-')} ({act.get('confidence', '-')})
🎯 Entry: {act.get('entry', '-')}
✅ TP: {act.get('target', '-')}
🛑 SL: {act.get('stop', '-')}

📈 풀 리포트: {report_url or '(링크 미설정)'}"""

    copy_to_clipboard_mac(kakao_text)
    log(f"📋 카톡 텍스트 클립보드 복사 완료")

    # macOS 알림
    try:
        img_note = f"이미지: {png_path}" if png_path else "이미지 없음"
        notif_script = f'''display notification "클립보드에 복사됨 — 카톡에 붙여넣기 하세요\\n{img_note}" with title "SPY Report 준비완료" sound name "Glass"'''
        subprocess.run(["osascript", "-e", notif_script], capture_output=True)
        log("🔔 macOS 알림 발송")
    except Exception:
        pass

    # Finder에서 이미지 보여주기 (카톡에 드래그용)
    if png_path and png_path.exists():
        try:
            subprocess.run(["open", "-R", str(png_path)], capture_output=True)
            log(f"📂 Finder에서 이미지 열림 → 카톡에 드래그하세요")
        except Exception:
            pass


# ══════════════════════════════════
#  MAIN
# ══════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="SPY Auto Report")
    parser.add_argument("--session", choices=["pre", "mid", "post"])
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--no-imessage", action="store_true")
    parser.add_argument("--no-deploy", action="store_true")
    parser.add_argument("--no-kakao", action="store_true")
    args = parser.parse_args()

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║     SPY AUTO REPORT ENGINE v3        ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    config = load_config()
    log("⚙️  Config 로드")

    # 1. Fetch data
    log("📡 데이터 수집 중...")
    from spy_engine import fetch_all, SESSION_LABELS
    data = fetch_all()
    if args.session:
        data["session"] = args.session
    session = data["session"]
    log(f"📊 세션: {SESSION_LABELS[session]}")

    # 2. Generate HTML
    log("🎨 리포트 생성 중...")
    from spy_template import generate_html, generate_imessage_summary
    html = generate_html(data)
    imsg_text = generate_imessage_summary(data)

    # 3. Save HTML
    html_path = save_html(html, session)

    # 4. Screenshot
    png_path = None
    if config.get("screenshot"):
        png_path = take_screenshot(html_path)

    # 5. GitHub Pages
    report_url = None
    if not args.no_deploy:
        report_url = deploy_github_pages(config, html_path, session)

    # 6. Email (Gmail 최적화 템플릿 사용)
    if not args.no_email:
        p = data["price"]
        comp = data.get("composite", {})
        act = comp.get("action", {}).get("direction", "")
        subj = f"SPY {SESSION_LABELS[session]} — ${p['last']} ({act})"
        from spy_email_template import generate_email_html
        email_html = generate_email_html(data, full_report_url=report_url or "")
        send_email(config, subj, email_html)

    # 7. iMessage
    if not args.no_imessage:
        send_imessage(config, imsg_text)

    # 8. KakaoTalk prep
    if not args.no_kakao:
        send_kakao_ready(config, png_path, report_url, data)

    # Summary
    p = data["price"]
    comp = data.get("composite", {})
    act = comp.get("action", {})
    print()
    print("  ┌─────────────────────────────────────┐")
    print(f"  │ SPY ${p['last']}  {'+' if p['chg']>0 else ''}{p['chg_pct']}%")
    print(f"  │ Signal: {data['signal']}")
    print(f"  │ Action: {act.get('direction','-')} ({act.get('confidence','-')})")
    print(f"  │ RSI: {data['indicators']['RSI (14)']['value']}  VIX: {data['extras'].get('vix','N/A')}")
    if report_url:
        print(f"  │ 🔗 {report_url}")
    print("  └─────────────────────────────────────┘")
    print()
    log("✅ 완료!")
    print()


if __name__ == "__main__":
    main()
