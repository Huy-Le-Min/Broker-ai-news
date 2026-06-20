# -*- coding: utf-8 -*-
"""
Build gallery — quét output/brief/ → tạo trang web tĩnh site/ (index.html + ảnh) cho GitHub Pages.
Cách dùng:  py scripts/build_gallery.py
"""
import os, re, shutil, html
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEF = os.path.join(ROOT, "output", "brief")
SITE = os.path.join(ROOT, "site")
PAT = re.compile(r"BanTin(Toi)?_(\d{8})_p(\d+)\.png$")


def parse():
    days = {}
    if not os.path.isdir(BRIEF):
        return []
    for cur, _, files in os.walk(BRIEF):
        for fn in files:
            m = PAT.match(fn)
            if not m:
                continue
            is_ev, tag, page = bool(m.group(1)), m.group(2), int(m.group(3))
            dt = None
            for fmt in ("%d%m%Y", "%Y%m%d"):
                try:
                    dt = datetime.strptime(tag, fmt); break
                except ValueError:
                    pass
            if not dt:
                continue
            dk = dt.strftime("%d/%m/%Y")
            rel = os.path.relpath(os.path.join(cur, fn), BRIEF).replace("\\", "/")
            d = days.setdefault(dk, {"dt": dt, "morning": {}, "evening": {}})
            d["evening" if is_ev else "morning"].setdefault(page, rel)
            # caption đi kèm
            cap = os.path.join(cur, fn.split("_p")[0] + "_caption.txt")
            d["cap_ev" if is_ev else "cap_am"] = os.path.relpath(cap, BRIEF).replace("\\", "/") if os.path.exists(cap) else None
    for d in days.values():
        d["morning"] = [u for _, u in sorted(d["morning"].items())]
        d["evening"] = [u for _, u in sorted(d["evening"].items())]
    return sorted(days.items(), key=lambda x: x[1]["dt"], reverse=True)


def carousel(title, imgs):
    if not imgs:
        return f'<div class="empty">Chưa có {title.lower()}</div>'
    cells = "".join(f'<img loading="lazy" src="brief/{html.escape(u)}" alt="{title}">' for u in imgs)
    return f'<div class="row">{cells}</div>'


def main():
    days = parse()
    # copy ảnh + caption sang site/brief
    site_brief = os.path.join(SITE, "brief")
    if os.path.isdir(site_brief):
        shutil.rmtree(site_brief)
    if os.path.isdir(BRIEF):
        shutil.copytree(BRIEF, site_brief)
    os.makedirs(SITE, exist_ok=True)

    sections = []
    for dk, d in days[:30]:
        cap_links = ""
        if d.get("cap_am"):
            cap_links += f' · <a href="brief/{html.escape(d["cap_am"])}" target="_blank">caption sáng</a>'
        if d.get("cap_ev"):
            cap_links += f' · <a href="brief/{html.escape(d["cap_ev"])}" target="_blank">caption tối</a>'
        sections.append(f"""<section>
  <h2>{dk}{cap_links}</h2>
  <h3>☀️ Bản tin sáng</h3>{carousel("bản tin sáng", d["morning"])}
  <h3>🌙 Bản tin tối</h3>{carousel("bản tin tối", d["evening"])}
</section>""")

    updated = datetime.now().strftime("%d/%m/%Y %H:%M")
    doc = f"""<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vietcap Hub — Bản tin</title>
<style>
:root{{color-scheme:light dark}}
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:920px;margin:0 auto;padding:16px;background:#0f1320;color:#e8eaf0}}
header{{display:flex;align-items:center;gap:10px;border-bottom:1px solid #2a3350;padding-bottom:12px;margin-bottom:8px}}
.logo{{width:34px;height:34px;border-radius:7px;background:#185fa5;display:flex;align-items:center;justify-content:center;font-weight:700}}
h1{{font-size:20px;margin:0}} .sub{{color:#8b93a7;font-size:13px}}
section{{margin:22px 0;border-bottom:1px solid #2a3350;padding-bottom:14px}}
h2{{font-size:17px;margin:6px 0}} h3{{font-size:14px;color:#9fb4d8;margin:14px 0 6px}}
a{{color:#6fb1ff}}
.row{{display:flex;gap:10px;overflow-x:auto;padding-bottom:8px;scroll-snap-type:x mandatory}}
.row img{{height:520px;border-radius:10px;scroll-snap-align:start;border:1px solid #2a3350}}
.empty{{color:#6b7280;font-size:13px;font-style:italic;padding:8px 0}}
footer{{color:#6b7280;font-size:12px;margin-top:24px}}
</style></head><body>
<header><div class="logo">V</div><div><h1>Vietcap Hub — Bản tin</h1>
<div class="sub">Tự động cập nhật mỗi sáng 7h & tối 20:30 · cuộn ngang để xem từng trang</div></div></header>
{''.join(sections) if sections else '<p>Chưa có bản tin nào.</p>'}
<footer>Cập nhật trang: {updated} · Tự động tổng hợp, mang tính tham khảo, không phải khuyến nghị mua/bán.</footer>
</body></html>"""
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"[build_gallery] {len(days)} ngày -> site/index.html")


if __name__ == "__main__":
    main()
