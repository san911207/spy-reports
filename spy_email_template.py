"""spy_email_template.py — Gmail 풀 리포트 (table 기반, 모바일 최적화)
   모든 내용 포함 + Gmail/Outlook/Apple Mail 완벽 호환
"""
from spy_engine import SESSION_LABELS

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
def badge_html(text):
    c = sig_clr(text)
    return f'<span style="background:{c}15;color:{c};padding:2px 8px;border-radius:8px;font-size:11px;font-weight:700">{text}</span>'

def divider():
    return '<tr><td style="padding:12px 0"><div style="height:1px;background:#DDD5C5"></div></td></tr>'

def section_title(text):
    return f'<tr><td style="font-size:16px;font-weight:800;color:#0f172a;padding:16px 0 10px;border-bottom:2px solid #DDD5C5">{text}</td></tr>'

def note_box(text):
    return f'<tr><td style="padding:8px 0 0"><div style="font-size:12px;color:#94a3b8;line-height:1.6;padding:10px 14px;background:#F0EBE1;border-radius:8px;border-left:3px solid #C9B99A">{text}</div></td></tr>'

def metric_cell(label, value, sub="", val_color="#0f172a"):
    return f'''<td style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;padding:12px 14px;text-align:center">
        <div style="font-size:10px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.3px">{label}</div>
        <div style="font-size:20px;font-weight:800;color:{val_color};margin-top:4px">{value}</div>
        <div style="font-size:11px;color:#94a3b8;margin-top:2px">{sub}</div></td>'''


