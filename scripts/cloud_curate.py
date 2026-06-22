# -*- coding: utf-8 -*-
"""
Cloud curate — gọi Claude API (web search) để tuyển 5 tin → ghi JSON cho morning/evening.
Dùng trên GitHub Actions (headless). Cần env ANTHROPIC_API_KEY.
Cách dùng:  py scripts/cloud_curate.py morning   |   py scripts/cloud_curate.py evening
Ghi:  data/brief_today.json (morning)  hoặc  data/evening_today.json (evening)
"""
import os, sys, json, re
from datetime import datetime, timezone, timedelta

import anthropic

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.environ.get("CURATE_MODEL", "claude-sonnet-4-6")

VN_NOW = datetime.now(timezone.utc) + timedelta(hours=7)
TODAY = VN_NOW.strftime("%d/%-m/%Y") if os.name != "nt" else VN_NOW.strftime("%d/%m/%Y")


def read(path):
    p = os.path.join(ROOT, path)
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


PLAYBOOK = read("context/brief_playbook.md")
SOURCES = read("context/sources.md")

MORNING_SCHEMA = """{
  "date": "__DATE__",
  "title": "5 tin cần biết sáng nay",
  "sources": "VnExpress · CafeF · Vietstock · Reuters · CNBC · Trading Economics",
  "snapshot": [
    {"label":"Tỷ giá USD/VND","value":"...","change":"±..%","dir":"up|down|flat"},
    {"label":"Vàng SJC","value":"...","change":"±..%","dir":"up|down|flat"},
    {"label":"Dầu Brent","value":"..$","change":"±..%","dir":"up|down|flat"}
  ],
  "today_watch": "sự kiện/số liệu đáng chú ý HÔM NAY",
  "items": [
    {"cat":"Trong nước","headline":"...","bullets":["...","..."],"insight":"...","source":"..."},
    {"cat":"Trong nước","headline":"...","bullets":["...","..."],"insight":"...","source":"..."},
    {"cat":"Trong nước","headline":"...","bullets":["...","..."],"insight":"...","source":"..."},
    {"cat":"Quốc tế","headline":"...","bullets":["...","..."],"insight":"...","source":"..."},
    {"cat":"Quốc tế","headline":"...","bullets":["...","..."],"insight":"...","source":"..."}
  ],
  "hashtags": ["#BảnTinSáng","#ChứngKhoán","#Vietcap","..."],
  "disclaimer": "Tự động tổng hợp từ nguồn công khai, mang tính tham khảo, không phải khuyến nghị mua/bán."
}"""

EVENING_SCHEMA = """{
  "date": "__DATE__",
  "title": "Điểm lại phiên · tin cuối ngày",
  "sources": "VnExpress · CafeF · Vietstock · Reuters · CNBC",
  "session": {"vnindex_close":"1.8xx,x","vnindex_change":"±x,x%","vnindex_dir":"up|down","foreign_net":"Bán ròng N tỷ | Mua ròng N tỷ","foreign_dir":"buy|sell","volume":"N tỷ","top_gainer":"nhóm/mã dẫn dắt"},
  "snapshot": [
    {"label":"Tỷ giá USD/VND","value":"...","change":"±..%","dir":"up|down|flat"},
    {"label":"Vàng SJC","value":"...","change":"±..%","dir":"up|down|flat"},
    {"label":"Dầu Brent","value":"..$","change":"±..%","dir":"up|down|flat"}
  ],
  "tomorrow_watch": "sự kiện/số liệu đáng chú ý NGÀY MAI",
  "items": [
    {"cat":"Trong nước","headline":"...","bullets":["...","..."],"insight":"...","source":"..."},
    {"cat":"Trong nước","headline":"...","bullets":["...","..."],"insight":"...","source":"..."},
    {"cat":"Trong nước","headline":"...","bullets":["...","..."],"insight":"...","source":"..."},
    {"cat":"Quốc tế","headline":"...","bullets":["...","..."],"insight":"...","source":"..."},
    {"cat":"Quốc tế","headline":"...","bullets":["...","..."],"insight":"...","source":"..."}
  ],
  "hashtags": ["#BảnTinTối","#ChứngKhoán","#Vietcap","..."],
  "disclaimer": "Tự động tổng hợp từ nguồn công khai, mang tính tham khảo, không phải khuyến nghị mua/bán."
}"""


def build_prompt(edition):
    if edition == "evening":
        kind = ("BẢN TIN TỐI (tổng kết phiên giao dịch hôm nay + tin tối). Thêm thống kê phiên: "
                "VN-Index đóng cửa, khối ngoại mua/bán ròng, thanh khoản, nhóm dẫn dắt.")
        schema = EVENING_SCHEMA.replace("__DATE__", TODAY)
    else:
        kind = "BẢN TIN SÁNG (5 tin cần biết quan trọng nhất qua đêm & sáng nay)."
        schema = MORNING_SCHEMA.replace("__DATE__", TODAY)
    return f"""Hôm nay là {TODAY} (giờ Việt Nam). Bạn tạo dữ liệu cho {kind}

Áp dụng PHƯƠNG PHÁP trong playbook dưới đây: quét rộng → chấm điểm tác động → lọc TOP 5 tin
ảnh hưởng mạnh nhất tới TTCK Việt Nam; KHÔNG trùng chủ đề; cân đối trong nước/quốc tế
(3 "Trong nước" + 2 "Quốc tế"); mọi CON SỐ quan trọng đối chiếu ≥2 nguồn, KHÔNG bịa;
"insight" là 1 câu góc nhìn tác động, KHÔNG phải khuyến nghị mua/bán.

GIỚI HẠN ĐỘ DÀI (bắt buộc, vì hiển thị trên thẻ ảnh):
- headline: ≤ 14 từ.
- mỗi bullet: ≤ 28 từ, súc tích; TUYỆT ĐỐI KHÔNG nhét "(nguồn: ...)" trong bullet (đã có field "source").
- insight: ≤ 28 từ, 1 câu.
- today_watch / tomorrow_watch: ≤ 26 từ.
- snapshot.value: CHỈ 1 con số ngắn (vd "26.440", "≈148,7tr", "80,6$") — KHÔNG liệt kê nhiều mức.
- snapshot.change: ngắn gọn dạng "±X%" (vd "-8,5%"), không thêm chữ.

Dùng web search để lấy tin & số liệu MỚI NHẤT (snapshot tỷ giá USD/VND, vàng SJC, dầu Brent).

=== PLAYBOOK ===
{PLAYBOOK[:4000]}

=== NGUỒN ===
{SOURCES[:2000]}

QUAN TRỌNG: Chỉ trả về DUY NHẤT một object JSON hợp lệ đúng schema sau (không kèm giải thích,
không markdown fence). Tiếng Việt có dấu. Giữ nguyên các khóa:
{schema}"""


def extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("Không tìm thấy JSON trong phản hồi")
    return json.loads(m.group(0))


def main():
    edition = (sys.argv[1] if len(sys.argv) > 1 else "morning").strip().lower()
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
        messages=[{"role": "user", "content": build_prompt(edition)}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    data = extract_json(text)
    out = "data/evening_today.json" if edition == "evening" else "data/brief_today.json"
    path = os.path.join(ROOT, out)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[cloud_curate] {edition} -> {out} ({len(data.get('items', []))} tin, ngày {data.get('date')})")


if __name__ == "__main__":
    main()
