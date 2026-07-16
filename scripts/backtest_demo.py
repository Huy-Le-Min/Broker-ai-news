# -*- coding: utf-8 -*-
"""
Backtest tín hiệu screener trên NHIỀU THÁNG lịch sử (vài mã) — kiểm chứng edge.
Quét mọi phiên tìm tín hiệu MUA -> mở lệnh giấy -> chấm forward (TP1/TP2/SL) -> thống kê.
Mỗi mã chỉ gọi API 1 lần. Dùng: py scripts/backtest_demo.py
"""
import warnings, os, sys, datetime as dt, json
warnings.filterwarnings("ignore")
from screener_vn100 import get_hist, analyze, SLEEP
import time

MAX_HOLD = 20
SYMS = ["FPT","HPG","SSI","GMD","DGW","VND","MWG","DBC"]

def resolve_fwd(df, i, entry, sl, tp1, tp2):
    risk = entry - sl
    mfe = mae = 0.0
    end = min(i+1+MAX_HOLD, len(df))
    for k in range(i+1, end):
        hi, lo = float(df["high"].iloc[k]), float(df["low"].iloc[k])
        mfe = max(mfe, hi-entry); mae = min(mae, lo-entry)
        hit_sl = lo <= sl; hit_tp2 = hi >= tp2; hit_tp1 = hi >= tp1
        if hit_sl and (hit_tp1 or hit_tp2):
            return "SL", round((sl-entry)/risk,2), k-i, mfe, mae
        if hit_tp2: return "TP2", round((tp2-entry)/risk,2), k-i, mfe, mae
        if hit_tp1: return "TP1", round((tp1-entry)/risk,2), k-i, mfe, mae
        if hit_sl:  return "SL",  round((sl-entry)/risk,2), k-i, mfe, mae
    if end-1 > i:
        last = float(df["close"].iloc[end-1])
        return "HET", round((last-entry)/risk,2), end-1-i, mfe, mae
    return None

def main():
    all_trades = []
    for s in SYMS:
        try:
            df = get_hist(s, days=400)
        except Exception as e:
            print(f"{s}: lỗi {repr(e)[:80]}"); time.sleep(SLEEP); continue
        if df is None or len(df) < 120:
            time.sleep(SLEEP); continue
        i = 60
        while i < len(df)-1:
            a = analyze(df.iloc[:i+1].reset_index(drop=True))
            if a["buy"]:
                r = resolve_fwd(df, i, a["entry"], a["sl"], a["tp1"], a["tp2"])
                if r:
                    oc, rr, held, mfe, mae = r
                    all_trades.append(dict(ticker=s, date=str(df["time"].iloc[i])[:10],
                        entry=a["entry"], sl=a["sl"], tp1=a["tp1"], tp2=a["tp2"],
                        outcome=oc, result_r=rr, held=held, score=a["score"],
                        reasons=a["reasons"]))
                    i += held  # nhảy qua đoạn đã giải quyết, tránh trùng
            i += 1
        time.sleep(SLEEP)

    if not all_trades:
        print("Không tìm thấy tín hiệu nào trong lịch sử mẫu."); return
    wins = [t for t in all_trades if t["outcome"] in ("TP1","TP2")]
    losses = [t for t in all_trades if t["outcome"] == "SL"]
    rs = [t["result_r"] for t in all_trades]
    wr = len(wins)/(len(wins)+len(losses)) if (wins or losses) else 0
    exp = sum(rs)/len(rs)
    json.dump(all_trades, open(os.path.join(os.path.dirname(__file__),"..","data","backtest_trades.json"),
              "w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"=== BACKTEST {len(SYMS)} mã, {len(all_trades)} lệnh ===")
    print(f"Thắng {len(wins)} | Thua {len(losses)} | Hết hạn {len(all_trades)-len(wins)-len(losses)}")
    print(f"Win-rate {wr:.0%} | Kỳ vọng {exp:+.2f}R/lệnh")
    print("--- vài lệnh mẫu (tự chấm đúng/sai + lý do) ---")
    for t in all_trades[:12]:
        verdict = "ĐÚNG" if t["outcome"] in ("TP1","TP2") else ("SAI" if t["outcome"]=="SL" else "HÒA")
        print(f"  {t['ticker']:4} {t['date']} sc{t['score']} -> {t['outcome']:3} {t['result_r']:+.2f}R "
              f"({t['held']}p) [{verdict}] | {t['reasons']}")

if __name__ == "__main__":
    main()
