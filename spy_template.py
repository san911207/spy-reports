"""spy_template.py — 세션별 3종 리포트 템플릿 (v3)
   pre  : 09:00 프리마켓 브리핑
   mid  : 12:30 미드데이 체크
   post : 21:00 데일리 리캡
"""
from spy_engine import SESSION_LABELS

# ══════════════════════════════════
#  SHARED DESIGN SYSTEM
# ══════════════════════════════════

SHARED_CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#F5F0E8;color:#1e293b;font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.w{max-width:680px;margin:0 auto;padding:24px 20px}
.hdr{padding:28px 0 20px}
.sb{display:inline-block;font-size:12px;font-weight:700;color:#64748b;background:#EBE5D9;padding:4px 14px;border-radius:20px;margin-bottom:16px}
.tr{display:flex;align-items:baseline;gap:14px;margin-bottom:2px}
.tk{font-size:13px;font-weight:700;color:#94a3b8;letter-spacing:1px}
.pr{font-size:38px;font-weight:900;color:#0f172a;letter-spacing:-1.5px}
.ch{font-size:16px;font-weight:700}
.si{font-size:12px;color:#94a3b8;margin-top:4px}
.sec{margin-bottom:28px}
.st{font-size:16px;font-weight:800;color:#0f172a;margin-bottom:14px;padding-bottom:10px;border-bottom:2px solid #DDD5C5}
.sn{font-size:12px;color:#94a3b8;line-height:1.6;margin-top:10px;padding:10px 14px;background:#F0EBE1;border-radius:8px;border-left:3px solid #C9B99A}
.cd{background:#FFFDF9;border-radius:12px;padding:16px 18px;border:1px solid #E8E0D0;box-shadow:0 1px 3px rgba(120,100,60,0.06)}
.cd .lb{font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px}
.cd .vl{font-size:24px;font-weight:800;letter-spacing:-0.5px}
.cd .su{font-size:11px;color:#94a3b8;margin-top:2px}
.sc{background:#FFFDF9;border-radius:12px;padding:18px 22px;border:1px solid #E8E0D0;box-shadow:0 1px 3px rgba(120,100,60,0.06);text-align:center}
.sc .lb{font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px}
.sc .sg{font-size:20px;font-weight:800}
.sc .ds{font-size:11px;color:#94a3b8;margin-top:4px}
.dv{height:1px;background:#DDD5C5;margin:24px 0}
.ft{text-align:center;padding:20px 0;font-size:11px;color:#94a3b8}
.warn-box{margin-top:12px;padding:10px 14px;background:#FEF3C7;border-radius:8px;border-left:3px solid #D97706}
.warn-item{font-size:12px;color:#92400e;margin-bottom:3px}
@media(max-width:600px){.g4{grid-template-columns:repeat(2,1fr)!important}.g5{grid-template-columns:repeat(2,1fr)!important}.pr{font-size:30px}}
'''

# ── Shared helpers ──
def clr(v):
    if v > 0: return "#16a34a"
    if v < 0: return "#dc2626"
    return "#6b7280"

def sign(v): return "+" if v > 0 else ""

def sig_clr(s):
    s = s.lower()
    if "sell" in s or "매도" in s or "과매도" in s or "put" in s: return "#dc2626"
    if "buy" in s or "매수" in s or "과매수" in s or "call" in s: return "#16a34a"
    return "#d97706"

def badge(text):
    c = sig_clr(text)
    return f'<span style="background:{c}12;color:{c};padding:2px 10px;border-radius:10px;font-size:11px;font-weight:600;border:1px solid {c}25">{text}</span>'

def score_dots(score, max_s=5):
    filled = min(abs(round(score)), 5)
    c = "#dc2626" if score < 0 else "#16a34a"
    dots = ""
    for i in range(5):
        bg = c if i < filled else "#DDD5C5"
        dots += f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{bg};margin:0 2px"></span>'
    return dots

def header_html(data):
    p = data["price"]; ath = data["ath"]; ts = data["timestamp"]
    session = data["session"]; chg_c = clr(p["chg"])
    label = SESSION_LABELS.get(session, "📊")

    # 애프터마켓 / 프리마켓 라인
    ah_line = ""
    if p.get("after_hours") and p["after_hours"] > 0:
        ahc = clr(p["ah_chg"])
        ah_line = f'<div style="font-size:13px;margin-top:4px"><span style="color:#94a3b8;font-weight:600">After-hours</span> <span style="font-weight:800;color:{ahc}">${p["after_hours"]}</span> <span style="color:{ahc};font-size:12px">{sign(p["ah_chg"])}{p["ah_chg"]} ({sign(p["ah_chg_pct"])}{p["ah_chg_pct"]}%)</span></div>'
    if p.get("pre_market") and p["pre_market"] > 0:
        pmc = clr(p["pm_chg"])
        ah_line = f'<div style="font-size:13px;margin-top:4px"><span style="color:#94a3b8;font-weight:600">Pre-market</span> <span style="font-weight:800;color:{pmc}">${p["pre_market"]}</span> <span style="color:{pmc};font-size:12px">{sign(p["pm_chg"])}{p["pm_chg"]} ({sign(p["pm_chg_pct"])}{p["pm_chg_pct"]}%)</span></div>'

    return f'''<div class="hdr">
    <div class="sb">{label} · {ts}</div>
    <div class="tr"><span class="tk">SPY</span><span class="pr">${p["last"]}</span>
        <span class="ch" style="color:{chg_c}">{sign(p["chg"])}{p["chg"]} ({sign(p["chg_pct"])}{p["chg_pct"]}%)</span></div>
    {ah_line}
    <div class="si">Range ${p["low"]} — ${p["high"]} · ATH ${ath["price"]} ({ath["date"]}) · ATH 대비 {ath["pct"]}%</div></div>'''

def footer_html(data):
    ts = data["timestamp"]; session = data["session"]
    labels = {"pre": "Pre-market Briefing", "mid": "Midday Check", "post": "Daily Recap"}
    return f'''<div class="ft"><div style="font-weight:600;margin-bottom:4px">SPY Auto Report — {labels.get(session,"Report")}</div>
    <div>Generated {ts} · 본 리포트는 정보 제공 목적이며 투자 조언이 아닙니다</div></div>'''

def market_overview_html(data):
    ext = data["extras"]
    def card(label, key, pre="", suf=""):
        v = ext.get(key, 0); c = ext.get(f"{key}_chg", 0)
        return f'''<div class="cd" style="text-align:center"><div class="lb">{label}</div>
            <div class="vl" style="font-size:20px">{pre}{v}{suf}</div>
            <div class="su" style="color:{clr(c)}">{sign(c)}{c}%</div></div>'''
    return f'''<div class="sec"><div class="st">Market overview</div>
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px" class="g5">
        {card("VIX","vix")}{card("WTI 원유","oil","$")}{card("ES 선물","es_futures","$")}{card("Gold","gold","$")}{card("10Y 금리","us10y","","%")}
    </div></div>'''

def action_card_html(data):
    comp = data.get("composite", {}); act = comp.get("action", {})
    st = comp.get("short_term", {}); mt = comp.get("mid_term", {})
    act_dir = act.get("direction", "WAIT")
    act_c = "#dc2626" if "PUT" in act_dir else "#16a34a" if "CALL" in act_dir else "#d97706"
    st_c = sig_clr(st.get("signal", ""))
    mt_c = sig_clr(mt.get("signal", ""))
    st_drv = " · ".join(st.get("drivers", []))
    mt_drv = " · ".join(mt.get("drivers", []))
    warns = "".join(f'<div class="warn-item">{w}</div>' for w in act.get("warnings", []))
    warn_box = f'<div class="warn-box">{warns}</div>' if warns else ""
    return f'''
<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:12px">
    <div class="cd"><div class="lb">단기 (1-5일)</div>
        <div style="font-size:24px;font-weight:800;color:{st_c};margin:6px 0">{st.get("signal","—")}</div>
        <div style="margin-bottom:6px">{score_dots(st.get("score",0))}<span style="font-size:11px;color:#94a3b8;margin-left:6px">score {st.get("score",0)}</span></div>
        <div style="font-size:12px;color:#64748b">{st_drv}</div></div>
    <div class="cd"><div class="lb">중기 (1-4주)</div>
        <div style="font-size:24px;font-weight:800;color:{mt_c};margin:6px 0">{mt.get("signal","—")}</div>
        <div style="margin-bottom:6px">{score_dots(mt.get("score",0))}<span style="font-size:11px;color:#94a3b8;margin-left:6px">score {mt.get("score",0)}</span></div>
        <div style="font-size:12px;color:#64748b">{mt_drv}</div></div>
</div>
<div style="background:#FFFDF9;border-radius:12px;padding:20px 24px;border:2px solid {act_c}30;box-shadow:0 1px 3px rgba(120,100,60,0.06)">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
        <div style="font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase">Today&apos;s action</div>
        <div style="font-size:22px;font-weight:900;color:{act_c}">{act_dir}</div>
        <div style="margin-left:auto">{badge("확신도: "+act.get("confidence","-"))}</div></div>
    <div style="font-size:13px;color:#475569;margin-bottom:14px">{act.get("description","")}</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
        <div style="background:#F5F0E8;border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;text-transform:uppercase;margin-bottom:3px">Entry</div>
            <div style="font-size:12px;font-weight:700;color:#1e293b">{act.get("entry","-")}</div></div>
        <div style="background:#F5F0E8;border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;text-transform:uppercase;margin-bottom:3px">Target</div>
            <div style="font-size:12px;font-weight:700;color:#16a34a">{act.get("target","-")}</div></div>
        <div style="background:#F5F0E8;border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;text-transform:uppercase;margin-bottom:3px">Stop</div>
            <div style="font-size:12px;font-weight:700;color:#dc2626">{act.get("stop","-")}</div></div>
        <div style="background:#F5F0E8;border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;text-transform:uppercase;margin-bottom:3px">Size</div>
            <div style="font-size:12px;font-weight:700;color:#1e293b">{act.get("sizing","-")}</div></div>
    </div>{warn_box}</div>'''

def wrap_page(title, ts, body):
    return f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} — {ts}</title><style>{SHARED_CSS}</style></head><body><div class="w">{body}</div></body></html>'''

# ══════════════════════════════════
#  09:00 프리마켓 브리핑
# ══════════════════════════════════

def generate_pre_html(data: dict) -> str:
    """오늘 전쟁터 지도 — 갭 방향 + 플랜 세팅"""
    p = data["price"]; ext = data["extras"]; lvl = data["levels"]
    comp = data.get("composite", {}); act = comp.get("action", {})

    # 선물 갭 계산
    es = ext.get("es_futures", p["last"])
    gap = round(es - p["last"], 2)
    gap_pct = round((gap / p["last"]) * 100, 2)
    gap_dir = "갭업" if gap > 0 else "갭다운" if gap < 0 else "플랫"
    gap_c = clr(gap)

    # 글로벌 마켓 카드
    def g_card(label, key, pre="", suf=""):
        v = ext.get(key, 0); c = ext.get(f"{key}_chg", 0)
        return f'''<div class="cd" style="text-align:center"><div class="lb">{label}</div>
            <div class="vl" style="font-size:18px">{pre}{v}{suf}</div>
            <div class="su" style="color:{clr(c)}">{sign(c)}{c}%</div></div>'''

    # Key levels
    r_list = sorted(lvl.get("resistance", []), key=lambda x: x["price"])
    s_list = sorted(lvl.get("support", []), key=lambda x: -x["price"])

    def level_rows(levels, color):
        rows = ""
        for l in levels[:4]:
            rows += f'''<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #EBE5D9">
                <span style="font-size:13px;color:#475569">{l["label"]}</span>
                <span style="font-weight:700;color:{color};font-size:14px">${l["price"]}</span></div>'''
        return rows

    # 갭 시나리오 3가지
    atr = data["indicators"].get("ATR (14)", {}).get("value", 10)
    near_r = r_list[0]["price"] if r_list else round(p["last"] + atr, 2)
    near_s = s_list[0]["price"] if s_list else round(p["last"] - atr, 2)

    scenarios = f'''
    <div class="cd" style="border-left:4px solid #dc2626;margin-bottom:8px">
        <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:6px">
            <span style="font-weight:800;color:#dc2626;font-size:14px">갭다운</span>
            <span style="font-size:13px;color:#64748b">ES &lt; ${round(p["last"]-3,2)}</span></div>
        <div style="font-size:13px;color:#475569;line-height:1.6">
            ${near_s} 지지 테스트 관찰 → 반등 확인 시 <b style="color:#16a34a">CALL</b> (counter-trend, 1/4 size)<br>
            지지 이탈 시 다음 레벨 ${s_list[1]["price"] if len(s_list)>1 else round(near_s-atr,2)}까지 관망</div></div>
    <div class="cd" style="border-left:4px solid #d97706;margin-bottom:8px">
        <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:6px">
            <span style="font-weight:800;color:#d97706;font-size:14px">플랫 오픈</span>
            <span style="font-size:13px;color:#64748b">ES ≈ ${p["last"]}</span></div>
        <div style="font-size:13px;color:#475569;line-height:1.6">
            09:30~10:00 방향성 확인 후 진입 → VWAP 기준 위/아래 판단<br>
            첫 30분 레인지 상단 돌파 시 방향 추종, 실패 시 <b style="color:#d97706">WAIT</b></div></div>
    <div class="cd" style="border-left:4px solid #16a34a;margin-bottom:8px">
        <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:6px">
            <span style="font-weight:800;color:#16a34a;font-size:14px">갭업</span>
            <span style="font-size:13px;color:#64748b">ES &gt; ${round(p["last"]+3,2)}</span></div>
        <div style="font-size:13px;color:#475569;line-height:1.6">
            ${near_r} 저항 도달 여부 관찰 → 저항 rejection 시 <b style="color:#dc2626">PUT</b><br>
            돌파 + 볼륨 컨펌 시 다음 저항 ${r_list[1]["price"] if len(r_list)>1 else round(near_r+atr,2)}까지 홀드</div></div>'''

    # 오늘 매크로 이벤트
    catalysts = data.get("catalysts", [])
    cat_html = ""
    for cat in catalysts[:3]:
        imp_c = {"CRITICAL":"#dc2626","HIGH":"#d97706","MEDIUM":"#3b82f6"}.get(cat.get("impact",""),"#6b7280")
        cat_html += f'''<div style="display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #EBE5D9;font-size:13px">
            <span style="width:110px;font-weight:600;color:#1e293b">{cat["date"]}</span>
            <span style="flex:1;color:#475569">{cat["event"]}</span>
            <span style="font-weight:700;color:{imp_c};font-size:11px;background:{imp_c}10;padding:2px 8px;border-radius:6px">{cat["impact"]}</span></div>'''

    body = header_html(data)

    # 갭 배너
    body += f'''<div style="background:#FFFDF9;border-radius:12px;padding:16px 20px;border:2px solid {gap_c}30;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 1px 3px rgba(120,100,60,0.06)">
        <div><div style="font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase">ES 선물 (프리마켓)</div>
            <div style="font-size:28px;font-weight:900;color:{gap_c}">{gap_dir} {sign(gap)}${abs(gap)}</div>
            <div style="font-size:12px;color:#94a3b8">ES ${es} vs 어제 종가 ${p["last"]} ({sign(gap_pct)}{gap_pct}%)</div></div>
        <div style="text-align:right"><div style="font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase">VIX</div>
            <div style="font-size:22px;font-weight:800;color:{clr(-ext.get("vix_chg",0))}">{ext.get("vix",0)}</div>
            <div style="font-size:12px;color:{clr(ext.get("vix_chg",0))}">{sign(ext.get("vix_chg",0))}{ext.get("vix_chg",0)}%</div></div></div>'''

    body += '<div class="dv"></div>'

    # 글로벌 마켓
    body += f'''<div class="sec"><div class="st">🌍 오버나이트 글로벌</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px" class="g4">
        {g_card("WTI 원유","oil","$")}{g_card("Gold","gold","$")}{g_card("10Y 금리","us10y","","%")}{g_card("ES 선물","es_futures","$")}
    </div></div><div class="dv"></div>'''

    # Key levels
    body += f'''<div class="sec"><div class="st">🎯 오늘의 Key levels</div>
    <div style="display:flex;gap:16px">
        <div style="flex:1"><div style="font-size:12px;font-weight:700;color:#dc2626;margin-bottom:6px">▲ RESISTANCE</div>
            <div class="cd" style="padding:12px 16px">{level_rows(sorted(r_list, key=lambda x:-x["price"]), "#dc2626")}</div></div>
        <div style="flex:1"><div style="font-size:12px;font-weight:700;color:#16a34a;margin-bottom:6px">▼ SUPPORT</div>
            <div class="cd" style="padding:12px 16px">{level_rows(s_list, "#16a34a")}</div></div>
    </div></div><div class="dv"></div>'''

    # 갭 시나리오
    body += f'''<div class="sec"><div class="st">📋 갭 시나리오별 플랜</div>{scenarios}</div><div class="dv"></div>'''

    # Composite signal + action
    body += f'''<div class="sec"><div class="st">📍 Composite signal + Action</div>{action_card_html(data)}</div>'''

    # 매크로 이벤트 (있을 때만)
    if cat_html:
        body += f'''<div class="dv"></div><div class="sec"><div class="st">📅 오늘 매크로 이벤트</div>
            <div class="cd" style="padding:12px 16px">{cat_html}</div></div>'''

    body += footer_html(data)
    return wrap_page(f"SPY 프리마켓 브리핑", data["timestamp"], body)

# ══════════════════════════════════
#  12:30 미드데이 체크
# ══════════════════════════════════

def generate_mid_html(data: dict) -> str:
    """전투 중간 점검 — 아침 플랜 vs 실제 + 오후 조정"""
    p = data["price"]; vol = data["volume"]; ext = data["extras"]
    comp = data.get("composite", {}); act = comp.get("action", {})

    vwap = data.get("vwap", 0)
    vwap_above = p["last"] > vwap and vwap > 0
    vwap_c = "#16a34a" if vwap_above else "#dc2626"

    # 오전 볼륨 페이스 (12:30 기준으로 하루 볼륨의 ~55% 소화가 정상)
    expected_vol = int(vol["avg20"] * 0.55)
    vol_pace = round(vol["current"] / expected_vol, 2) if expected_vol > 0 else 1.0
    if vol_pace > 1.3:
        vol_label = "과다 (고변동성)"
        vol_c = "#dc2626"
    elif vol_pace < 0.7:
        vol_label = "부족 (저유동성)"
        vol_c = "#d97706"
    else:
        vol_label = "정상"
        vol_c = "#16a34a"

    # 오전 고/저 기반 오후 레벨
    am_high = p["high"]
    am_low = p["low"]
    am_range = round(am_high - am_low, 2)
    atr = data["indicators"].get("ATR (14)", {}).get("value", 10)
    range_used = round((am_range / atr) * 100) if atr else 0

    body = header_html(data)

    # 장중 스코어보드
    body += f'''<div class="sec"><div class="st">📊 장중 스코어보드</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px" class="g4">
        <div class="cd"><div class="lb">현재가</div>
            <div class="vl">${p["last"]}</div>
            <div class="su" style="color:{clr(p["chg"])}">{sign(p["chg_pct"])}{p["chg_pct"]}%</div></div>
        <div class="cd"><div class="lb">장중 레인지</div>
            <div class="vl" style="font-size:20px">${am_low} — ${am_high}</div>
            <div class="su">ATR 소화율 {range_used}%</div></div>
        <div class="cd"><div class="lb">VWAP</div>
            <div class="vl" style="font-size:20px;color:{vwap_c}">{"▲ 상회" if vwap_above else "▼ 하회"}</div>
            <div class="su">${vwap}</div></div>
        <div class="cd"><div class="lb">볼륨 페이스</div>
            <div class="vl" style="font-size:20px;color:{vol_c}">{vol_pace}x</div>
            <div class="su">{vol_label}</div></div>
    </div></div><div class="dv"></div>'''

    # 오전 레인지 시각화
    if atr > 0:
        price_in_range = max(0, min(100, ((p["last"] - am_low) / (am_high - am_low) * 100))) if am_high != am_low else 50
        vwap_in_range = max(0, min(100, ((vwap - am_low) / (am_high - am_low) * 100))) if am_high != am_low and vwap > 0 else -1

        body += f'''<div class="sec"><div class="st">📈 오전 레인지 맵</div>
        <div class="cd" style="padding:20px 22px">
            <div style="display:flex;justify-content:space-between;font-size:12px;color:#94a3b8;margin-bottom:6px">
                <span>Low ${am_low}</span><span>High ${am_high}</span></div>
            <div style="height:12px;background:linear-gradient(to right, #dcfce720, #F5F0E8, #fee2e220);border-radius:6px;position:relative;border:1px solid #E8E0D0">
                {"" if vwap_in_range < 0 else f'<div style="position:absolute;top:-3px;left:{vwap_in_range}%;width:2px;height:18px;background:#6366f1;border-radius:1px" title="VWAP"></div>'}
                <div style="position:absolute;top:-4px;left:{price_in_range}%;width:14px;height:14px;background:#0f172a;border-radius:50%;border:2px solid #fff;transform:translateX(-50%);box-shadow:0 1px 3px rgba(0,0,0,0.2)" title="현재가"></div>
            </div>
            <div style="display:flex;gap:16px;margin-top:8px;font-size:11px;color:#94a3b8">
                <span>● 현재가 ${p["last"]}</span>
                {"" if vwap_in_range < 0 else f'<span style="color:#6366f1">│ VWAP ${vwap}</span>'}
                <span style="margin-left:auto">레인지 ${am_range} (ATR의 {range_used}%)</span></div>
        </div></div><div class="dv"></div>'''

    # 오후 주의사항
    pm_notes = []
    if range_used > 80:
        pm_notes.append("ATR 대부분 소화 — 오후 레인지 축소 가능, 브레이크아웃 확률 낮음")
    elif range_used < 40:
        pm_notes.append("ATR 절반 미만 소화 — 오후 큰 움직임 가능성 (파워아워 주의)")
    if vol_pace > 1.3:
        pm_notes.append("거래량 과다 — 기관 활동 활발, 방향성 무브 가능")
    elif vol_pace < 0.7:
        pm_notes.append("거래량 부족 — 유동성 낮아 스프레드 주의, 0DTE 조심")
    pm_notes.append("3:00-4:00 파워아워 — 최종 방향 결정 구간, 포지션 정리 또는 추종")
    pm_notes.append("0DTE 보유 중이면 3:00 PM 이전 정리 권장")

    notes_html = "".join(f'<div style="margin-bottom:6px;font-size:13px;color:#475569">· {n}</div>' for n in pm_notes)

    body += f'''<div class="sec"><div class="st">⚡ 오후 주의사항</div>
    <div class="cd" style="padding:16px 20px">{notes_html}</div></div><div class="dv"></div>'''

    # Action 업데이트
    body += f'''<div class="sec"><div class="st">📍 Action 업데이트 (오후용)</div>{action_card_html(data)}</div>'''

    # Market overview (간결)
    body += f'<div class="dv"></div>{market_overview_html(data)}'

    body += footer_html(data)
    return wrap_page(f"SPY 미드데이 체크", data["timestamp"], body)

# ══════════════════════════════════
#  21:00 데일리 리캡
# ══════════════════════════════════

def generate_post_html(data: dict) -> str:
    """전투 결과 + 내일 준비 — 풀 테크니컬 리포트"""
    p = data["price"]; ath = data["ath"]; vol = data["volume"]; ma = data["ma"]
    ms = data["ma_summary"]; ind = data["indicators"]; lvl = data["levels"]
    ext = data["extras"]; bb = data["bollinger"]
    vwap = data.get("vwap", 0); vwap_above = p["last"] > vwap and vwap > 0

    # MA rows
    ma_rows = ""
    for name, val in ma.items():
        gap = round(((p["last"] - val) / val) * 100, 2)
        s = "매수" if p["last"] > val else "매도"; s_c = "#16a34a" if s == "매수" else "#dc2626"
        bar_pct = min(abs(gap) * 15, 100)
        ma_rows += f'''<div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #EBE5D9">
            <span style="width:120px;font-size:13px;color:#64748b;font-weight:500">{name}</span>
            <div style="flex:1;height:8px;background:#EBE5D9;border-radius:4px;overflow:hidden">
                <div style="width:{bar_pct}%;height:100%;background:{s_c}35;border-radius:4px"></div></div>
            <span style="width:65px;text-align:right;font-weight:700;color:{s_c};font-size:14px">${val}</span></div>'''

    # Indicator grid
    ind_items = [(k, v) for k, v in ind.items() if v.get("signal")]
    ind_grid = ""
    for i in range(0, len(ind_items), 2):
        left = ind_items[i]
        right = ind_items[i+1] if i+1 < len(ind_items) else None
        def cell(item):
            nm, info = item
            return f'''<div style="flex:1;display:flex;justify-content:space-between;align-items:center;padding:14px 18px;background:#F5F0E8;border-radius:10px;border:1px solid #E8E0D0">
                <span style="font-size:13px;color:#64748b;font-weight:500">{nm}</span>
                <div style="display:flex;align-items:center;gap:8px">
                    <span style="font-weight:700;color:{sig_clr(info["signal"])};font-size:15px">{info["value"]}</span>
                    {badge(info["signal"])}</div></div>'''
        rh = cell(right) if right else '<div style="flex:1"></div>'
        ind_grid += f'<div style="display:flex;gap:10px;margin-bottom:8px">{cell(left)}{rh}</div>'

    # S/R
    def sr_rows(levels, color):
        rows = ""
        for l in levels:
            rows += f'''<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #EBE5D9">
                <span style="font-size:14px;color:#475569">{l["label"]}</span>
                <span style="font-weight:700;color:{color};font-size:15px">${l["price"]}</span></div>'''
        return rows

    # Recent 5 days
    recent_rows = ""
    for r in data.get("recent", []):
        rc = clr(r["chg_pct"])
        recent_rows += f'''<div style="display:flex;padding:8px 0;border-bottom:1px solid #EBE5D9;font-size:13px">
            <span style="flex:1;color:#64748b">{r["date"]}</span>
            <span style="flex:1;text-align:center;font-weight:600">${r["close"]}</span>
            <span style="flex:1;text-align:center;font-weight:600;color:{rc}">{sign(r["chg_pct"])}{r["chg_pct"]}%</span>
            <span style="flex:1;text-align:right;color:#94a3b8">{r["vol"]:,}</span></div>'''

    # Scenarios
    scenarios = data.get("scenarios", [
        {"pct":45,"label":"Bear case","target":"$610 테스트","color":"#dc2626","points":["호르무즈 해협 장기 봉쇄 → 유가 $120+ 유지 → 인플레 재점화 → Fed 금리인하 무산","트럼프 4/6 이란 에너지시설 공격 유예 만료 후 재개 시 → 급격한 리스크오프","$628 이탈 시 $610 직행, worst case $600까지 열림"]},
        {"pct":35,"label":"Base case","target":"$628-650 레인지","color":"#d97706","points":["이란-미국 협상 진전 → VIX 하락 → 과매도 반등","RSI 극단 → 기술적 dead cat bounce $645-650 저항까지 반등 후 재하락","헤드라인 주도 시장에서 레인지 바운드"]},
        {"pct":20,"label":"Bull case","target":"$672+ 회복","color":"#16a34a","points":["이란 전쟁 조기 종결 + 호르무즈 재개방 → 유가 급락 → 릴리프 랠리","SMA 50 돌파 확인 시에만 추세 전환으로 판단"]},
    ])
    scen_html = ""
    for sc in scenarios:
        pts = "".join(f'<div style="margin-bottom:5px">{pt}</div>' for pt in sc["points"])
        scen_html += f'''<div class="cd" style="border-left:4px solid {sc["color"]};margin-bottom:10px">
            <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:8px">
                <span style="font-size:22px;font-weight:800;color:{sc["color"]}">{sc["pct"]}%</span>
                <span style="font-size:15px;font-weight:700;color:#1e293b">{sc["label"]} — {sc["target"]}</span></div>
            <div style="font-size:13px;color:#475569;line-height:1.7">{pts}</div></div>'''

    # Catalysts
    catalysts = data.get("catalysts", [
        {"date":"Apr 6","event":"트럼프 이란 에너지시설 공격 유예 만료","impact":"CRITICAL"},
        {"date":"Apr 10","event":"CPI 발표 (인플레이션)","impact":"HIGH"},
        {"date":"Mid-Apr","event":"호르무즈 봉쇄 티핑포인트","impact":"CRITICAL"},
    ])
    cat_html = ""
    for cat in catalysts:
        imp_c = {"CRITICAL":"#dc2626","HIGH":"#d97706","MEDIUM":"#3b82f6"}.get(cat.get("impact",""),"#6b7280")
        cat_html += f'''<div style="display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #EBE5D9;font-size:13px">
            <span style="width:100px;font-weight:600;color:#1e293b">{cat["date"]}</span>
            <span style="flex:1;color:#475569">{cat["event"]}</span>
            <span style="font-weight:700;color:{imp_c};font-size:11px;background:{imp_c}10;padding:2px 8px;border-radius:6px">{cat["impact"]}</span></div>'''

    # BB position
    bb_pct = max(0, min(100, ((p["last"]-bb["lower"])/(bb["upper"]-bb["lower"])*100) if bb["upper"]!=bb["lower"] else 50))

    # ── Assemble ──
    body = header_html(data)

    # Price snapshot
    body += f'''<div class="sec"><div class="st">Price snapshot — {data["date"]} close</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px" class="g4">
        <div class="cd"><div class="lb">종가</div><div class="vl">${p["last"]}</div><div class="su" style="color:{clr(p["chg"])}">{sign(p["chg_pct"])}{p["chg_pct"]}%</div></div>
        <div class="cd"><div class="lb">ATH 대비</div><div class="vl" style="color:#dc2626">{ath["pct"]}%</div><div class="su">ATH ${ath["price"]}</div></div>
        <div class="cd"><div class="lb">거래량</div><div class="vl">{vol["current"]//1000000}M</div><div class="su">{vol["ratio"]}x avg</div></div>
        <div class="cd"><div class="lb">일일 변동성</div><div class="vl">{p["range_pct"]}%</div><div class="su">${p["range"]}</div></div>
    </div></div><div class="dv"></div>'''

    body += f'{market_overview_html(data)}<div class="dv"></div>'

    # MA
    body += f'''<div class="sec"><div class="st">Moving averages — {"전 구간 매도 시그널" if ms["sell"]==len(ma) else f'{ms["sell"]} Sell / {ms["buy"]} Buy'}</div>
    <div class="cd" style="padding:18px 22px">{ma_rows}</div>
    <div class="sn">현재가가 5일선부터 200일선까지 <b style="color:#dc2626">전부 하회</b> — {ms["sell"]}/{ms["sell"]+ms["buy"]} MA Sell. {ms["cross"]} 진행 중.</div></div><div class="dv"></div>'''

    # Indicators
    body += f'''<div class="sec"><div class="st">Key technical indicators</div>{ind_grid}
    <div class="sn">RSI {ind["RSI (14)"]["value"]} — 극단적 과매도 영역</div></div><div class="dv"></div>'''

    # S/R
    body += f'''<div class="sec"><div class="st">Support / Resistance</div>
    <div style="display:flex;gap:16px">
        <div style="flex:1"><div style="font-size:12px;font-weight:700;color:#dc2626;margin-bottom:6px">▲ RESISTANCE</div>
            <div class="cd" style="padding:12px 16px">{sr_rows(sorted(lvl["resistance"], key=lambda x:-x["price"]), "#dc2626")}</div></div>
        <div style="flex:1"><div style="font-size:12px;font-weight:700;color:#16a34a;margin-bottom:6px">▼ SUPPORT</div>
            <div class="cd" style="padding:12px 16px">{sr_rows(sorted(lvl["support"], key=lambda x:-x["price"]), "#16a34a")}</div></div>
    </div></div><div class="dv"></div>'''

    # Composite
    body += f'''<div class="sec"><div class="st">Composite signal</div>{action_card_html(data)}</div><div class="dv"></div>'''

    # Scenarios
    body += f'''<div class="sec"><div class="st">Forward scenarios — 향후 1~4주</div>{scen_html}</div><div class="dv"></div>'''

    # Catalysts
    body += f'''<div class="sec"><div class="st">Catalyst calendar</div>
    <div class="cd" style="padding:12px 16px">{cat_html}</div></div><div class="dv"></div>'''

    # Recent 5 days
    body += f'''<div class="sec"><div class="st">Recent 5 days</div>
    <div class="cd" style="padding:12px 16px">
        <div style="display:flex;padding:4px 0;border-bottom:1px solid #DDD5C5;font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase">
            <span style="flex:1">날짜</span><span style="flex:1;text-align:center">종가</span><span style="flex:1;text-align:center">변동</span><span style="flex:1;text-align:right">거래량</span></div>
        {recent_rows}</div></div><div class="dv"></div>'''

    # BB + VWAP
    body += f'''<div class="sec"><div class="st">Bollinger Bands &amp; VWAP</div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">
        <div class="cd"><div class="lb">Bollinger Bands (20, 2)</div>
            <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:13px">
                <span style="color:#16a34a">Lower<br><b>${bb["lower"]}</b></span>
                <span style="color:#64748b;font-weight:700">Mid<br><b>${bb["mid"]}</b></span>
                <span style="color:#dc2626">Upper<br><b>${bb["upper"]}</b></span></div>
            <div style="margin-top:10px;height:8px;background:linear-gradient(to right,#dcfce7,#EBE5D9,#fee2e2);border-radius:4px;position:relative">
                <div style="position:absolute;top:-2px;left:{bb_pct}%;width:12px;height:12px;background:#0f172a;border-radius:50%;border:2px solid #fff;transform:translateX(-50%)"></div></div></div>
        <div class="cd"><div class="lb">VWAP Position</div>
            <div class="vl" style="font-size:20px;color:{"#16a34a" if vwap_above else "#dc2626"};margin-top:6px">{"▲ 상회 (강세)" if vwap_above else "▼ 하회 (약세)"}</div>
            <div class="su">VWAP ${vwap} vs ${p["last"]}</div>
            <div style="margin-top:8px;font-size:12px;color:#64748b">Gap: {sign(p["last"]-vwap)}${abs(round(p["last"]-vwap,2))}</div></div>
    </div></div>'''

    body += footer_html(data)
    return wrap_page("SPY 데일리 리캡", data["timestamp"], body)

# ══════════════════════════════════
#  ROUTER + iMessage
# ══════════════════════════════════

def generate_html(data: dict) -> str:
    """세션에 따라 적절한 템플릿 자동 선택"""
    session = data.get("session", "post")
    if session == "pre":
        return generate_pre_html(data)
    elif session == "mid":
        return generate_mid_html(data)
    else:
        return generate_post_html(data)

def generate_imessage_summary(data: dict) -> str:
    p = data["price"]; sig = data["signal"]; ind = data["indicators"]
    ms = data["ma_summary"]; ext = data["extras"]; session = data["session"]
    ts = data["timestamp"]; comp = data.get("composite", {})
    act = comp.get("action", {})
    s = "+" if p["chg"] > 0 else ""
    label = SESSION_LABELS.get(session, "📊")
    act_dir = act.get("direction", "-")

    # AH/PM line
    ah_line = ""
    if p.get("after_hours") and p["after_hours"] > 0:
        ahs = "+" if p["ah_chg"] > 0 else ""
        ah_line = f"🌙 AH: ${p['after_hours']} ({ahs}{p['ah_chg_pct']}%)"
    if p.get("pre_market") and p["pre_market"] > 0:
        pms = "+" if p["pm_chg"] > 0 else ""
        ah_line = f"🌅 PM: ${p['pre_market']} ({pms}{p['pm_chg_pct']}%)"

    lines = [
        f"{label} {ts}", "",
        f"SPY ${p['last']} ({s}{p['chg_pct']}%)",
    ]
    if ah_line:
        lines.append(ah_line)
    lines += [
        f"📍 Action: {act_dir} ({act.get('confidence','-')})",
        f"📊 RSI {ind['RSI (14)']['value']} | MACD {ind['MACD']['value']}",
        f"📉 MA {ms['sell']}S/{ms['buy']}B | {ms['cross']}",
        f"",
        f"🎯 Entry: {act.get('entry','-')}",
        f"✅ TP: {act.get('target','-')}",
        f"🛑 SL: {act.get('stop','-')}",
        f"📏 Size: {act.get('sizing','-')}",
        f"",
        f"🌍 VIX {ext.get('vix',0)} | Oil ${ext.get('oil',0)}",
        f"⚠️ 투자 조언 아님",
    ]
    return "\n".join(lines)
