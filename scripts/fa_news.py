# -*- coding: utf-8 -*-
"""
FA tầng 1 — LỌC PHÁP LÝ / CỜ ĐỎ từ tin tức + thu thập tin gần đây (vnstock).
0 token LLM: quét tiêu đề/keyword tin bằng luật từ khóa. Mã dính cờ đỏ -> loại khỏi TA.

Dùng: py scripts/fa_news.py FPT VIC NVL ...   (mặc định: đọc data/watchlist.json)
"""
import warnings, io, contextlib, json, os, sys, time, datetime as dt, re
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = 120  # chỉ xét tin trong ~4 tháng gần nhất

# Cờ đỏ pháp lý/nghiêm trọng -> LOẠI (không dùng TA vì giá nhảy theo tin)
RED = ["khởi tố","điều tra","truy tố","bắt tạm giam","khám xét","thao túng","làm giá",
       "hủy niêm yết","huỷ niêm yết","đình chỉ","kiểm soát đặc biệt","hạn chế giao dịch",
       "diện cảnh báo","diện kiểm soát","gian lận","âm vốn","vỡ nợ","mất khả năng thanh toán",
       "kiểm toán từ chối","ý kiến ngoại trừ","chậm công bố","phong tỏa","cưỡng chế"]
# Cảnh báo nhẹ -> ghi chú, không loại
WARN = ["xử phạt","vi phạm","phạt","truy thu","từ nhiệm","miễn nhiệm","bán giải chấp","thua lỗ"]
# Chức danh lãnh đạo -> gắn cờ tin ban lãnh đạo
POS = ["chủ tịch","tổng giám đốc","phó chủ tịch","thành viên hđqt","hội đồng quản trị",
       "kế toán trưởng","ceo","ban lãnh đạo","người nội bộ","người liên quan","cổ đông lớn"]
# Vấn đề quản trị lãnh đạo (kết hợp với POS) -> cảnh báo/loại tùy mức
LEAD_RED = ["bị bắt","khởi tố","truy tố","tạm giam","điều tra"]
LEAD_WARN = ["từ nhiệm","miễn nhiệm","đăng ký bán","bán giải chấp","thoái vốn","bán chui","từ chức"]

def _silent(fn,*a,**k):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        return fn(*a,**k)

def get_news(sym):
    from vnstock.api.company import Company
    c = Company(symbol=sym, source="VCI")
    return _silent(c.news)

def scan(sym):
    try:
        n = get_news(sym)
    except Exception as e:
        return dict(ticker=sym, ok=None, note=f"lỗi tin: {repr(e)[:60]}")
    if n is None or len(n)==0:
        return dict(ticker=sym, ok=True, red=[], warn=[], recent=[], note="không có tin")
    n = n.copy()
    n["_d"] = n["public_date"].astype(str).str[:10]
    cutoff = (dt.date.today()-dt.timedelta(days=DAYS)).isoformat()
    n = n[n["_d"] >= cutoff]
    text_cols = [c for c in ["news_title","friendly_title","news_short_content","news_keyword"] if c in n.columns]
    red_hits, warn_hits, recent = set(), set(), []
    lead_news, lead_red, lead_warn = [], set(), set()
    for _, row in n.sort_values("_d", ascending=False).iterrows():
        blob = " ".join(str(row.get(c,"")) for c in text_cols).lower()
        for kw in RED:
            if kw in blob: red_hits.add(kw)
        for kw in WARN:
            if kw in blob: warn_hits.add(kw)
        # --- tin ban lãnh đạo ---
        if any(p in blob for p in POS):
            title = str(row.get("news_title") or row.get("friendly_title") or "")[:85]
            if len(lead_news) < 5:
                lead_news.append(f"{row['_d']} — {title}")
            for kw in LEAD_RED:
                if kw in blob: lead_red.add(kw)
            for kw in LEAD_WARN:
                if kw in blob: lead_warn.add(kw)
    for _, row in n.sort_values("_d", ascending=False).head(4).iterrows():
        t = str(row.get("news_title") or row.get("friendly_title") or "")[:80]
        recent.append(f"{row['_d']} — {t}")
    return dict(ticker=sym, ok=(len(red_hits)==0 and len(lead_red)==0),
                red=sorted(red_hits), warn=sorted(warn_hits),
                lead_red=sorted(lead_red), lead_warn=sorted(lead_warn),
                lead_news=lead_news, n_news=int(len(n)), recent=recent)

def main():
    syms = sys.argv[1:]
    if not syms:
        syms = json.load(open(os.path.join(ROOT,"data","watchlist.json"),encoding="utf-8"))
    results=[]
    for s in syms:
        results.append(scan(s)); time.sleep(3.2)

    # hợp nhất cờ pháp lý lãnh đạo từ báo chí (fa_press_scan / seed thủ công)
    lf_path = os.path.join(ROOT, "data", "leadership_flags.json")
    press = {}
    if os.path.exists(lf_path):
        for f in json.load(open(lf_path, encoding="utf-8")).get("flags", []):
            press[f.get("ticker")] = f
    for r in results:
        f = press.get(r["ticker"])
        if not f: continue
        r["press_flag"] = f
        if f.get("severity") == "red":
            r.setdefault("lead_red", []).append("báo chí: " + f.get("issue","")[:50]); r["ok"] = False
        else:
            r.setdefault("lead_warn", []).append("báo chí: " + f.get("person",""))

    json.dump(results, open(os.path.join(ROOT,"data","fa_news.json"),"w",encoding="utf-8"),
              ensure_ascii=False, indent=2)
    passed=[r for r in results if r.get("ok")]
    flagged=[r for r in results if r.get("ok")==False]
    print(f"Quét tin {len(syms)} mã | Sạch: {len(passed)} | DÍNH CỜ ĐỎ (loại): {len(flagged)}")
    for r in flagged:
        why = (r.get('red') or []) + [f"LÃNH ĐẠO:{x}" for x in (r.get('lead_red') or [])]
        print(f"  [LOẠI] {r['ticker']}: {', '.join(why)}")
        for line in r.get("recent",[])[:2]: print(f"          · {line}")
    for r in results:
        if r.get("ok") and (r.get("warn") or r.get("lead_warn")):
            w = (r.get('warn') or []) + [f"LĐ:{x}" for x in (r.get('lead_warn') or [])]
            print(f"  [lưu ý] {r['ticker']}: {', '.join(w)}")
    for r in results:
        if r.get("press_flag"):
            f = r["press_flag"]
            print(f"  [BÁO CHÍ {f.get('severity','?').upper()}] {r['ticker']}: {f.get('person','')} "
                  f"({f.get('role','')}) — {f.get('issue','')}")
            print(f"        nguồn: {f.get('source','')}")
    print("--- Tin ban lãnh đạo gần đây (CBTT) ---")
    for r in results:
        if r.get("lead_news"):
            print(f"  {r['ticker']}:")
            for line in r["lead_news"][:3]: print(f"     · {line}")

if __name__ == "__main__":
    main()