def generate_email_html(data: dict, full_report_url: str = "") -> str:
    p = data["price"]; ath = data["ath"]; vol = data["volume"]; ma = data["ma"]
    ms = data["ma_summary"]; ind = data["indicators"]; lvl = data["levels"]
    ext = data["extras"]; bb = data["bollinger"]; sig = data["signal"]
    comp = data.get("composite", {}); act = comp.get("action", {})
    st = comp.get("short_term", {}); mt = comp.get("mid_term", {})
    session = data["session"]; ts = data["timestamp"]

    chg_c = clr(p["chg"]); act_dir = act.get("direction", "WAIT")
    act_c = sig_clr(act_dir); st_c = sig_clr(st.get("signal", ""))
    mt_c = sig_clr(mt.get("signal", ""))
    session_kr = SESSION_LABELS.get(session, "📊")
    vwap = data.get("vwap", 0)

    # ── Warnings ──
    warns = "".join(f'<div style="font-size:12px;color:#92400e;padding:2px 0">{w}</div>' for w in act.get("warnings", []))
    warn_block = f'<div style="background:#FEF3C7;border-radius:8px;margin-top:10px;padding:10px 12px;border-left:3px solid #D97706">{warns}</div>' if warns else ""

    # ── MA rows ──
    ma_rows = ""
    for name, val in ma.items():
        s = "매수" if p["last"] > val else "매도"
        s_c = "#16a34a" if s == "매수" else "#dc2626"
        ma_rows += f'''<tr>
            <td style="padding:8px 0;border-bottom:1px solid #EBE5D9;font-size:13px;color:#64748b;font-weight:500">{name}</td>
            <td style="padding:8px 0;border-bottom:1px solid #EBE5D9;text-align:right;font-weight:700;color:{s_c};font-size:14px">${val}</td>
            <td style="padding:8px 0;border-bottom:1px solid #EBE5D9;text-align:right">{badge_html(s)}</td></tr>'''

    # ── Indicator rows ──
    ind_rows = ""
    for name, info in ind.items():
        if info.get("signal"):
            ind_rows += f'''<tr>
                <td style="padding:8px 0;border-bottom:1px solid #EBE5D9;font-size:13px;color:#64748b">{name}</td>
                <td style="padding:8px 0;border-bottom:1px solid #EBE5D9;text-align:center;font-weight:700;color:{sig_clr(info["signal"])};font-size:14px">{info["value"]}</td>
                <td style="padding:8px 0;border-bottom:1px solid #EBE5D9;text-align:right">{badge_html(info["signal"])}</td></tr>'''

    # ── S/R rows ──
    def sr_rows(levels, color):
        rows = ""
        for l in levels:
            rows += f'<tr><td style="padding:7px 0;border-bottom:1px solid #EBE5D9;font-size:13px;color:#475569">{l["label"]}</td><td style="padding:7px 0;border-bottom:1px solid #EBE5D9;text-align:right;font-weight:700;color:{color};font-size:14px">${l["price"]}</td></tr>'
        return rows

    # ── Recent rows ──
    recent_rows = ""
    for r in data.get("recent", []):
        rc = clr(r["chg_pct"])
        recent_rows += f'''<tr>
            <td style="padding:6px 0;border-bottom:1px solid #EBE5D9;font-size:13px;color:#64748b">{r["date"]}</td>
            <td style="padding:6px 0;border-bottom:1px solid #EBE5D9;text-align:center;font-weight:600;font-size:13px">${r["close"]}</td>
            <td style="padding:6px 0;border-bottom:1px solid #EBE5D9;text-align:center;font-weight:600;color:{rc};font-size:13px">{sign(r["chg_pct"])}{r["chg_pct"]}%</td>
            <td style="padding:6px 0;border-bottom:1px solid #EBE5D9;text-align:right;color:#94a3b8;font-size:12px">{r["vol"]//1000000}M</td></tr>'''

    # ── Scenarios ──
    scenarios = data.get("scenarios", [
        {"pct":45,"label":"Bear case","target":"$610 테스트","color":"#dc2626","points":["호르무즈 봉쇄 지속 → 유가 $120+ → 인플레 재점화","트럼프 4/6 이란 공격 유예 만료 → 리스크오프","$628 이탈 시 $610, worst case $600"]},
        {"pct":35,"label":"Base case","target":"$628-650","color":"#d97706","points":["이란-미국 협상 진전 → VIX 하락 → 과매도 반등","$645-650 저항까지 dead cat bounce 후 재하락","헤드라인 주도 레인지 바운드"]},
        {"pct":20,"label":"Bull case","target":"$672+","color":"#16a34a","points":["이란 전쟁 조기 종결 → 유가 급락 → 릴리프 랠리","SMA 50 ($652) 돌파 시 추세 전환"]},
    ])
    scen_html = ""
    for sc in scenarios:
        pts = "<br>".join(f"· {pt}" for pt in sc["points"])
        scen_html += f'''<tr><td style="padding:6px 0">
            <div style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;border-left:4px solid {sc["color"]};padding:14px 16px">
                <span style="font-size:20px;font-weight:800;color:{sc["color"]}">{sc["pct"]}%</span>
                <span style="font-size:14px;font-weight:700;color:#1e293b;margin-left:8px">{sc["label"]} — {sc["target"]}</span>
                <div style="font-size:12px;color:#475569;line-height:1.7;margin-top:8px">{pts}</div>
            </div></td></tr>'''

    # ── Catalysts ──
    catalysts = data.get("catalysts", [
        {"date":"Apr 6","event":"트럼프 이란 에너지시설 공격 유예 만료","impact":"CRITICAL"},
        {"date":"Apr 10","event":"CPI 발표","impact":"HIGH"},
        {"date":"Mid-Apr","event":"호르무즈 봉쇄 티핑포인트","impact":"CRITICAL"},
    ])
    cat_rows = ""
    for cat in catalysts:
        imp_c = {"CRITICAL":"#dc2626","HIGH":"#d97706","MEDIUM":"#3b82f6"}.get(cat.get("impact",""),"#6b7280")
        cat_rows += f'<tr><td style="padding:7px 0;border-bottom:1px solid #EBE5D9;font-weight:600;font-size:13px;color:#1e293b">{cat["date"]}</td><td style="padding:7px 0;border-bottom:1px solid #EBE5D9;font-size:13px;color:#475569">{cat["event"]}</td><td style="padding:7px 0;border-bottom:1px solid #EBE5D9;text-align:right"><span style="font-weight:700;color:{imp_c};font-size:11px;background:{imp_c}10;padding:2px 6px;border-radius:4px">{cat["impact"]}</span></td></tr>'

    # ── Link button ──
    link_btn = ""
    if full_report_url:
        link_btn = f'''<tr><td style="padding:16px 0" align="center">
            <a href="{full_report_url}" style="display:inline-block;background:#1e293b;color:#ffffff;padding:12px 32px;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none">🔗 웹에서 풀 리포트 보기</a></td></tr>'''

    # ══════════════════════════
    #  FULL EMAIL HTML
    # ══════════════════════════
    # After-hours / Pre-market line for email
    ah_email = ""
    if p.get("after_hours") and p["after_hours"] > 0:
        ahc = clr(p["ah_chg"])
        ah_email = f'<div style="font-size:13px;margin-top:6px"><span style="color:#94a3b8;font-weight:700">After-hours</span>&nbsp; <span style="font-weight:800;color:{ahc}">${p["after_hours"]}</span> <span style="color:{ahc}">{sign(p["ah_chg"])}{p["ah_chg"]} ({sign(p["ah_chg_pct"])}{p["ah_chg_pct"]}%)</span></div>'
    if p.get("pre_market") and p["pre_market"] > 0:
        pmc = clr(p["pm_chg"])
        ah_email = f'<div style="font-size:13px;margin-top:6px"><span style="color:#94a3b8;font-weight:700">Pre-market</span>&nbsp; <span style="font-weight:800;color:{pmc}">${p["pre_market"]}</span> <span style="color:{pmc}">{sign(p["pm_chg"])}{p["pm_chg"]} ({sign(p["pm_chg_pct"])}{p["pm_chg_pct"]}%)</span></div>'

    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F5F0E8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;-webkit-text-size-adjust:100%">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:540px;margin:0 auto;padding:16px">

