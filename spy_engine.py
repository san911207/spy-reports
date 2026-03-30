"""spy_engine.py — SPY 데이터 수집 + 기술적 지표 계산"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def fetch_all() -> dict:
    """모든 데이터 수집 + 지표 계산 → dict 반환"""
    now = datetime.now(ET)

    # ── 1. 원시 데이터 수집 ──
    spy = yf.Ticker("SPY")
    hist = spy.history(period="1y", interval="1d")
    if hist.empty:
        raise RuntimeError("SPY 데이터 수신 실패")

    intra = spy.history(period="5d", interval="5m")

    # 보조 자산
    extras = {}
    for sym, key in [("^VIX", "vix"), ("CL=F", "oil"), ("ES=F", "es_futures"),
                      ("GC=F", "gold"), ("^TNX", "us10y"), ("^IXIC", "nasdaq"),
                      ("^DJI", "dow"), ("EFA", "efa")]:
        try:
            h = yf.Ticker(sym).history(period="5d")
            if not h.empty:
                extras[key] = round(h["Close"].iloc[-1], 2)
                if len(h) >= 2:
                    prev = h["Close"].iloc[-2]
                    extras[f"{key}_chg"] = round(((h["Close"].iloc[-1] - prev) / prev) * 100, 2)
                else:
                    extras[f"{key}_chg"] = 0.0
            else:
                extras[key] = 0
                extras[f"{key}_chg"] = 0
        except:
            extras[key] = 0
            extras[f"{key}_chg"] = 0

    # ── 2. 가격 기본 ──
    c = hist["Close"]
    h = hist["High"]
    lo = hist["Low"]
    v = hist["Volume"]

    last = round(c.iloc[-1], 2)
    prev = round(c.iloc[-2], 2)
    chg = round(last - prev, 2)
    chg_pct = round((chg / prev) * 100, 2)
    d_high = round(h.iloc[-1], 2)
    d_low = round(lo.iloc[-1], 2)
    d_vol = int(v.iloc[-1])
    avg_vol = int(v.tail(20).mean())
    vol_ratio = round(d_vol / avg_vol, 2) if avg_vol else 1.0

    # ── 2b. 애프터마켓 / 프리마켓 가격 ──
    ah_price = 0; ah_chg = 0; ah_chg_pct = 0
    pm_price = 0; pm_chg = 0; pm_chg_pct = 0
    try:
        info = spy.fast_info
        # Post-market (애프터마켓)
        if hasattr(info, 'last_price') and info.last_price:
            rt = round(info.last_price, 2)
            if rt != last:  # 장 마감가와 다르면 시간외 가격
                ah_price = rt
                ah_chg = round(rt - last, 2)
                ah_chg_pct = round((ah_chg / last) * 100, 2)
    except:
        pass
    try:
        info_dict = spy.info
        # Post-market
        if not ah_price and info_dict.get("postMarketPrice"):
            ah_price = round(info_dict["postMarketPrice"], 2)
            ah_chg = round(ah_price - last, 2)
            ah_chg_pct = round((ah_chg / last) * 100, 2)
        # Pre-market
        if info_dict.get("preMarketPrice"):
            pm_price = round(info_dict["preMarketPrice"], 2)
            pm_chg = round(pm_price - last, 2)
            pm_chg_pct = round((pm_chg / last) * 100, 2)
    except:
        pass

    ath = round(c.max(), 2)
    ath_date = c.idxmax().strftime("%m/%d")
    ath_pct = round(((last - ath) / ath) * 100, 2)

    # ── 3. 이동평균선 ──
    def ema(s, n): return round(s.ewm(span=n, adjust=False).mean().iloc[-1], 2)
    def sma(s, n): return round(s.tail(n).mean(), 2)

    mas = {
        "EMA 5": ema(c, 5), "T-Line (EMA 8)": ema(c, 8),
        "EMA 9": ema(c, 9), "EMA 21": ema(c, 21),
        "SMA 50": sma(c, 50), "SMA 100": sma(c, 100), "SMA 200": sma(c, 200),
    }
    ma_sell = sum(1 for x in mas.values() if last < x)
    ma_buy = len(mas) - ma_sell

    # Death cross / Golden cross
    cross = "Death Cross" if sma(c, 50) < sma(c, 200) else "Golden Cross"

    # ── 4. RSI ──
    delta = c.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    rsi = round((100 - (100 / (1 + rs))).iloc[-1], 1)

    # ── 5. MACD ──
    e12 = c.ewm(span=12, adjust=False).mean()
    e26 = c.ewm(span=26, adjust=False).mean()
    macd_line = e12 - e26
    sig_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_val = round(macd_line.iloc[-1], 3)
    macd_sig = round(sig_line.iloc[-1], 3)
    macd_hist = round((macd_line - sig_line).iloc[-1], 3)

    # ── 6. Stochastic ──
    low14 = lo.tail(14).min()
    high14 = h.tail(14).max()
    stoch_k = round(((c.iloc[-1] - low14) / (high14 - low14)) * 100, 1) if high14 != low14 else 50

    # ── 7. ATR ──
    tr = pd.concat([h - lo, (h - c.shift()).abs(), (lo - c.shift()).abs()], axis=1).max(axis=1)
    atr = round(tr.tail(14).mean(), 2)

    # ── 8. VWAP (장중) ──
    vwap = 0
    if not intra.empty and intra["Volume"].sum() > 0:
        cv = intra["Volume"].cumsum()
        cvp = (intra["Close"] * intra["Volume"]).cumsum()
        vwap = round(cvp.iloc[-1] / cv.iloc[-1], 2)

    # ── 9. Bollinger Bands ──
    sma20 = c.tail(20).mean()
    std20 = c.tail(20).std()
    bb_upper = round(sma20 + 2 * std20, 2)
    bb_lower = round(sma20 - 2 * std20, 2)
    bb_mid = round(sma20, 2)

    # ── 10. 지지/저항 ──
    pp = round((d_high + d_low + last) / 3, 2)
    r1 = round(2 * pp - d_low, 2)
    r2 = round(pp + (d_high - d_low), 2)
    s1_pivot = round(2 * pp - d_high, 2)
    s2_pivot = round(pp - (d_high - d_low), 2)

    # 주요 레벨
    levels = {
        "resistance": [
            {"label": "SMA 200", "price": mas["SMA 200"]},
            {"label": "SMA 100", "price": mas["SMA 100"]},
            {"label": "SMA 50", "price": mas["SMA 50"]},
            {"label": "Pivot R1", "price": r1},
        ],
        "support": [
            {"label": "Pivot", "price": pp},
            {"label": "Pivot S1", "price": s1_pivot},
            {"label": "Pivot S2", "price": s2_pivot},
            {"label": "BB Lower", "price": bb_lower},
        ],
    }

    # ── 11. 시그널 종합 ──
    def rsi_signal(r):
        if r < 30: return "과매도"
        if r > 70: return "과매수"
        return "중립"

    def overall_signal(ma_s, r):
        score = 0
        score -= ma_s * 2       # MA sell signals
        score += (7 - ma_s) * 2  # MA buy signals
        if r < 30: score += 1    # oversold = contrarian buy
        if r > 70: score -= 1
        if macd_val < macd_sig: score -= 1
        else: score += 1
        if score <= -8: return "Strong Sell"
        if score <= -3: return "Sell"
        if score >= 8: return "Strong Buy"
        if score >= 3: return "Buy"
        return "Neutral"

    signal = overall_signal(ma_sell, rsi)

    # ── 12. 최근 5일 성과 ──
    recent = []
    for i in range(-5, 0):
        if abs(i) <= len(hist):
            idx = hist.index[i]
            recent.append({
                "date": idx.strftime("%m/%d"),
                "close": round(c.iloc[i], 2),
                "chg_pct": round(((c.iloc[i] - c.iloc[i-1]) / c.iloc[i-1]) * 100, 2),
                "vol": int(v.iloc[i]),
            })

    # ── 13. COMPOSITE SIGNAL ──
    composite = compute_composite(
        last=last, mas=mas, rsi=rsi, macd_val=macd_val, macd_sig=macd_sig,
        macd_hist=macd_hist, stoch_k=stoch_k, vwap=vwap,
        d_vol=d_vol, avg_vol=avg_vol, chg=chg, atr=atr,
        sma50_prev=round(c.tail(55).head(50).mean(), 2),
        sma200_prev=round(c.tail(220).head(200).mean(), 2),
        levels=levels, bb_lower=bb_lower, bb_upper=bb_upper,
    )

    # ── Return ──
    return {
        "timestamp": now.strftime("%Y-%m-%d %H:%M ET"),
        "date": now.strftime("%Y-%m-%d"),
        "session": detect_session(now),
        "price": {
            "last": last, "prev": prev, "chg": chg, "chg_pct": chg_pct,
            "high": d_high, "low": d_low, "range": round(d_high - d_low, 2),
            "range_pct": round(((d_high - d_low) / d_low) * 100, 2),
            "after_hours": ah_price, "ah_chg": ah_chg, "ah_chg_pct": ah_chg_pct,
            "pre_market": pm_price, "pm_chg": pm_chg, "pm_chg_pct": pm_chg_pct,
        },
        "ath": {"price": ath, "date": ath_date, "pct": ath_pct},
        "volume": {
            "current": d_vol, "avg20": avg_vol, "ratio": vol_ratio,
            "trend": "상승" if d_vol > avg_vol else "하락",
        },
        "ma": mas,
        "ma_summary": {"sell": ma_sell, "buy": ma_buy, "cross": cross},
        "indicators": {
            "RSI (14)": {"value": rsi, "signal": rsi_signal(rsi)},
            "MACD": {"value": macd_val, "signal": "매도" if macd_val < macd_sig else "매수"},
            "MACD Signal": {"value": macd_sig, "signal": ""},
            "MACD Histogram": {"value": macd_hist, "signal": "확장" if abs(macd_hist) > abs(round((macd_line - sig_line).iloc[-2], 3)) else "수축"},
            "Stochastic %K": {"value": stoch_k, "signal": "과매도" if stoch_k < 20 else ("과매수" if stoch_k > 80 else "중립")},
            "ATR (14)": {"value": atr, "signal": f"일일 변동 ${atr}"},
        },
        "vwap": vwap,
        "bollinger": {"upper": bb_upper, "mid": bb_mid, "lower": bb_lower},
        "levels": levels,
        "signal": signal,
        "composite": composite,
        "extras": extras,
        "recent": recent,
    }


def compute_composite(*, last, mas, rsi, macd_val, macd_sig, macd_hist,
                       stoch_k, vwap, d_vol, avg_vol, chg, atr,
                       sma50_prev, sma200_prev, levels, bb_lower, bb_upper):
    """
    단기 (1-5일) + 중기 (1-4주) + Today's Action 산출
    ─────────────────────────────────────────────────
    각 지표별 +1(매수) / -1(매도) 스코어링 → 합산 → 등급 변환
    """

    # ══════════════════════════════════
    #  단기 (Short-term, 1-5일)
    # ══════════════════════════════════
    st_scores = {}

    # 1) 단기 MA 크로스 (EMA 5/8/9/21 vs price)
    for name in ["EMA 5", "T-Line (EMA 8)", "EMA 9", "EMA 21"]:
        if name in mas:
            st_scores[name] = 1 if last > mas[name] else -1

    # 2) RSI — 방향성 + 과매도/과매수 반전 가능성
    if rsi < 20:
        st_scores["RSI"] = 0.5    # 극단적 과매도 → 반등 가능성 (약한 매수)
    elif rsi < 30:
        st_scores["RSI"] = 0      # 과매도지만 추세 약세 → 중립
    elif rsi < 45:
        st_scores["RSI"] = -1     # 약세 영역
    elif rsi < 55:
        st_scores["RSI"] = 0      # 중립
    elif rsi < 70:
        st_scores["RSI"] = 1      # 강세 영역
    else:
        st_scores["RSI"] = -0.5   # 과매수 → 되돌림 가능성

    # 3) MACD
    if macd_val > macd_sig:
        st_scores["MACD"] = 1
        if macd_hist > 0:
            st_scores["MACD 모멘텀"] = 0.5  # histogram 확장
    else:
        st_scores["MACD"] = -1
        if macd_hist < 0:
            st_scores["MACD 모멘텀"] = -0.5

    # 4) Stochastic
    if stoch_k < 20:
        st_scores["Stochastic"] = 0.5  # 과매도 반등 가능
    elif stoch_k > 80:
        st_scores["Stochastic"] = -0.5
    elif stoch_k > 50:
        st_scores["Stochastic"] = 0.5
    else:
        st_scores["Stochastic"] = -0.5

    # 5) VWAP
    if vwap > 0:
        st_scores["VWAP"] = 1 if last > vwap else -1

    # 6) 볼륨 컨펌 (가격 방향과 볼륨 방향 일치 여부)
    vol_rising = d_vol > avg_vol
    if chg > 0 and vol_rising:
        st_scores["Vol Confirm"] = 1     # 상승 + 볼륨 증가 = 강세 컨펌
    elif chg < 0 and vol_rising:
        st_scores["Vol Confirm"] = -1    # 하락 + 볼륨 증가 = 약세 컨펌 (distribution)
    else:
        st_scores["Vol Confirm"] = 0     # 미확인

    st_total = sum(st_scores.values())
    st_max = len(st_scores)  # 이론적 max

    # 등급 변환
    if st_total <= -4:
        st_signal = "Strong Sell"
    elif st_total <= -1.5:
        st_signal = "Sell"
    elif st_total < 1.5:
        st_signal = "Neutral"
    elif st_total < 4:
        st_signal = "Buy"
    else:
        st_signal = "Strong Buy"

    # 핵심 근거 문자열
    st_drivers = []
    if st_scores.get("VWAP", 0) < 0:
        st_drivers.append("VWAP 하회")
    elif st_scores.get("VWAP", 0) > 0:
        st_drivers.append("VWAP 상회")
    if rsi < 30:
        st_drivers.append(f"RSI {rsi} 과매도")
    elif rsi > 70:
        st_drivers.append(f"RSI {rsi} 과매수")
    ma_below = sum(1 for n in ["EMA 5", "EMA 9", "EMA 21"] if st_scores.get(n, 0) < 0)
    if ma_below >= 2:
        st_drivers.append(f"단기 MA {ma_below}/3 하회")
    ma_above = sum(1 for n in ["EMA 5", "EMA 9", "EMA 21"] if st_scores.get(n, 0) > 0)
    if ma_above >= 2:
        st_drivers.append(f"단기 MA {ma_above}/3 상회")
    if st_scores.get("Vol Confirm", 0) == -1:
        st_drivers.append("볼륨 매도 컨펌")
    elif st_scores.get("Vol Confirm", 0) == 1:
        st_drivers.append("볼륨 매수 컨펌")

    # ══════════════════════════════════
    #  중기 (Mid-term, 1-4주)
    # ══════════════════════════════════
    mt_scores = {}

    # 1) SMA 50 vs price (가중 1.5x)
    mt_scores["SMA 50"] = 1.5 if last > mas.get("SMA 50", 0) else -1.5

    # 2) SMA 200 vs price (가중 2x)
    mt_scores["SMA 200"] = 2 if last > mas.get("SMA 200", 0) else -2

    # 3) Golden/Death Cross (가중 1.5x)
    sma50_val = mas.get("SMA 50", 0)
    sma200_val = mas.get("SMA 200", 0)
    if sma50_val > sma200_val:
        mt_scores["MA Cross"] = 1.5
    else:
        mt_scores["MA Cross"] = -1.5

    # 4) SMA 50 기울기 (현재 vs 5일전)
    if sma50_val > sma50_prev:
        mt_scores["SMA50 방향"] = 1
    else:
        mt_scores["SMA50 방향"] = -1

    # 5) SMA 200 기울기 (현재 vs 20일전)
    if sma200_val > sma200_prev:
        mt_scores["SMA200 방향"] = 1
    else:
        mt_scores["SMA200 방향"] = -1

    # 6) RSI 영역 (50 기준)
    mt_scores["RSI 중기"] = 1 if rsi > 50 else -1

    mt_total = sum(mt_scores.values())

    if mt_total <= -4:
        mt_signal = "Strong Sell"
    elif mt_total <= -1:
        mt_signal = "Sell"
    elif mt_total < 1:
        mt_signal = "Neutral"
    elif mt_total < 4:
        mt_signal = "Buy"
    else:
        mt_signal = "Strong Buy"

    mt_drivers = []
    if mt_scores["SMA 200"] < 0:
        mt_drivers.append("200일선 하회")
    else:
        mt_drivers.append("200일선 상회")
    if mt_scores["MA Cross"] < 0:
        mt_drivers.append("Death Cross")
    else:
        mt_drivers.append("Golden Cross")
    if mt_scores["SMA50 방향"] < 0:
        mt_drivers.append("SMA50 하락 중")
    else:
        mt_drivers.append("SMA50 상승 중")

    # ══════════════════════════════════
    #  Today's Action
    # ══════════════════════════════════

    # 방향 판단
    both_bear = "Sell" in st_signal and "Sell" in mt_signal
    both_bull = "Buy" in st_signal and "Buy" in mt_signal
    st_bear = "Sell" in st_signal
    st_bull = "Buy" in st_signal
    oversold = rsi < 30

    # 사이즈 결정
    if both_bear or both_bull:
        sizing = "1/2 Kelly"
        confidence = "높음"
    elif oversold and st_bear:
        sizing = "1/4 Kelly"
        confidence = "낮음 (과매도 반등 리스크)"
    else:
        sizing = "1/3 Kelly"
        confidence = "보통"

    # 저항/지지 레벨에서 Entry/Target/Stop 산출
    r_levels = sorted([l["price"] for l in levels.get("resistance", [])], reverse=False)
    s_levels = sorted([l["price"] for l in levels.get("support", [])], reverse=True)

    nearest_r = r_levels[0] if r_levels else last + atr
    nearest_s = s_levels[0] if s_levels else last - atr

    if both_bear:
        action = "PUT"
        action_desc = "단기 + 중기 모두 약세 → 하방 유지"
        entry = f"${nearest_r} 저항 rejection 시"
        target = f"${s_levels[0] if s_levels else round(last - atr, 2)} → ${s_levels[1] if len(s_levels) > 1 else round(last - atr*2, 2)}"
        stop = f"${round(nearest_r + atr * 0.3, 2)} 위"
        caution = ""
    elif both_bull:
        action = "CALL"
        action_desc = "단기 + 중기 모두 강세 → 상방 유지"
        entry = f"${nearest_s} 지지 확인 시"
        target = f"${r_levels[0] if r_levels else round(last + atr, 2)} → ${r_levels[1] if len(r_levels) > 1 else round(last + atr*2, 2)}"
        stop = f"${round(nearest_s - atr * 0.3, 2)} 아래"
        caution = ""
    elif st_bear and not "Sell" in mt_signal:
        action = "PUT (light)"
        action_desc = "단기 약세 but 중기 아직 전환 미확정 → 소규모"
        entry = f"${nearest_r} rejection 시"
        target = f"${nearest_s}"
        stop = f"${round(nearest_r + atr * 0.3, 2)} 위"
        sizing = "1/4 Kelly"
        confidence = "보통 (시간축 불일치)"
        caution = "중기 추세 전환 미확정 — 사이즈 축소"
    elif st_bull and not "Buy" in mt_signal:
        action = "CALL (light)"
        action_desc = "단기 반등 시그널 but 중기 약세 → counter-trend"
        entry = f"${nearest_s} 지지 확인 시"
        target = f"${nearest_r}"
        stop = f"${round(nearest_s - atr * 0.3, 2)} 아래"
        sizing = "1/4 Kelly"
        confidence = "보통 (counter-trend)"
        caution = "중기 하락 추세 내 반등 — TP 보수적"
    else:
        action = "WAIT"
        action_desc = "시그널 불명확 → 관망"
        entry = "시그널 대기"
        target = "-"
        stop = "-"
        sizing = "-"
        confidence = "-"
        caution = "명확한 방향 잡힐 때까지 대기"

    # 추가 주의사항
    warnings = []
    if oversold:
        warnings.append(f"⚠️ RSI {rsi} 극단적 과매도 — 기술적 반등 가능성 상존")
    if d_vol > avg_vol * 1.3:
        warnings.append(f"⚠️ 거래량 평균 대비 {round(d_vol/avg_vol, 1)}x — 변동성 확대")
    if atr > last * 0.02:
        warnings.append(f"⚠️ ATR ${atr} — 일일 변동 큼, SL 넓게 설정")
    if caution:
        warnings.append(f"⚠️ {caution}")

    return {
        "short_term": {
            "signal": st_signal,
            "score": round(st_total, 1),
            "max_score": st_max,
            "drivers": st_drivers,
            "details": {k: v for k, v in st_scores.items()},
        },
        "mid_term": {
            "signal": mt_signal,
            "score": round(mt_total, 1),
            "max_score": len(mt_scores),
            "drivers": mt_drivers,
            "details": {k: v for k, v in mt_scores.items()},
        },
        "action": {
            "direction": action,
            "description": action_desc,
            "entry": entry,
            "target": target,
            "stop": stop,
            "sizing": sizing,
            "confidence": confidence,
            "warnings": warnings,
        },
    }


def detect_session(now) -> str:
    h = now.hour
    if h < 10: return "pre"
    elif h < 16: return "mid"
    else: return "post"


SESSION_LABELS = {
    "pre":  "🌅 프리마켓 브리핑",
    "mid":  "📊 미드데이 체크",
    "post": "🌙 데일리 리캡",
}

SESSION_LABELS_EN = {
    "pre":  "Pre-market Briefing",
    "mid":  "Midday Check",
    "post": "Daily Recap",
}
