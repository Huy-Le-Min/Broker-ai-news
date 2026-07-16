# -*- coding: utf-8 -*-
"""
FA tầng 2 — CHẤM ĐIỂM CHẤT LƯỢNG + ĐỊNH GIÁ từ báo cáo tài chính thô (vnstock VCI).
Tự tính: ROE, biên LN ròng, tăng trưởng DT/LN (YoY), Nợ vay/VCSH, P/E, P/B.
Điểm FA 0-100. Loại (FAIL) nếu thua lỗ hoặc âm vốn. Ngân hàng/CK bỏ qua phạt đòn bẩy.
FA đổi theo quý -> cache data/fa_scores.json, làm mới ~tuần (không cần chạy mỗi tối).

Dùng: py scripts/fundamentals.py FPT VCB HPG ...
"""
import warnings, io, contextlib, json, os, sys, time, datetime as dt
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

# Ngành tài chính (bank/CK/bảo hiểm): đòn bẩy cao là bản chất -> không phạt D/E, ưu tiên P/B
FIN = set("VCB BID CTG ACB MBB TCB VPB STB SHB HDB TPB LPB VIB MSB EIB SSB NAB OCB "
          "SSI VCI HCM VND VIX FTS BSI SHS MBS CTS EVF DSE BVH MIG PVI".split())

def _silent(fn,*a,**k):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        return fn(*a,**k)

def val(df, label, year, contains=False):
    """Lấy giá trị dòng theo item_en (khớp đúng, hoặc chứa) tại cột năm."""
    col = "item_en"
    if contains:
        m = df[df[col].astype(str).str.lower().str.contains(label.lower(), na=False)]
    else:
        m = df[df[col].astype(str) == label]
    for _, r in m.iterrows():
        v = r.get(year)
        if v is not None and str(v) not in ("nan","None",""):
            try: return float(v)
            except: pass
    return None

def val_ci(df, labels, year):
    """Thử lần lượt danh sách nhãn (khớp đúng, không phân biệt hoa/thường)."""
    low = df["item_en"].astype(str).str.strip().str.lower()
    for lab in labels:
        m = df[low == lab.lower()]
        for _, r in m.iterrows():
            v = r.get(year)
            if v is not None and str(v) not in ("nan","None",""):
                try: return float(v)
                except: pass
    return None

def get_statements(sym):
    from vnstock.api.financial import Finance
    f = Finance(symbol=sym, source="VCI")
    inc = _silent(f.income_statement, period="year", lang="en")
    bs  = _silent(f.balance_sheet, period="year", lang="en")
    return inc, bs

def last_close(sym):
    from screener_vn100 import get_hist
    df = get_hist(sym, days=150)   # >60 nến để qua ngưỡng tối thiểu
    return float(df["close"].iloc[-1]) * 1000 if df is not None else None  # nghìn -> đồng

def years_of(df):
    return sorted([c for c in df.columns if str(c).isdigit()], reverse=True)