<!-- HEADER -->
<tr><td>
    <div style="display:inline-block;font-size:11px;font-weight:700;color:#64748b;background:#EBE5D9;padding:3px 12px;border-radius:10px">{session_kr} · {ts}</div>
    <table width="100%" style="margin-top:10px"><tr>
        <td style="font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:1px;vertical-align:bottom;width:35px;padding-bottom:6px">SPY</td>
        <td style="font-size:34px;font-weight:900;color:#0f172a;letter-spacing:-1px">${p["last"]}</td>
        <td style="font-size:15px;font-weight:700;color:{chg_c};vertical-align:bottom;padding-bottom:6px">&nbsp;{sign(p["chg"])}{p["chg"]} ({sign(p["chg_pct"])}{p["chg_pct"]}%)</td>
    </tr></table>
    {ah_email}
    <div style="font-size:11px;color:#94a3b8;margin-top:2px">Range ${p["low"]}—${p["high"]} · ATH ${ath["price"]} ({ath["date"]}) · ATH 대비 {ath["pct"]}%</div>
</td></tr>

{divider()}

<!-- ACTION CARD -->
{section_title("📍 Today's action")}
<tr><td style="padding:8px 0">
    <table width="100%" style="background:#FFFDF9;border-radius:10px;border:2px solid {act_c}25;border-collapse:separate">
    <tr><td style="padding:16px">
        <table width="100%"><tr>
            <td style="font-size:11px;color:#94a3b8;font-weight:600">TODAY'S ACTION</td>
            <td align="right">{badge_html("확신도: "+act.get("confidence","-"))}</td>
        </tr></table>
        <div style="font-size:28px;font-weight:900;color:{act_c};margin:8px 0">{act_dir}</div>
        <div style="font-size:13px;color:#475569;margin-bottom:12px">{act.get("description","")}</div>
        <table width="100%" cellspacing="6" style="border-collapse:separate"><tr>
            <td width="25%" style="background:#F5F0E8;border-radius:6px;padding:8px 4px;text-align:center"><div style="font-size:10px;color:#94a3b8;font-weight:600">ENTRY</div><div style="font-size:12px;font-weight:700;margin-top:2px">{act.get("entry","-")}</div></td>
            <td width="25%" style="background:#F5F0E8;border-radius:6px;padding:8px 4px;text-align:center"><div style="font-size:10px;color:#94a3b8;font-weight:600">TARGET</div><div style="font-size:12px;font-weight:700;color:#16a34a;margin-top:2px">{act.get("target","-")}</div></td>
            <td width="25%" style="background:#F5F0E8;border-radius:6px;padding:8px 4px;text-align:center"><div style="font-size:10px;color:#94a3b8;font-weight:600">STOP</div><div style="font-size:12px;font-weight:700;color:#dc2626;margin-top:2px">{act.get("stop","-")}</div></td>
            <td width="25%" style="background:#F5F0E8;border-radius:6px;padding:8px 4px;text-align:center"><div style="font-size:10px;color:#94a3b8;font-weight:600">SIZE</div><div style="font-size:12px;font-weight:700;margin-top:2px">{act.get("sizing","-")}</div></td>
        </tr></table>
        {warn_block}
    </td></tr></table>
