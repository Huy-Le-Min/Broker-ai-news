# -*- coding: utf-8 -*-
"""
FA tầng 1 (bổ sung) — RÀ SOÁT PHÁP LÝ BAN LÃNH ĐẠO QUA BÁO CHÍ (web search).
Bổ khuyết cho fa_news.py: CBTT chính thức bỏ sót vụ hình sự cá nhân do báo chí đưa
(vd đồng sáng lập FPT bị khởi tố vụ chính trị). Chạy 1 truy vấn thị-trường-rộng/tối
-> rẻ (không quét từng mã). Chạy trên cloud (Gemini free / Claude), tái dùng cloud_curate.

Ghi: data/leadership_flags.json  (fa_news.py sẽ hợp nhất vào cờ đỏ).
Dùng: py scripts/fa_press_scan.py
"""
import os, sys, json, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

PROMPT = """Bạn là trợ lý rà soát RỦI RO PHÁP LÝ BAN LÃNH ĐẠO cho nhà đầu tư chứng khoán Việt Nam.
Dùng web search nguồn báo chí uy tín (VnExpress, CafeF, Vietstock, Tuổi Trẻ, Thanh Niên...).
Liệt kê các DOANH NGHIỆP NIÊM YẾT VN (HOSE/HNX/UPCOM) mà trong ~30 NGÀY QUA có
CHỦ TỊCH / TỔNG GIÁM ĐỐC / THÀNH VIÊN HĐQT / SÁNG LẬP / NGƯỜI NỘI BỘ bị:
khởi tố, bắt tạm giam, điều tra, truy tố, thao túng chứng khoán, hoặc vấn đề chính trị/pháp lý nghiêm trọng.
QUY TẮC: chỉ lấy tin có nguồn thật; KHÔNG bịa; nêu rõ nếu chỉ là cá nhân liên quan chứ không phải ban điều hành đương nhiệm.
Trả về DUY NHẤT JSON:
{"date":"__DATE__","flags":[{"ticker":"MÃ","company":"...","person":"...","role":"...","issue":"tóm tắt ngắn","severity":"red|warn","date":"YYYY-MM-DD","source":"url"}]}
Nếu không có vụ nào: {"date":"__DATE__","flags":[]}"""

def main():
    from cloud_curate import curate_gemini, curate_claude, extract_json
    today = (dt.datetime.utcnow() + dt.timedelta(hours=7)).strftime("%Y-%m-%d")
    prompt = PROMPT.replace("__DATE__", today)
    if os.environ.get("GEMINI_API_KEY"):
        provider, text = "gemini", curate_gemini(prompt)
    elif os.environ.get("ANTHROPIC_API_KEY"):
        provider, text = "claude", curate_claude(prompt)
    else:
        raise SystemExit("Thiếu GEMINI_API_KEY / ANTHROPIC_API_KEY (chạy trên cloud).")
    data = extract_json(text) or {"flags": []}
    flags = data.get("flags", [])

    # chỉ giữ mã thuộc universe (VN100 ∪ watchlist) + đánh dấu
    try:
        from screener_vn100 import get_universe
        uni = set(get_universe())
    except Exception:
        uni = set()
    for f in flags:
        f["in_universe"] = f.get("ticker") in uni
    out = {"date": today, "provider": provider, "flags": flags}
    json.dump(out, open(os.path.join(ROOT, "data", "leadership_flags.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[fa_press_scan] {provider} · {today} · {len(flags)} cờ lãnh đạo "
          f"({sum(1 for f in flags if f.get('in_universe'))} trong universe)")
    for f in flags:
        mark = "★" if f.get("in_universe") else " "
        print(f"  {mark} {f.get('ticker','?'):5} {f.get('severity','?'):4} {f.get('person','')} — {f.get('issue','')}")

if __name__ == "__main__":
    main()
