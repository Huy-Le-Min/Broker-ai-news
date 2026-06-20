# Đưa bản tin lên cloud (GitHub Actions) — chạy tự động kể cả khi tắt máy

Mỗi **7:00 sáng** và **20:30 tối** (giờ VN), GitHub tự: gọi Claude API tuyển 5 tin → dựng ảnh →
đăng lên **trang web gallery**. Máy bạn không cần bật.

## Việc bạn làm 1 lần (≈10 phút)

### 1. Tạo repo trên GitHub
- Vào https://github.com/new → đặt tên (vd `vietcap-hub`) → **Private** cũng được → **Create**.
- KHÔNG tick "add README".

### 2. Đẩy code lên (chạy trong `E:\Automation`)
```bash
git remote add origin https://github.com/<TÊN_BẠN>/vietcap-hub.git
git push -u origin main
```

### 3. Cho Actions quyền ghi (để lưu lịch sử bản tin)
Repo → **Settings → Actions → General → Workflow permissions** → chọn
**"Read and write permissions"** → Save.

### 4. Dán API key
- Lấy key tại https://console.anthropic.com → **API Keys** → tạo key, và nạp ít credit (Billing).
- Repo → **Settings → Secrets and variables → Actions → New repository secret**
  - Name: `ANTHROPIC_API_KEY`
  - Secret: dán key vào → **Add secret**.

### 5. Bật GitHub Pages
Repo → **Settings → Pages → Build and deployment → Source = GitHub Actions**.

### 6. Chạy thử
Repo → tab **Actions** → workflow **"ban-tin"** → **Run workflow** → chọn `morning` → **Run**.
- Xong (~2–3 phút) → vào **Settings → Pages** thấy link dạng `https://<tên>.github.io/vietcap-hub/`.
- Mở link trên điện thoại = gallery bản tin (cuộn ngang xem từng trang, tải ảnh để đăng).

## Sau đó
- Lịch **7:00** & **20:30** giờ VN tự chạy (giờ GitHub có thể trễ 5–15 phút, đôi khi lệch — bình thường).
- Mỗi lần chạy tốn rất nhỏ (Claude API ~vài nghìn đồng/bản tin).
- Muốn chạy tay bất cứ lúc nào: Actions → Run workflow → chọn `morning`/`evening`.
- Lịch chạy-trong-app cũ (`ban-tin-sang`, `ban-tin-toi`) giờ không cần nữa — có thể tắt trong app.

## Lưu ý kỹ thuật
- VN-Index trên thẻ snapshot lấy qua `vnstock`; nếu máy chủ GitHub bị chặn thì thẻ đó vắng, các số khác vẫn đủ (Claude lấy qua web search).
- Sửa cách tuyển tin: chỉnh `context/brief_playbook.md` rồi push lại.