</td></tr>

{divider()}

<!-- COMPOSITE SIGNAL -->
{section_title("📊 Composite signal")}
<tr><td style="padding:8px 0">
    <table width="100%" cellspacing="8" style="border-collapse:separate"><tr>
        <td width="50%" style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;padding:14px;text-align:center">
            <div style="font-size:10px;color:#94a3b8;font-weight:600">단기 (1-5일)</div>
            <div style="font-size:22px;font-weight:800;color:{st_c};margin:4px 0">{st.get("signal","—")}</div>
            <div style="font-size:11px;color:#94a3b8">score {st.get("score",0)}</div>
            <div style="font-size:11px;color:#64748b;margin-top:4px">{" · ".join(st.get("drivers",[]))}</div></td>
        <td width="50%" style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;padding:14px;text-align:center">
            <div style="font-size:10px;color:#94a3b8;font-weight:600">중기 (1-4주)</div>
            <div style="font-size:22px;font-weight:800;color:{mt_c};margin:4px 0">{mt.get("signal","—")}</div>
            <div style="font-size:11px;color:#94a3b8">score {mt.get("score",0)}</div>
            <div style="font-size:11px;color:#64748b;margin-top:4px">{" · ".join(mt.get("drivers",[]))}</div></td>
    </tr></table>
</td></tr>

{divider()}

<!-- PRICE SNAPSHOT -->
{section_title("💰 Price snapshot")}
<tr><td style="padding:8px 0">
    <table width="100%" cellspacing="6" style="border-collapse:separate"><tr>
        {metric_cell("종가", f"${p['last']}", f"{sign(p['chg_pct'])}{p['chg_pct']}%", chg_c)}
        {metric_cell("ATH 대비", f"{ath['pct']}%", f"ATH ${ath['price']}", "#dc2626")}
    </tr><tr>
        {metric_cell("거래량", f"{vol['current']//1000000}M", f"{vol['ratio']}x avg")}
        {metric_cell("VIX", f"{ext.get('vix',0)}", f"{sign(ext.get('vix_chg',0))}{ext.get('vix_chg',0)}%", clr(-ext.get('vix_chg',0)))}
    </tr></table>
</td></tr>

{divider()}

<!-- MARKET OVERVIEW -->
{section_title("🌍 Market overview")}
<tr><td style="padding:8px 0">
    <table width="100%" cellspacing="6" style="border-collapse:separate"><tr>
        {metric_cell("WTI 원유", f"${ext.get('oil',0)}", f"{sign(ext.get('oil_chg',0))}{ext.get('oil_chg',0)}%", clr(ext.get('oil_chg',0)))}
        {metric_cell("Gold", f"${ext.get('gold',0)}", f"{sign(ext.get('gold_chg',0))}{ext.get('gold_chg',0)}%", clr(ext.get('gold_chg',0)))}
        {metric_cell("10Y 금리", f"{ext.get('us10y',0)}%", f"{sign(ext.get('us10y_chg',0))}{ext.get('us10y_chg',0)}%", clr(ext.get('us10y_chg',0)))}
    </tr></table>
