# -*- coding: utf-8 -*-
"""
Auto 2 — Bản tin sáng "X tin cần biết" dạng CAROUSEL nhiều trang:
  trang 1 = bìa (liệt kê tiêu đề), các trang sau = mỗi tin 1 trang bullet point.
Dữ liệu: data/brief_today.json (Claude/cloud agent fetch & ghi mỗi sáng).
Cách dùng:  py scripts/morning_brief.py
Xuất: output/brief/BanTin_<ngày>_p1..pN.png  +  ..._caption.txt
"""
import os, sys, io, json, contextlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "brief")
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350          # khổ slide dọc 4:5 (chuẩn FB/IG)
PAD = 80
INK = (17, 17, 17)
BLUE = (24, 95, 165)
MUTED = (120, 120, 116)
LIGHT = (240, 240, 236)
CAT_COLORS = {"Trong nước": ((230, 241, 251), (12, 68, 124)),
              "Quốc tế": ((225, 245, 238), (15, 110, 86)),
              "Phiên hôm nay": ((230, 241, 251), (12, 68, 124)),
              "Vĩ mô": ((245, 238, 218), (133, 79, 11)),
              "Thế giới": ((225, 245, 238), (15, 110, 86))}

# Cấu hình "ấn bản" — bản sáng mặc định; bản tối ghi đè (xem evening_brief.py)
EDITION = {"label": "BẢN TIN SÁNG", "logo": "5", "sub": "5 tin cần biết",
           "prefix": "BanTin", "watch_label": "HÔM NAY CHÚ Ý", "band": (17, 17, 17)}


def font(size, bold=False):
    cands = ["arialbd.ttf", "segoeuib.ttf"] if bold else ["arial.ttf", "segoeui.ttf"]
    cands += ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"] if bold else ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    dirs = [r"C:\Windows\Fonts", "/usr/share/fonts/truetype/dejavu",
            "/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype"]
    for d in dirs:
        for f in cands:
            p = os.path.join(d, f)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def get_vnindex():
    """Lấy VN-Index mới nhất + %1 phiên từ vnstock (tự động). None nếu lỗi."""
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            from vnstock.api.quote import Quote
            df = Quote(symbol="VNINDEX", source="VCI").history(
                start="2025-12-01", end=datetime.today().strftime("%Y-%m-%d"), interval="1D")
        last, prev = float(df["close"].iloc[-1]), float(df["close"].iloc[-2])
        chg = (last / prev - 1) * 100
        return {"label": "VN-Index", "value": f"{last:,.1f}", "change": f"{chg:+.1f}%",
                "dir": "up" if chg >= 0 else "down"}
    except Exception:
        return None


def new_slide():
    img = Image.new("RGB", (W, H), "white")
    return img, ImageDraw.Draw(img)


def snapshot_row(d, y, snaps):
    """Vẽ hàng thẻ số liệu nhanh (tối đa 4 thẻ). Trả về y sau hàng."""
    snaps = snaps[:4]
    if not snaps:
        return y
    gap = 18
    cw = (W - 2 * PAD - gap * (len(snaps) - 1)) / len(snaps)
    fl, fv, fc = font(22), font(34, True), font(24, True)
    for i, s in enumerate(snaps):
        x = PAD + i * (cw + gap)
        d.rounded_rectangle([x, y, x + cw, y + 120], 14, fill=LIGHT)
        d.text((x + 18, y + 16), s["label"], font=fl, fill=MUTED)
        d.text((x + 18, y + 46), str(s["value"]), font=fv, fill=INK)
        col = (15, 110, 86) if s.get("dir") == "up" else (163, 45, 45) if s.get("dir") == "down" else MUTED
        d.text((x + 18, y + 88), str(s.get("change", "")), font=fc, fill=col)
    return y + 120 + 24


def header(d, date, right=""):
    band = EDITION["band"]
    d.rectangle([0, 0, W, 150], fill=band)
    d.rounded_rectangle([PAD, 42, PAD + 66, 108], 10, fill=(255, 255, 255))
    d.text((PAD + 18, 46), EDITION["logo"], font=font(52, True), fill=band)
    d.text((PAD + 88, 44), EDITION["label"], font=font(48, True), fill=(255, 255, 255))
    d.text((PAD + 90, 104), f"{EDITION['sub']} · {date}", font=font(24), fill=(200, 200, 200))
    if right:
        d.text((W - PAD - d.textlength(right, font=font(26, True)), 60), right, font=font(26, True), fill=(255, 255, 255))


def footer(d, data, page_hint=""):
    y = H - 132
    d.line([PAD, y, W - PAD, y], fill=LIGHT, width=2)
    y += 16
    fs = font(22)
    for ln in wrap(d, "Nguồn: " + data["sources"], fs, W - 2 * PAD):
        d.text((PAD, y), ln, font=fs, fill=MUTED)
        y += 28
    for ln in wrap(d, data["disclaimer"], fs, W - 2 * PAD):
        d.text((PAD, y), ln, font=fs, fill=MUTED)
        y += 28
    if page_hint:
        d.text((W - PAD - d.textlength(page_hint, font=font(22, True)), H - 150), page_hint, font=font(22, True), fill=BLUE)


