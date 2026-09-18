# -*- coding: utf-8 -*-
"""
PIPELINE FA-first: FA chất lượng -> loại dính pháp lý -> TA setup. Xếp hạng survivors.
Quét universe (VN100 ∪ watchlist). Lưu tiến độ dần vào data/pipeline_result.json.
Nếu có data/broker_reports.json: ghép consensus CTCK vào mỗi survivor + nhích điểm ±6
(broker_boost = 2×(số MUA/KHẢ QUAN − số BÁN/KÉM KHẢ QUAN), chặn [-6,+6]).
LƯU Ý: TA chỉ là 'chất lượng setup', KHÔNG phải xác suất lời đã kiểm chứng (backtest edge âm).

Dùng: py scripts/pipeline.py [limit]
"""
import warnings, io, contextlib, json, os, sys, time, datetime as dt
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from fundamentals import val, val_ci, FIN, years_of
from screener_vn100 import get_hist, analyze, get_universe, SLEEP
from fa_news import scan as legal_scan

def _silent(fn,*a,**k):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        return fn(*a,**k)

def load_broker():
    """Đọc data/broker_reports.json -> map MÃ -> [khuyến nghị CTCK]. Rỗng nếu chưa có file."""
    m={}
    p=os.path.join(ROOT,"data","broker_reports.json")
    if os.path.exists(p):
        try:
            for s in json.load(open(p,encoding="utf-8")).get("stocks",[]):
                t=s.get("ticker")
                if t: m.setdefault(t,[]).append(s)
        except Exception:
            pass
    return m

def broker_summary(calls):
    """Tóm tắt consensus + điểm ròng (số MUA/KHẢ QUAN trừ số BÁN/KÉM KHẢ QUAN)."""
    def up(r): return (r or "").upper()
    pos=sum(1 for c in calls if any(k in up(c.get("rating")) for k in ("MUA","KHẢ QUAN")) and "KÉM" not in up(c.get("rating")))
    neg=sum(1 for c in calls if any(k in up(c.get("rating")) for k in ("BÁN","KÉM")))
    txt=" · ".join(f"{c.get('house','')} {c.get('rating','')}".strip() for c in calls[:3])
    return txt, pos-neg

def get_stmt(sym, kind):
    from vnstock.api.financial import Finance
    return _silent(getattr(Finance(symbol=sym, source="VCI"), kind), period="year", lang="en")

def fa_quality(sym):
    try:
        inc = get_stmt(sym,"income_statement"); time.sleep(SLEEP)
        bs  = get_stmt(sym,"balance_sheet")
    except Exception as e:
        return None
    yrs = years_of(inc)
    if len(yrs) < 2: return None
    y0,y1 = yrs[0],yrs[1]; is_fin = sym in FIN
    if is_fin:
        rev0=val(inc,"Total operating income",y0,contains=True) or val(inc,"Net Interest Income",y0)
        rev1=val(inc,"Total operating income",y1,contains=True) or val(inc,"Net Interest Income",y1)
    else:
        rev0=val(inc,"Net sales",y0) or val(inc,"revenue",y0,contains=True)
        rev1=val(inc,"Net sales",y1) or val(inc,"revenue",y1,contains=True)
    npat0=val(inc,"Net profit/(loss) after tax",y0)
    attr0=val(inc,"Attributable to parent company",y0) or npat0
    attr1=val(inc,"Attributable to parent company",y1) or val(inc,"Net profit/(loss) after tax",y1)
    ta=val_ci(bs,["Total Assets","TOTAL ASSETS"],y0)
    liab=val_ci(bs,["Liabilities","Total liabilities","TOTAL LIABILITIES"],y0)
    eq=val_ci(bs,["OWNER'S EQUITY","Owner's Equity","Total equity","TOTAL EQUITY","Equity"],y0)
    if eq is None and ta is not None and liab is not None: eq=ta-liab
    debt=(val(bs,"Short-term borrowings",y0) or 0)+(val(bs,"Long-term borrowings",y0) or 0)
    roe=(attr0/eq) if (attr0 and eq and eq>0) else None
    margin=(npat0/rev0) if (npat0 and rev0) else None
    rev_g=(rev0/rev1-1) if (rev0 and rev1 and rev1>0) else None
    prof_g=(attr0/attr1-1) if (attr0 and attr1 and attr1>0) else None
    de=(debt/eq) if (eq and eq>0) else None
    fail=(attr0 is not None and attr0<0) or (eq is not None and eq<0)
    def band(x,cuts,pts):
        if x is None: return pts[-1]//2
        for c,p in zip(cuts,pts):
            if x>=c: return p
        return 0
    score=(band(roe,[.20,.15,.10,.05],[30,24,16,8]) + band(margin,[.20,.10,.05,0],[15,10,6,3])
           + band(rev_g,[.20,.10,0,-.15],[20,15,8,3]) + band(prof_g,[.20,.10,0,-.15],[20,15,8,3])
           + (8 if is_fin else band(-(de if de is not None else 9),[-.3,-.6,-1.0,-1.5],[15,11,7,3])))
    verdict="FAIL" if fail else ("PASS" if score>=55 else "WEAK")
    return dict(ticker=sym, fa_verdict=verdict, fa_score=score, is_fin=is_fin,
        roe=round(roe*100,1) if roe else None, margin=round(margin*100,1) if margin else None,
        rev_g=round(rev_g*100,1) if rev_g is not None else None,
        prof_g=round(prof_g*100,1) if prof_g is not None else None, de=round(de,2) if de is not None else None)