</td></tr>

{divider()}

<!-- MOVING AVERAGES -->
{section_title("📉 Moving averages — " + ("전 구간 매도" if ms["sell"]==len(ma) else f'{ms["sell"]}S / {ms["buy"]}B'))}
<tr><td style="padding:8px 0">
    <table width="100%" style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;border-collapse:separate">
    <tr><td style="padding:12px 16px"><table width="100%">{ma_rows}</table></td></tr></table>
</td></tr>
{note_box(f"현재가 5일선~200일선 <b style='color:#dc2626'>전부 하회</b> — {ms['sell']}/{ms['sell']+ms['buy']} MA Sell. {ms['cross']} 진행 중.")}

{divider()}

<!-- INDICATORS -->
{section_title("🔬 Key indicators")}
<tr><td style="padding:8px 0">
    <table width="100%" style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;border-collapse:separate">
    <tr><td style="padding:12px 16px"><table width="100%">{ind_rows}</table></td></tr></table>
</td></tr>

{divider()}

<!-- S/R -->
{section_title("🎯 Support / Resistance")}
<tr><td style="padding:8px 0">
    <table width="100%" cellspacing="8" style="border-collapse:separate"><tr>
        <td width="50%" valign="top" style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;padding:12px 14px">
            <div style="font-size:11px;font-weight:700;color:#dc2626;margin-bottom:6px">▲ RESISTANCE</div>
            <table width="100%">{sr_rows(sorted(lvl["resistance"], key=lambda x:-x["price"]), "#dc2626")}</table></td>
        <td width="50%" valign="top" style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;padding:12px 14px">
            <div style="font-size:11px;font-weight:700;color:#16a34a;margin-bottom:6px">▼ SUPPORT</div>
            <table width="100%">{sr_rows(sorted(lvl["support"], key=lambda x:-x["price"]), "#16a34a")}</table></td>
    </tr></table>
</td></tr>

{divider()}

<!-- SCENARIOS -->
{section_title("🔮 Forward scenarios — 향후 1~4주")}
{scen_html}

{divider()}

<!-- CATALYSTS -->
{section_title("📅 Catalyst calendar")}
<tr><td style="padding:8px 0">
    <table width="100%" style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;border-collapse:separate">
    <tr><td style="padding:12px 14px"><table width="100%">{cat_rows}</table></td></tr></table>
</td></tr>

{divider()}

<!-- RECENT 5 DAYS -->
{section_title("📅 Recent 5 days")}
<tr><td style="padding:8px 0">
    <table width="100%" style="background:#FFFDF9;border-radius:10px;border:1px solid #E8E0D0;border-collapse:separate">
    <tr><td style="padding:12px 14px">
        <table width="100%">
        <tr><td style="font-size:10px;color:#94a3b8;font-weight:600;padding-bottom:6px;border-bottom:1px solid #DDD5C5">날짜</td>
            <td style="font-size:10px;color:#94a3b8;font-weight:600;padding-bottom:6px;border-bottom:1px solid #DDD5C5;text-align:center">종가</td>
            <td style="font-size:10px;color:#94a3b8;font-weight:600;padding-bottom:6px;border-bottom:1px solid #DDD5C5;text-align:center">변동</td>
            <td style="font-size:10px;color:#94a3b8;font-weight:600;padding-bottom:6px;border-bottom:1px solid #DDD5C5;text-align:right">거래량</td></tr>
        {recent_rows}</table>
    </td></tr></table>
</td></tr>

{link_btn}

<!-- FOOTER -->
<tr><td style="text-align:center;padding:20px 0;font-size:11px;color:#94a3b8">
    <div style="font-weight:600">SPY Auto Report</div>
    <div style="margin-top:4px">Generated {ts} · 본 리포트는 정보 제공 목적이며 투자 조언이 아닙니다</div>
</td></tr>

</table></body></html>'''
