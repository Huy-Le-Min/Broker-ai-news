# -*- coding: utf-8 -*-
"""
Review lệnh giấy — tự chấm ĐÚNG/SAI + lý do, cập nhật thống kê.
Đọc data/paper_trades.json, với mỗi lệnh 'open' lấy giá từ ngày vào -> nay,
đi tới từng phiên xem chạm TP/SL trước, tính R thực tế + nhận xét.

Dùng: py scripts/screener_review.py
"""
import warnings, json, os, datetime as dt
warnings.filterwarnings("ignore")
from screener_vn100 import get_hist, SLEEP
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = os.path.join(ROOT, "data", "paper_trades.json")
MAX_HOLD = 20  # phiên: quá hạn mà chưa chạm gì -> hết hiệu lực

def resolve(t):
    entry, sl, tp1, tp2 = t["entry"], t["sl"], t["tp1"], t["tp2"]
    risk = entry - sl
    d0 = dt.date.fromisoformat(t["date"])
    df = get_hist(t["ticker"], end=dt.date.today())
    df = df[df["time"].astype(str) > t["date"]].reset_index(drop=True)
    if len(df) == 0:
        return t  # chưa có phiên nào sau khi vào
    mfe = mae = 0.0
    for k in range(len(df)):
        hi, lo = float(df["high"].iloc[k]), float(df["low"].iloc[k])
        mfe = max(mfe, hi - entry); mae = min(mae, lo - entry)
        hit_sl = lo <= sl
        hit_tp2 = hi >= tp2
        hit_tp1 = hi >= tp1
        # cùng phiên chạm cả hai -> giả định thận trọng: SL trước
        if hit_sl and (hit_tp1 or hit_tp2):
            outcome, r = "Chạm SL", round((sl-entry)/risk, 2)
            break
        if hit_tp2:
            outcome, r = "Chạm TP2", round((tp2-entry)/risk, 2); break
        if hit_tp1:
            outcome, r = "Chạm TP1", round((tp1-entry)/risk, 2); break
        if hit_sl:
            outcome, r = "Chạm SL", round((sl-entry)/risk, 2); break
    else:
        if len(df) >= MAX_HOLD:
            last = float(df["close"].iloc[-1])
            outcome, r = "Hết hiệu lực", round((last-entry)/risk, 2)
        else:
            return t  # còn mở, chờ tiếp

    held = k+1 if outcome != "Hết hiệu lực" else len(df)
    if outcome.startswith("Chạm TP"):
        note = f"ĐÚNG — {t['reasons']}; chạm {outcome[-3:]} sau {held} phiên (MFE +{mfe:.2f})."
    elif outcome == "Chạm SL":
        note = (f"SAI — dính SL sau {held} phiên. Tín hiệu bị phủ nhận "
                f"(MAE {mae:.2f}). Xem lại: vol có giả? thị trường chỉnh chung?")
    else:
        note = f"HÒA/HẾT HẠN — {held} phiên chưa tới TP/SL, đóng theo giá đóng cửa (R {r})."
    t.update(status="closed", outcome=outcome, result_r=r,
             closed_date=str(df["time"].iloc[held-1])[:10], review=note)
    return t

def stats(book):
    closed = [t for t in book if t["status"] == "closed"]
    wins = [t for t in closed if t["outcome"].startswith("Chạm TP")]
    losses = [t for t in closed if t["outcome"] == "Chạm SL"]
    rs = [t["result_r"] for t in closed if t.get("result_r") is not None]
    wr = len(wins)/(len(wins)+len(losses)) if (wins or losses) else None
    avg_r = sum(rs)/len(rs) if rs else None
    return dict(closed=len(closed), wins=len(wins), losses=len(losses),
                win_rate=round(wr,3) if wr is not None else None,
                avg_r=round(avg_r,2) if avg_r is not None else None)

def main():
    if not os.path.exists(PAPER):
        print("Chưa có lệnh giấy nào."); return
    book = json.load(open(PAPER, encoding="utf-8"))
    n_open = 0
    for t in book:
        if t["status"] == "open":
            n_open += 1
            resolve(t)
            time.sleep(SLEEP)
    json.dump(book, open(PAPER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    s = stats(book)
    print(f"Đã soát {n_open} lệnh mở. Tổng đã đóng: {s['closed']} "
          f"| Thắng {s['wins']} Thua {s['losses']} "
          f"| Win-rate {s['win_rate']} | R TB {s['avg_r']}")
    for t in book:
        if t["status"] == "closed" and t.get("review"):
            print(f"  {t['ticker']:5} [{t['date']}] {t['outcome']:11} R={t['result_r']:+.2f} | {t['review']}")

if __name__ == "__main__":
    main()
