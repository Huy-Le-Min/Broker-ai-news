# -*- coding: utf-8 -*-
"""
Vietcap Automation Hub
Chạy: py run_app.bat  (từ E:\Automation)
Mở:  http://localhost:8080
"""
import os, re, sys, time, asyncio
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
PY = sys.executable

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Vietcap Hub")
app.mount("/output", StaticFiles(directory=str(ROOT / "output")), name="output")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

BRIEF_DIR = ROOT / "output" / "brief"
OUTPUT_DIR = ROOT / "output"


def parse_briefs():
    """Quét output/brief/, trả về list [{date, dt, morning:[urls], evening:[urls]}] mới nhất trước.
    Dedup theo page number khi cùng ngày có nhiều format tên file (YYYYMMDD và DDMMYYYY)."""
    if not BRIEF_DIR.exists():
        return []
    result = {}
    for fpath in sorted(BRIEF_DIR.rglob("BanTin*.png")):
        m = re.match(r"BanTin(Toi)?_(\d{8})_p(\d+)\.png$", fpath.name)
        if not m:
            continue
        is_ev = bool(m.group(1))
        tag, page = m.group(2), int(m.group(3))
        dt = None
        for fmt in ("%d%m%Y", "%Y%m%d"):
            try:
                dt = datetime.strptime(tag, fmt)
                break
            except ValueError:
                pass
        if not dt:
            continue
        dk = dt.strftime("%d/%m/%Y")
        if dk not in result:
            result[dk] = {"date": dk, "dt": dt, "morning": {}, "evening": {}}
        pages = result[dk]["evening" if is_ev else "morning"]
        pages.setdefault(page, "/output/" + fpath.relative_to(OUTPUT_DIR).as_posix())
    for v in result.values():
        v["morning"] = [u for _, u in sorted(v["morning"].items())]
        v["evening"] = [u for _, u in sorted(v["evening"].items())]
    return sorted(result.values(), key=lambda x: x["dt"], reverse=True)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    briefs = parse_briefs()
    latest = briefs[0] if briefs else {}
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "morning": latest.get("morning", []),
            "evening": latest.get("evening", []),
            "briefs": briefs,
            "today": datetime.today().strftime("%d/%m/%Y"),
        },
    )


async def _run(script: str, *args):
    env = {**os.environ, "PYTHONUTF8": "1"}
    proc = await asyncio.create_subprocess_exec(
        PY, script, *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env, cwd=str(ROOT),
    )
    out, err = await asyncio.wait_for(proc.communicate(), timeout=300)
    return {
        "ok": proc.returncode == 0,
        "stdout": out.decode("utf-8", "replace"),
        "stderr": err.decode("utf-8", "replace"),
    }


@app.post("/api/run/morning")
async def run_morning():
    return JSONResponse(await _run(str(ROOT / "scripts" / "morning_brief.py")))


@app.post("/api/run/evening")
async def run_evening():
    return JSONResponse(await _run(str(ROOT / "scripts" / "evening_brief.py")))


@app.post("/api/run/keyword")
async def run_keyword(request: Request):
    body = await request.json()
    kws = [k.strip() for k in body.get("keywords", []) if k.strip()]
    if not kws:
        return JSONResponse({"ok": False, "error": "Thiếu keywords"}, status_code=400)
    t0 = time.time()
    r = await _run(str(ROOT / "scripts" / "automation1_keyword.py"), *kws)
    # Tìm file xlsx vừa tạo (trong 2 phút vừa qua)
    r["files"] = sorted(
        f"/output/{p.name}"
        for p in OUTPUT_DIR.glob("*.xlsx")
        if p.stat().st_mtime >= t0 - 30
    )
    return JSONResponse(r)


@app.on_event("startup")
async def _open_browser():
    """Tự mở trình duyệt sau 1s khi server khởi động."""
    async def _open():
        await asyncio.sleep(1)
        import webbrowser
        webbrowser.open("http://localhost:8080")
    asyncio.create_task(_open())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