def cover(data):
    img, d = new_slide()
    header(d, data["date"])
    y = 184
    snaps = []
    vni = get_vnindex()
    if vni:
        snaps.append(vni)
    snaps += data.get("snapshot", [])
    y = snapshot_row(d, y, snaps)
    fcat, fitem = font(34, True), font(32)
    by_cat = {}
    for i, it in enumerate(data["items"], 1):
        by_cat.setdefault(it["cat"], []).append((i, it["headline"]))
    for cat, lst in by_cat.items():
        d.rectangle([PAD, y + 4, PAD + 8, y + 30], fill=BLUE)
        d.text((PAD + 20, y), cat.upper(), font=fcat, fill=BLUE)
        y += 52
        for num, hl in lst:
            for k, ln in enumerate(wrap(d, f"{num}. {hl}", fitem, W - 2 * PAD - 10)):
                d.text((PAD + (0 if k == 0 else 28), y), ln, font=fitem, fill=INK)
                y += 44
            y += 12
        y += 12
    tw = data.get("today_watch")
    if tw:
        tb = font(26)
        lines = wrap(d, tw, tb, W - 2 * PAD - 36)
        box_h = 56 + len(lines) * 36
        d.rounded_rectangle([PAD, y, W - PAD, y + box_h], 14, fill=(230, 241, 251))
        d.text((PAD + 18, y + 14), EDITION["watch_label"], font=font(24, True), fill=BLUE)
        yy = y + 50
        for ln in lines:
            d.text((PAD + 18, yy), ln, font=tb, fill=INK)
            yy += 36
    d.text((PAD, H - 200), "Vuốt xem chi tiết từng tin →", font=font(26, True), fill=BLUE)
    footer(d, data)
    return img


def detail(data, idx):
    it = data["items"][idx]
    img, d = new_slide()
    header(d, data["date"], right=f"TIN {idx + 1}/{len(data['items'])}")
    y = 210
    bg, tx = CAT_COLORS.get(it["cat"], (LIGHT, INK))
    pill = it["cat"]
    pw = d.textlength(pill, font=font(24, True)) + 36
    d.rounded_rectangle([PAD, y, PAD + pw, y + 44], 22, fill=bg)
    d.text((PAD + 18, y + 8), pill, font=font(24, True), fill=tx)
    y += 72
    for ln in wrap(d, it["headline"], font(46, True), W - 2 * PAD):
        d.text((PAD, y), ln, font=font(46, True), fill=INK)
        y += 60
    y += 24
    fb = font(33)
    for b in it["bullets"]:
        d.ellipse([PAD + 2, y + 12, PAD + 14, y + 24], fill=BLUE)
        for k, ln in enumerate(wrap(d, b, fb, W - 2 * PAD - 36)):
            d.text((PAD + 32, y), ln, font=fb, fill=INK)
            y += 46
        y += 18
    ins = it.get("insight")
    if ins:
        fi = font(30)
        lines = wrap(d, ins, fi, W - 2 * PAD - 36)
        bh = 24 + len(lines) * 40
        d.rounded_rectangle([PAD, y + 8, W - PAD, y + 8 + bh], 14, fill=(255, 247, 230))
        yy = y + 20
        for ln in lines:
            d.text((PAD + 20, yy), ln, font=fi, fill=INK)
            yy += 40
    footer(d, data, page_hint=f"{idx + 2}/{len(data['items']) + 1}")
    return img


def caption(data):
    L = [f"📌 {data['title'].upper()} ({data['date']})"]
    snaps = data.get("snapshot", [])
    if snaps:
        L.append("📈 " + "  |  ".join(f"{s['label']} {s['value']} ({s.get('change','')})" for s in snaps))
    cur = None
    for i, it in enumerate(data["items"], 1):
        if it["cat"] != cur:
            cur = it["cat"]
            flag = "🇻🇳" if cur == "Trong nước" else "🌏"
            L += ["", f"{flag} {cur.upper()}:"]
        L.append(f"{i}. {it['headline']}")
        L += [f"   • {b}" for b in it["bullets"]]
        if it.get("insight"):
            L.append(f"   → {it['insight']}")
    if data.get("today_watch"):
        L += ["", "⏰ Hôm nay chú ý: " + data["today_watch"]]
    L += ["", " ".join(data["hashtags"]), "", "Nguồn: " + data["sources"], data["disclaimer"]]
    return "\n".join(L)


def generate(data_path):
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = datetime.today().strftime("%d%m%Y")
    daydir = os.path.join(OUT, datetime.today().strftime("%d-%m-%y"))
    os.makedirs(daydir, exist_ok=True)
    pre = EDITION["prefix"]
    paths = []
    cv = os.path.join(daydir, f"{pre}_{tag}_p1.png")
    cover(data).save(cv)
    paths.append(cv)
    for i in range(len(data["items"])):
        pp = os.path.join(daydir, f"{pre}_{tag}_p{i + 2}.png")
        detail(data, i).save(pp)
        paths.append(pp)
    cap = os.path.join(daydir, f"{pre}_{tag}_caption.txt")
    with open(cap, "w", encoding="utf-8") as f:
        f.write(caption(data))
    print(f"Đã xuất {len(paths)} trang ảnh:")
    for p_ in paths:
        print("  -", p_)
    print("Caption:", cap)
    return paths


def main():
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "brief_today.json")
    generate(p)


if __name__ == "__main__":
    main()
