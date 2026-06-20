# Rubric Chấm Điểm Tác Động  — BẢN NHÁP (đang co-define)

> ⚠️ Đây là bản nháp để user và Claude cùng định nghĩa. Mọi con số bên dưới là gợi ý khởi đầu,
> CHƯA chốt. Đây là **ước lượng định tính có giả định**, KHÔNG phải dự báo giá chính xác.

## Công thức tổng quát

Mỗi tin → tính cho từng mã trong danh mục:

```
Điểm tác động (mã) = Hướng × Mức độ × Độ tin cậy × Độ liên quan của mã
```

### 1. Hướng (dấu)
- `+1` Tích cực · `0` Trung tính · `−1` Tiêu cực

### 2. Mức độ (độ lớn sự kiện)
| Nhãn | Hệ số | Ví dụ í
|---|---|---|
| Cao | 3 | Đổi lãi suất điều hành, tỷ giá biến động mạnh, luật mới |
| Vừa | 2 | Số CPI/GDP lệch dự báo vừa phải, tin ngành |
| Thấp | 1 | Tin nền, bình luận thị trường |

### 3. Độ tin cậy nguồn
| Nhãn | Hệ số |
|---|---|
| Chính thống (SBV, Bộ TC, GSO) | 1.0 |
| Báo tài chính uy tín (CafeF, Vietstock) | 0.8 |
| Tin chưa kiểm chứng | 0.4 |

### 4. Độ liên quan của mã (qua ngành + độ nhạy)
Bảng độ nhạy theo chủ đề → ngành (gợi ý khởi đầu, cần user chỉnh theo kinh nghiệm):

| Chủ đề sự kiện | Ngành hưởng lợi (+) | Ngành chịu hại (−) |
|---|---|---|
| Tỷ giá USD/VND tăng | Xuất khẩu (thủy sản, dệt may, gỗ) | DN vay nợ USD lớn, nhập khẩu |
| Lãi suất tăng | Bảo hiểm, ngân hàng (NIM) | BĐS, chứng khoán, DN đòn bẩy cao |
| Giá dầu tăng | Dầu khí (GAS, PVD, PVS) | Vận tải, hàng không, nhựa |
| CPI cao hơn dự báo | (phòng thủ: điện, nước) | Bán lẻ, tiêu dùng không thiết yếu |
| Đầu tư công đẩy mạnh | Xây dựng, VLXD (thép, đá) | — |

→ Mỗi mã gắn 1 mức độ nhạy: Cao (1.0) / Vừa (0.6) / Thấp (0.3) / Không liên quan (0).

## Diễn giải điểm ra chữ (cho khách dễ hiểu)
| |Điểm| | Diễn giải |
|---|---|---|
| Mạnh | ≥ 2.0 | Tác động đáng kể, nên chú ý |
| Vừa | 1.0–2.0 | Tác động trung bình |
| Nhẹ | 0–1.0 | Tác động nhỏ |

## Đã chốt với user (2026-06-09)
- [x] Hệ số Mức độ (3/2/1) & Độ tin cậy (1.0/0.8/0.4): **OK, giữ nguyên.**
- [x] Nhiều tin cùng 1 mã trong ngày: **LIỆT KÊ RIÊNG từng tin, không cộng dồn.**
- [x] Ngưỡng diễn giải Mạnh ≥2.0 / Vừa 1.0–2.0 / Nhẹ <1.0: **OK, giữ nguyên.**
- [x] Bảng độ nhạy ngành: OK bản nháp; user có thể bổ sung dần theo kinh nghiệm.

## Còn để ngỏ (bổ sung dần)
- Thêm chủ đề/ngành vào bảng độ nhạy khi gặp tình huống thực tế.

_Cập nhật: 2026-06-09._
