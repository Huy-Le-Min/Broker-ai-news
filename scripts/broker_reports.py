# -*- coding: utf-8 -*-
"""
GOM BÁO CÁO PHÂN TÍCH CTCK / QUỸ (web search) — bổ sung cho bản tin sáng.
Tuyển quan điểm MỚI NHẤT (~30 ngày) từ SSI, Vietcap (VCSC), TCBS, VNDIRECT, MBS, HSC,
Rồng Việt (VDSC), KBSV, ACBS, BSC, Mirae Asset, Dragon Capital, VinaCapital...
Chia 4 nhóm: THỊ TRƯỜNG · MÃ CỔ PHIẾU · VĨ MÔ · DỰ BÁO TƯƠNG LAI.

Chạy trên cloud (Gemini free / Claude) — tái dùng cloud_curate. Rẻ: 1 truy vấn tổng.
Ghi: data/broker_reports.json  (pipeline / morning_brief có thể tham chiếu consensus).
Dùng: py scripts/broker_reports.py
"""
import os, sys, json, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

HOUSES = ("SSI Research, Vietcap (VCSC), TCBS, VNDIRECT, MBS, HSC, Rồng Việt (VDSC), "
          "KBSV, ACBS, BSC, Mirae Asset, Dragon Capital, VinaCapital")

SCHEMA = """{
  "date": "__DATE__",
  "as_of": "khoảng thời gian các báo cáo (vd 'nửa cuối T9/2026')",
  "market": [
    {"house":"SSI","view":"tích cực|trung lập|thận trọng","target_vnindex":"vd 1.4xx hoặc null","horizon":"vd cuối 2026","summary":"≤26 từ, luận điểm chính","source":"url|tên báo cáo"}
  ],
  "stocks": [
    {"ticker":"MÃ","house":"...","rating":"MUA|KHẢ QUAN|NẮM GIỮ|TRUNG LẬP|KÉM KHẢ QUAN|BÁN","target_price":"giá mục tiêu (vd 32.500) hoặc null","upside":"±..% so với thị giá hoặc null","thesis":"≤26 từ, 1 câu luận điểm","source":"url|tên báo cáo"}
  ],
  "macro": [
    {"topic":"GDP|CPI|lãi suất|tỷ giá|FDI|tín dụng|xuất khẩu...","house":"...","view":"≤26 từ nhận định","forecast":"số dự báo + mốc thời gian hoặc null","source":"url|tên báo cáo"}
  ],
  "forecasts": [
    {"house":"...","item":"vd VN-Index cuối năm | tăng trưởng LNST toàn thị trường 2026 | nâng hạng thị trường","value":"con số/kịch bản","horizon":"mốc thời gian","source":"url|tên báo cáo"}
  ]
}"""

PROMPT_TMPL = """Hôm nay là __DATE__ (giờ Việt Nam). Bạn là trợ lý tổng hợp BÁO CÁO PHÂN TÍCH cho một broker
tại Việt Nam. Dùng web search tìm quan điểm MỚI NHẤT (ưu tiên trong ~30 NGÀY QUA) từ khối phân tích của
các CTCK & quỹ: __HOUSES__.

Tổng hợp thành 4 nhóm:
1) market  — nhận định TOÀN THỊ TRƯỜNG (xu hướng VN-Index, chiến lược, mục tiêu chỉ số nếu có).
2) stocks  — KHUYẾN NGHỊ CỔ PHIẾU cụ thể (mã, nhà phát hành báo cáo, khuyến nghị, giá mục tiêu, upside, luận điểm 1 câu).
3) macro   — quan điểm VĨ MÔ (GDP, CPI/lạm phát, lãi suất, tỷ giá, tín dụng, FDI, xuất khẩu...).
4) forecasts — DỰ BÁO TƯƠNG LAI có con số/kịch bản (mục tiêu VN-Index cuối năm, tăng trưởng lợi nhuận, nâng hạng...).

QUY TẮC BẮT BUỘC:
- CHỈ lấy nội dung có nguồn thật (báo cáo/bản tin CTCK, hoặc báo tài chính trích dẫn báo cáo: CafeF, Vietstock, VnEconomy, Đầu tư Chứng khoán, Fili...). TUYỆT ĐỐI KHÔNG bịa số, không bịa giá mục tiêu.
- Field "house" ghi rõ CTCK/quỹ nào đưa ra quan điểm. Mỗi mục PHẢI có "source".
- Nếu một con số không chắc chắn / không tra được, để null — KHÔNG đoán.
- Ưu tiên đa dạng nhà phát hành (đừng để 1 CTCK chiếm hết). Gộp trùng: cùng 1 mã nhiều CTCK thì tách dòng theo từng house.
- Súc tích: summary/thesis/view ≤ 26 từ, tiếng Việt có dấu.

Số lượng gợi ý: market 3-5 mục · stocks 8-15 mục · macro 3-6 mục · forecasts 3-6 mục (ít hơn nếu không đủ nguồn thật).

Chỉ trả về DUY NHẤT một object JSON hợp lệ đúng schema sau (không markdown fence, không giải thích):
__SCHEMA__"""


def build_prompt(today):
    return (PROMPT_TMPL
            .replace("__DATE__", today)
            .replace("__HOUSES__", HOUSES)
            .replace("__SCHEMA__", SCHEMA.replace("__DATE__", today)))


def main():
    from cloud_curate import curate_gemini, curate_claude, extract_json
    today = (dt.datetime.utcnow() + dt.timedelta(hours=7)).strftime("%d/%m/%Y")
    prompt = build_prompt(today)
    if os.environ.get("GEMINI_API_KEY"):
        provider, text = "gemini", curate_gemini(prompt)
    elif os.environ.get("ANTHROPIC_API_KEY"):
        provider, text = "claude", curate_claude(prompt)
    else:
        raise SystemExit("Thiếu GEMINI_API_KEY / ANTHROPIC_API_KEY (chạy trên cloud).")

    data = extract_json(text)
    for k in ("market", "stocks", "macro", "forecasts"):
        data.setdefault(k, [])
    data["date"], data["provider"] = today, provider

    # đánh dấu mã thuộc universe (VN100 ∪ watchlist) để pipeline/report ưu tiên
    try:
        from screener_vn100 import get_universe
        uni = set(get_universe())
    except Exception:
        uni = set()
    for s in data["stocks"]:
        s["in_universe"] = s.get("ticker") in uni

    out_path = os.path.join(ROOT, "data", "broker_reports.json")
    json.dump(data, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    n_uni = sum(1 for s in data["stocks"] if s.get("in_universe"))
    print(f"[broker_reports] {provider} · {today} · thị trường {len(data['market'])} · "
          f"cổ phiếu {len(data['stocks'])} ({n_uni} trong universe) · "
          f"vĩ mô {len(data['macro'])} · dự báo {len(data['forecasts'])}")
    for s in data["stocks"][:15]:
        mark = "★" if s.get("in_universe") else " "
        print(f"  {mark} {s.get('ticker','?'):5} {s.get('house','?'):12} "
              f"{s.get('rating','?'):11} TP {s.get('target_price') or '-'}")


if __name__ == "__main__":
    main()
