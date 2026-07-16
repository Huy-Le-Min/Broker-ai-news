# -*- coding: utf-8 -*-
"""
Screener VN100 — kết hợp RSI + MACD + Bollinger + Volume (khung Daily).
Tìm tín hiệu MUA (>=3/4 đồng thuận) -> sinh "lệnh giấy" (paper trade) entry/SL/TP.
Ghi ra data/paper_trades.json (append). Chạy được local & trên GitHub Action (dùng vnstock).

Dùng: py scripts/screener_vn100.py [limit]
"""
import warnings, json, io, contextlib, time, sys, os, datetime as dt
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = os.path.join(ROOT, "data", "paper_trades.json")

def _silent(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        return fn(*a, **k)

def get_vn100():
    from vnstock.api.listing import Listing
    return list(_silent(Listing(source="VCI").symbols_by_group, "VN100"))

def get_universe():
    """VN100 ∪ watchlist riêng (data/watchlist.json). Dedup, giữ ổn định."""
    uni = set(get_vn100())
    wl_path = os.path.join(ROOT, "data", "watchlist.json")
    if os.path.exists(wl_path):
        uni |= set(json.load(open(wl_path, encoding="utf-8")))
    return sorted(uni)

SLEEP = float(os.environ.get("SCREENER_SLEEP", "3.2"))  # Guest vnstock = 20 req/phut

def get_hist(sym, days=320, retries=2, end=None):
    from vnstock.api.quote import Quote
    end = end or dt.date.today()
    start = end - dt.timedelta(days=days)
    for attempt in range(retries + 1):
        try:
            q = Quote(symbol=sym, source="VCI")
            df = _silent(q.history, start=start.isoformat(), end=end.isoformat(), interval="1D")
            if df is None or len(df) < 60:
                return None
            return df.reset_index(drop=True)
        except Exception as e:
            if "rate" in repr(e).lower() or "limit" in repr(e).lower():
                time.sleep(20)
            else:
                if attempt == retries:
                    raise
                time.sleep(3)
    return None

# ---------- indicators ----------
def rma(s, n):  # Wilder smoothing (khớp RSI TradingView)
    return s.ewm(alpha=1/n, adjust=False).mean()

def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0); dn = -d.clip(upper=0)
    rs = rma(up, n) / rma(dn, n).replace(0, np.nan)
    return 100 - 100/(1+rs)

def macd(close, f=12, s=26, sig=9):
    m = close.ewm(span=f, adjust=False).mean() - close.ewm(span=s, adjust=False).mean()
    sg = m.ewm(span=sig, adjust=False).mean()
    return m, sg, m - sg

def boll(close, n=20, k=2):
    mid = close.rolling(n).mean()
    sd = close.rolling(n).std(ddof=0)
    return mid + k*sd, mid, mid - k*sd

