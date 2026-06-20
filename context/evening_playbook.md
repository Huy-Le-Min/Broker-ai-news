# Playbook — Bản tin tối "Điểm lại phiên · 5 tin cuối ngày"

Mục tiêu: **tổng kết phiên VN + tin quan trọng đã xảy ra hôm nay + nhìn ra thế giới cuối chiều.**
Chạy lúc ~20:30 mỗi ngày. KHÔNG vớ đại tin — chọn đúng theo rubric.

## Bước 1 — Lấy dữ liệu phiên VN (VN-Index script tự lấy, Claude lấy phần còn lại)

Tìm từ CafeF (cafef.vn) hoặc Vietstock (finance.vietstock.vn) mục "Thị trường hôm nay":
- **Khối ngoại**: mua/bán ròng tổng hợp HOSE hôm nay (đơn vị tỷ đồng) + hướng (buy/sell/flat)
- **Thanh khoản**: tổng giá trị khớp lệnh HOSE hôm nay (tỷ đồng)
- **Top gainer**: mã tăng mạnh nhất phiên (ví dụ "VHM +6.8%")
- **Top loser**: mã giảm mạnh nhất phiên (ví dụ "HPG -3.2%")

## Bước 2 — Quét 12–20 tin ứng viên từ HÔM NAY

Nguồn: VnExpress, CafeF, Vietstock (VN) + Reuters, Bloomberg, CNBC (quốc tế).
Chỉ lấy tin **trong 24h qua**, ưu tiên tin **đã ảnh hưởng đến phiên hôm nay** hoặc **sẽ ảnh hưởng ngày mai**.

Nhóm cần quét (giống sáng, nhưng focus vào tin ĐÃ CÓ KẾT QUẢ hôm nay):
- Lãi suất & CSTT
- Ngân hàng (KQKD, tín dụng, nợ xấu)
- Vĩ mô VN (số liệu mới công bố hôm nay)
- Tỷ giá & dòng vốn ngoại
- Chính sách (nghị định, quyết định mới ký)
- Vàng & hàng hóa (close cuối ngày)
- Doanh nghiệp lớn (thông báo, KQKD)
- Thế giới (US futures, EU close, sự kiện toàn cầu)

## Bước 3 — Chấm điểm & Lọc TOP 5

Dùng rubric.md (Phạm vi × Mức độ × Thời sự × Liên quan TTCK VN × Độ tin cậy).
- 3 tin Trong nước + 2 tin Quốc tế (luôn có ≥1 quốc tế).
- Ưu tiên tin giải thích được **tại sao phiên hôm nay diễn ra như vậy**.

## Bước 4 — Viết mỗi tin

- Tiêu đề ngắn + 2–3 bullet (số liệu cụ thể, đối chiếu ≥2 nguồn) + 1 câu insight + nguồn.
- Insight hướng về **ý nghĩa ngày mai / phiên tới**, KHÔNG phải khuyến nghị.

## Bước 5 — Snapshot cuối ngày

- **USD/VND**: tỷ giá Vietcombank chiều hôm nay
- **Vàng SJC**: giá đóng cửa / chiều hôm nay
- **Dầu Brent**: giá hiện tại (close hoặc pre-market US)
- **DJI Futures**: chỉ số tương lai Dow Jones (US pre-market, ±%)

## Bước 6 — tomorrow_watch

1 câu ngắn: số liệu kinh tế sẽ công bố ngày mai hoặc sự kiện quan trọng cần chú ý.
Ví dụ: "Fed họp lúc 2am — thị trường chờ tín hiệu lãi suất; CPI VN tháng 6 dự kiến 14h."

_Sửa file này để đổi cách tuyển tin buổi tối._
