# Danh Sách Nguồn Được Phép

Quy tắc: chỉ lấy số từ các nguồn dưới đây. Nguồn có **API** thì ổn định, ưu tiên dùng.
Nguồn **scrape (web)** dễ gãy khi site đổi giao diện — chấp nhận chi phí bảo trì vì chưa mua data trả phí.

## ⚠️ Thực tế mạng máy user (test 2026-06-09) — QUAN TRỌNG

Python local trên máy user **chỉ vào được một số host**. Đây là ràng buộc lớn quyết định kiến trúc:

| Nguồn | Python local | Ghi chú |
|---|---|---|
| World Bank API | ✅ | dùng `requests` + User-Agent |
| vnstock (VCI) | ✅ | giá cổ phiếu |
| cafef.vn / finance.vietstock.vn / wichart.vn | ✅ | nhưng data nằm trong JS-API (khó bóc) |
| **GSO/NSO** (gso.gov.vn, nso.gov.vn) | ❌ ConnectTimeout | site chặn/không tới được |
| **FRED** (fred.stlouisfed.org) | ❌ Connection/Timeout | KHÔNG phải lỗi key — mạng không tới |
| tradingeconomics.com | ❌ 403 | chặn bot |
| SJC (giá vàng) | ❌ 403 | |
| stooq (vàng thế giới) | ❌ | trả JS-challenge |

→ **WebSearch/WebFetch (Claude chạy) vào được HẾT** (kể cả nso, cafef) vì đi qua hạ tầng Claude, không qua mạng máy user.

## Kiến trúc lấy số — 2 tầng (theo thực tế trên)

- **Tầng A — Python local tự động** (`scripts/automation1_keyword.py`): cổ phiếu (vnstock) + vĩ mô THEO NĂM (World Bank). Chạy `kw <keyword>`. Hoàn toàn tự động, ổn định.
- **Tầng B — Claude fetch lúc chạy** (cho nguồn Python local bị chặn: vàng, dầu, CPI/GDP theo tháng): Claude lấy số bằng WebSearch/WebFetch → ghi `data/<KEY>.json` → `py scripts/snapshot_report.py data/<KEY>.json` ra Excel. Dùng được trong Auto 1 (có Claude) và Auto 2 (cloud agent có tool).

> **Đã loại:** investing.com, FRED (từ máy này), GSO/NSO trực tiếp từ Python local.
> **Domain GSO mới:** `nso.gov.vn` (cũ: gso.gov.vn) — cả 2 đều unreachable từ Python local.

## ⏱️ Tính cập nhật (recency) — quan trọng

World Bank chỉ theo NĂM & trễ ~1–2 năm (hiện ra 2024). Để **tiệm cận hiện tại**, dùng số tháng/quý từ nguồn VN qua **Tầng B (Claude fetch)** và lưu vào `data/macro_latest.json` (Claude/cloud agent refresh). Macro report **dẫn bằng số "MỚI NHẤT"** rồi mới tới xu hướng World Bank.

**Nguồn cập nhật uy tín:**
- **Cục Thống kê / nso.gov.vn** — CPI hàng tháng, GDP hàng quý (chính thống).
- **SBV** — tỷ giá trung tâm hàng ngày; **Vietcombank** — tỷ giá NHTM.
- **CafeF / Vietstock / VnEconomy / VnExpress** — số + phân tích nhanh.

Ví dụ số mới nhất đã fetch (10/6/2026): GDP Q1/2026 +7,83%; CPI T5/2026 +5,6% YoY; tỷ giá TT 25.153.

## Dữ liệu vĩ mô (GDP, CPI, lãi suất, tỷ giá)

| Nguồn | Lấy gì | Cách lấy | Ghi chú |
|---|---|---|---|
| World Bank API | GDP, CPI, dân số... VN | API (free) | Ổn định, chuỗi dài |
| IMF | GDP, lạm phát, dự báo | API/file (free) | Có dự báo để so sánh |
| FRED (St. Louis Fed) | Lãi suất, tỷ giá, dầu, hàng hóa | API (free, cần key free) | Rất ổn định |
| SBV (Ngân hàng Nhà nước) | Tỷ giá trung tâm, lãi suất điều hành | Web (scrape) | Nguồn chính thống VN |
| GSO / Tổng cục Thống kê | CPI, GDP theo tháng/quý VN | Web/PDF (scrape) | Số VN chính thức |

## Giá vàng & hàng hóa

| Nguồn | Lấy gì | Cách lấy |
|---|---|---|
| SJC / PNJ | Giá vàng trong nước | Web (scrape) |
| FRED / EIA | Giá dầu, hàng hóa quốc tế | API (free) |

## Giá cổ phiếu & BCTC (VN)

| Nguồn | Lấy gì | Cách lấy |
|---|---|---|
| `vnstock` (thư viện Python) | Giá HOSE/HNX, BCTC, chỉ số | Python (free) |

## Tin tức (cho digest sáng)

| Nguồn | Loại | Ghi chú |
|---|---|---|
| VnExpress | Tổng hợp + vĩ mô VN | reachable |
| CafeF | Vĩ mô + doanh nghiệp VN | reachable |
| Vietstock | Thị trường + doanh nghiệp | reachable |
| SBV | Chính sách tiền tệ | |
| Bộ Tài chính | Chính sách tài khóa, TTCK | |
| **Bloomberg Businessweek** (thế giới) | Phân tích kinh tế/thị trường quốc tế chiều sâu | bloomberg.com/businessweek — lấy qua Claude WebSearch; bài dài có thể paywall nhưng headline + tóm tắt đọc được |
| **CNBC** (thế giới) | Tin thị trường/vĩ mô quốc tế nhanh | cnbc.com — mở hoàn toàn, lấy qua Claude WebSearch/WebFetch |
| **Trading Economics** (thế giới) | Vĩ mô/thị trường toàn cầu | hay chặn bot (403) → lấy qua Claude WebSearch, hoặc Reuters/Bloomberg index |

> Auto 2 — phong cách bài: kiểu **"X tin cần biết"** của Bloomberg Businessweek VN (Tin trong nước / Tin quốc tế + hashtags + ảnh infographic).

> Cần bổ sung/loại nguồn nào thì sửa file này — cả 2 automation tự theo.

_Cập nhật: 2026-06-09._