def analyze_fa(sym):
    try:
        inc, bs = get_statements(sym)
    except Exception as e:
        return dict(ticker=sym, ok=None, note=f"lỗi BCTC: {repr(e)[:50]}")
    yrs = years_of(inc)
    if len(yrs) < 2:
        return dict(ticker=sym, ok=None, note="thiếu năm")
    y0, y1 = yrs[0], yrs[1]
    is_fin = sym in FIN

    if is_fin:  # ngân hàng/CK: doanh thu lõi = thu nhập lãi thuần / tổng thu nhập HĐ
        rev0 = val(inc,"Total operating income",y0,contains=True) or val(inc,"Net Interest Income",y0)
        rev1 = val(inc,"Total operating income",y1,contains=True) or val(inc,"Net Interest Income",y1)
    else:
        rev0 = val(inc,"Net sales",y0) or val(inc,"revenue",y0,contains=True)
        rev1 = val(inc,"Net sales",y1) or val(inc,"revenue",y1,contains=True)
    npat0 = val(inc,"Net profit/(loss) after tax",y0)
    attr0 = val(inc,"Attributable to parent company",y0) or npat0
    attr1 = val(inc,"Attributable to parent company",y1) or val(inc,"Net profit/(loss) after tax",y1)
    ta = val_ci(bs,["Total Assets","TOTAL ASSETS"],y0)
    liab = val_ci(bs,["Liabilities","LIABILITIES","Total liabilities","TOTAL LIABILITIES"],y0)
    eq = val_ci(bs,["OWNER'S EQUITY","Owner's Equity","Total equity","TOTAL EQUITY","Equity"],y0)
    if eq is None and ta is not None and liab is not None:
        eq = ta - liab
    st_b = val(bs,"Short-term borrowings",y0) or 0
    lt_b = val(bs,"Long-term borrowings",y0) or 0
    debt = st_b + lt_b
    eps = val(inc,"EPS basic (VND)",y0)

    roe = (attr0/eq) if (attr0 and eq and eq>0) else None
    margin = (npat0/rev0) if (npat0 and rev0) else None
    rev_g = (rev0/rev1-1) if (rev0 and rev1 and rev1>0) else None
    prof_g = (attr0/attr1-1) if (attr0 and attr1 and attr1>0) else None
    de = (debt/eq) if (eq and eq>0) else None
    price = last_close(sym)
    shares = (attr0/eps) if (eps and eps>0 and attr0) else None
    pe = (price/eps) if (price and eps and eps>0) else None
    pb = (price*shares/eq) if (price and shares and eq and eq>0) else None

    # hard fail
    fail = (attr0 is not None and attr0 < 0) or (eq is not None and eq < 0)

    def band(x, cuts, pts):
        if x is None: return pts[-1]//2  # thiếu dữ liệu -> điểm trung tính
        for c,p in zip(cuts,pts):
            if x >= c: return p
        return 0
    s_roe = band(roe,[.20,.15,.10,.05],[25,20,13,6])
    s_mar = band(margin,[.20,.10,.05,0],[15,10,6,3])
    s_rg  = band(rev_g,[.20,.10,0,-.15],[15,11,6,2])
    s_pg  = band(prof_g,[.20,.10,0,-.15],[15,11,6,2])
    s_safe = 8 if is_fin else band(-(de if de is not None else 9),[-.3,-.6,-1.0,-1.5],[15,11,7,3])
    # valuation: P/E thấp tốt (đảo dấu)
    s_val = band(-(pe if pe and pe>0 else 99),[-8,-12,-16,-22],[15,11,7,3])
    score = s_roe+s_mar+s_rg+s_pg+s_safe+s_val
    verdict = "FAIL" if fail else ("PASS" if score>=55 else "WEAK")

    return dict(ticker=sym, ok=(not fail), verdict=verdict, score=score, is_fin=is_fin,
        roe=round(roe*100,1) if roe else None, margin=round(margin*100,1) if margin else None,
        rev_g=round(rev_g*100,1) if rev_g is not None else None,
        prof_g=round(prof_g*100,1) if prof_g is not None else None,
        de=round(de,2) if de is not None else None,
        pe=round(pe,1) if pe else None, pb=round(pb,2) if pb else None, year=y0)

def main():
    syms = sys.argv[1:] or json.load(open(os.path.join(ROOT,"data","watchlist.json"),encoding="utf-8"))
    res=[]
    for s in syms:
        res.append(analyze_fa(s)); time.sleep(3.2)
    res_ok=[r for r in res if r.get("score") is not None]
    res_ok.sort(key=lambda x:-x["score"])
    json.dump({"date":dt.date.today().isoformat(),"scores":res},
              open(os.path.join(ROOT,"data","fa_scores.json"),"w",encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"FA {len(syms)} mã | PASS: {sum(1 for r in res if r.get('verdict')=='PASS')} "
          f"| WEAK: {sum(1 for r in res if r.get('verdict')=='WEAK')} "
          f"| FAIL: {sum(1 for r in res if r.get('verdict')=='FAIL')}")
    for r in res_ok:
        print(f"  {r['ticker']:5} {r['verdict']:4} {r['score']:>3}đ | ROE {r['roe']}% biên {r['margin']}% "
              f"| tăng DT {r['rev_g']}% LN {r['prof_g']}% | D/E {r['de']} | P/E {r['pe']} P/B {r['pb']}"
              + (" [tài chính]" if r['is_fin'] else ""))
    for r in res:
        if r.get("score") is None: print(f"  {r['ticker']:5} — {r.get('note')}")

if __name__ == "__main__":
    main()
