# Bộ Context Dùng Chung (Portable)

Đây là "bộ não nền" cho 2 automation tài chính. Mọi AI tool (Claude Code, hay tool khác) đều
đọc các file ở đây để hiểu **nguồn được phép dùng, cách chấm điểm tác động, hồ sơ khách, danh mục,
và disclaimer**. Mục tiêu: không bị khóa vào một công cụ duy nhất — chuyển AI vẫn giữ nguyên ngữ cảnh.

## Bản đồ thư mục

```
E:\Automation\
├─ context\                     ← bộ context dùng chung (file này)
│  ├─ README.md                 ← tổng quan + quy ước
│  ├─ sources.md                ← danh sách nguồn được phép + cách lấy số
│  ├─ rubric.md                 ← khung chấm điểm tác động (đang co-define)
│  ├─ client-profile.template.md← mẫu hồ sơ 1 khách (onboarding)
│  ├─ portfolio.template.csv    ← mẫu danh mục
│  └─ disclaimer.md             ← disclaimer chuẩn gắn vào mọi báo cáo
├─ clients\                     ← mỗi khách 1 thư mục (sau này, multi-client)
│  └─ _me\                      ← danh mục cá nhân của user (MVP)
│     ├─ profile.md
│     └─ portfolio.csv
├─ output\                      ← file Excel + email xuất ra
└─ scripts\                     ← code Python kéo số / gửi mail (Phase 1+)
```

## Hai automation

1. **Keyword → Excel** (on-demand): gõ 1 keyword vĩ mô → kéo số từ `sources.md` →
   xuất 1 workbook nhiều sheet (năm 5y / quý 2y / tháng 12m) + bullet insight.
2. **Digest sáng** (7h, cloud routine): tổng hợp tin từ nguồn cho phép → chấm điểm theo
   `rubric.md` → map vào danh mục → email tiếng Việt dễ hiểu + disclaimer.

## Quy ước

- **Ngôn ngữ output: tiếng Việt**, giải thích dễ hiểu cho khách hàng phổ thông.
- Công cụ ở vai **hỗ trợ ra quyết định**; broker (user) **review & duyệt** trước khi gửi khách.
- Mọi số liệu phải **ghi rõ nguồn + ngày cập nhật**. Mọi ước lượng tác động phải **nêu giả định**.

_Cập nhật: 2026-06-09._