def analyze(df):
    c = df["close"]; v = df["volume"]
    r = rsi(c); m, sg, h = macd(c); ub, mb, lb = boll(c)
    vsma = v.rolling(20).mean()
    pctb = (c - lb) / (ub - lb)
    i = len(df) - 1; j = i - 1
    R, Rp = r.iloc[i], r.iloc[j]
    H, Hp = h.iloc[i], h.iloc[j]
    M, Mp = m.iloc[i], m.iloc[j]
    C, Cp = c.iloc[i], c.iloc[j]
    MB, MBp = mb.iloc[i], mb.iloc[j]
    PB, PBp = pctb.iloc[i], pctb.iloc[j]
    V, VS = v.iloc[i], vsma.iloc[i]

    rsi_bull = (Rp < 50 <= R) or (Rp < 35 and R > Rp)
    macd_bull = (Hp <= 0 < H) or (H > 0 and H > Hp)
    bb_bull = (C > MB and Cp <= MBp) or (PBp < 0.10 and PB > PBp)
    vol_ok = VS and V > 1.5 * VS
    guard = (R < 72) and (PB < 1.05)

    # --- lớp theo dõi OVERSOLD (bật đáy) ---
    LOW = float(lb.iloc[i])
    recently_os = float(r.iloc[max(0, i-5):i+1].min()) < 36
    oversold = (R < 36) and (PB < 0.20)                      # ứng viên: quá bán tại dải dưới
    vol_soft = bool(VS and V > 1.2 * VS)
    bounce_confirm = recently_os and macd_bull and vol_soft and (C > LOW)  # xác nhận đảo chiều

    reasons = []
    if rsi_bull: reasons.append(f"RSI {R:.0f} (bật lên)")
    if macd_bull: reasons.append(f"MACD hist {'+' if H>0 else ''}{H:.0f} cắt lên")
    if bb_bull: reasons.append("BB: bật dải dưới / lấy lại MA20")
    if vol_ok: reasons.append(f"Vol {V/VS:.1f}x TB20")
    score = int(rsi_bull) + int(macd_bull) + int(bb_bull) + int(vol_ok)
    buy = (score >= 3) and (macd_bull or rsi_bull) and guard

    # paper order
    entry = float(C)
    swing_low = float(df["low"].iloc[-5:].min())
    sl = min(swing_low, float(lb.iloc[i])) * 0.995
    if entry - sl <= 0 or (entry - sl)/entry > 0.08:
        sl = entry * 0.94
    risk = entry - sl
    tp1 = entry + 2*risk; tp2 = entry + 3*risk
    return dict(score=score, buy=bool(buy),
                f_rsi=bool(rsi_bull), f_macd=bool(macd_bull), f_bb=bool(bb_bull),
                f_vol=bool(vol_ok), f_guard=bool(guard),
                oversold=bool(oversold), bounce_confirm=bool(bounce_confirm),
                rsi=round(float(R),1),
                macd_hist=round(float(H),1), pctB=round(float(PB),2),
                vol_x=round(float(V/VS),2) if VS else None,
                entry=round(entry,2), sl=round(sl,2), tp1=round(tp1,2), tp2=round(tp2,2),
                rr_tp1=round((tp1-entry)/risk,2), rr_tp2=round((tp2-entry)/risk,2),
                reasons="; ".join(reasons))

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asof = None
    if len(sys.argv) > 2:
        asof = dt.date.fromisoformat(sys.argv[2])
    syms = get_universe()
    if limit: syms = syms[:limit]
    today = (asof or dt.date.today()).isoformat()
    signals, oversold, bounces, errors = [], [], [], 0
    for k, s in enumerate(syms):
        try:
            df = get_hist(s, end=asof)
            if df is None: continue
            a = analyze(df)
            a["ticker"] = s
            if a["buy"]:
                signals.append(a)
            if a["bounce_confirm"]:
                bounces.append(a)
            elif a["oversold"]:
                oversold.append(dict(ticker=s, date=today, rsi=a["rsi"],
                                     pctB=a["pctB"], vol_x=a["vol_x"]))
        except Exception as e:
            errors += 1
        time.sleep(SLEEP)

    # cập nhật danh sách oversold-watch (refresh mỗi lần quét)
    json.dump(sorted(oversold, key=lambda x: x["rsi"]),
              open(os.path.join(ROOT, "data", "oversold_watch.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    signals.sort(key=lambda x: (-x["score"], -(x["vol_x"] or 0)))

    # append paper trades
    book = []
    if os.path.exists(PAPER):
        book = json.load(open(PAPER, encoding="utf-8"))
    existing = {(t["ticker"], t["date"]) for t in book}
    for a in signals + bounces:
        key = (a["ticker"], today)
        if key in existing: continue
        existing.add(key)
        book.append(dict(date=today, ticker=a["ticker"], score=a["score"],
                         setup=("bounce_oversold" if a.get("bounce_confirm") else "screener"),
                         entry=a["entry"], sl=a["sl"], tp1=a["tp1"], tp2=a["tp2"],
                         rr_tp1=a["rr_tp1"], rr_tp2=a["rr_tp2"], reasons=a["reasons"],
                         status="open", outcome="", result_r=None, closed_date=""))
    json.dump(book, open(PAPER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    out = dict(date=today, scanned=len(syms), errors=errors, n_signals=len(signals),
               signals=signals)
    json.dump(out, open(os.path.join(ROOT, "data", "screener_last.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[{today}] Quét {len(syms)} mã, lỗi {errors} | MUA: {len(signals)} | "
          f"Bounce xác nhận: {len(bounces)} | Oversold theo dõi: {len(oversold)}")
    for a in signals:
        print(f"  [MUA] {a['ticker']:5} score {a['score']}/4 | entry {a['entry']} SL {a['sl']} "
              f"TP1 {a['tp1']} TP2 {a['tp2']} (R:R {a['rr_tp1']}) | {a['reasons']}")
    for a in bounces:
        print(f"  [BOUNCE] {a['ticker']:5} entry {a['entry']} SL {a['sl']} TP1 {a['tp1']} "
              f"| {a['reasons']}")
    if oversold:
        print("  [OVERSOLD watch] " + ", ".join(f"{o['ticker']}(RSI{o['rsi']})" for o in oversold))

if __name__ == "__main__":
    main()