def ta_setup(sym):
    d=get_hist(sym)
    if d is None: return None
    a=analyze(d); c=d["close"]; price=float(c.iloc[-1])
    ma20=float(c.iloc[-20:].mean()); ma50=float(c.iloc[-50:].mean()) if len(c)>=50 else ma20
    uptrend=price>ma20 and ma20>=ma50
    s=0
    if uptrend: s+=3
    elif price>ma20: s+=1
    if 45<=a["rsi"]<=66: s+=2
    if a["macd_hist"]>=0: s+=2
    if a["pctB"]<0.85: s+=1
    if a["rsi"]>50 and not a["oversold"]: s+=1
    return dict(price=price, rsi=a["rsi"], macd_hist=a["macd_hist"], pctB=a["pctB"],
                above_ma20=price>ma20, uptrend=uptrend, ta_score=s)

def main():
    limit=int(sys.argv[1]) if len(sys.argv)>1 else None
    uni=get_universe()
    if limit: uni=uni[:limit]
    bro=load_broker()
    lf={}
    p=os.path.join(ROOT,"data","leadership_flags.json")
    if os.path.exists(p):
        for f in json.load(open(p,encoding="utf-8")).get("flags",[]):
            if f.get("severity")=="red": lf[f["ticker"]]=f
    OUT=os.path.join(ROOT,"data","pipeline_result.json")
    res=[]; done=0
    for s in uni:
        done+=1
        rec={"ticker":s}
        if s in lf:
            rec.update(stage="loai_phap_ly", note=lf[s].get("issue","")[:60]); res.append(rec)
            json.dump({"date":dt.date.today().isoformat(),"scanned":done,"results":res},open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=2); continue
        fa=fa_quality(s); time.sleep(SLEEP)
        if not fa:
            rec.update(stage="thieu_bctc"); res.append(rec); continue
        rec.update(fa)
        if fa["fa_verdict"]!="PASS":
            rec["stage"]="fa_khong_dat"; res.append(rec)
            json.dump({"date":dt.date.today().isoformat(),"scanned":done,"results":res},open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=2); continue
        # FA PASS -> legal news + TA
        lg=legal_scan(s); time.sleep(SLEEP)
        if lg.get("ok")==False:
            rec.update(stage="loai_phap_ly", legal=(lg.get("red") or [])+(lg.get("lead_red") or []))
            res.append(rec); continue
        ta=ta_setup(s); time.sleep(SLEEP)
        if ta: rec.update(ta)
        rec["legal_warn"]=(lg.get("warn") or [])+(lg.get("lead_warn") or [])
        # consensus báo cáo CTCK/quỹ (nếu có) — ghép quan điểm + nhích nhẹ điểm (±6)
        calls=bro.get(s) or []
        boost=0
        if calls:
            rec["broker"]=[{k:c.get(k) for k in ("house","rating","target_price","upside","thesis","source")} for c in calls[:4]]
            summ,net=broker_summary(calls)
            rec["broker_consensus"]=summ
            boost=max(-6,min(6,net*2)); rec["broker_boost"]=boost
        rec["combined"]=round(fa["fa_score"]*0.6 + (ta["ta_score"] if ta else 0)*4 + boost, 1)
        rec["stage"]="ok"
        res.append(rec)
        json.dump({"date":dt.date.today().isoformat(),"scanned":done,"results":res},open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

    json.dump({"date":dt.date.today().isoformat(),"scanned":done,"results":res},open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    finalists=[r for r in res if r.get("stage")=="ok"]
    finalists.sort(key=lambda x:-x.get("combined",0))
    print(f"=== PIPELINE {done} mã ===")
    print(f"FA PASS + sạch pháp lý + có TA: {len(finalists)} | Loại pháp lý: {sum(1 for r in res if r.get('stage')=='loai_phap_ly')}")
    print("--- TOP (FA tốt + sạch + setup TA thuận lợi) ---")
    for r in finalists[:20]:
        tag="↑trend" if r.get("uptrend") else ("↗MA20" if r.get("above_ma20") else "dưới MA20")
        wn=(" ⚠"+",".join(r["legal_warn"][:2])) if r.get("legal_warn") else ""
        bc=(" | CTCK: "+r["broker_consensus"]) if r.get("broker_consensus") else ""
        print(f"  {r['ticker']:5} tổng{r['combined']:>5} | FA{r['fa_score']} ROE{r.get('roe')}% tăngLN{r.get('prof_g')}% "
              f"| TA{r.get('ta_score')} RSI{r.get('rsi')} {tag}{wn}{bc}")

if __name__ == "__main__":
    main()
