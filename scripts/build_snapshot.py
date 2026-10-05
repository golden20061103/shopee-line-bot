"""產生可離線瀏覽的靜態快照頁：python scripts/build_snapshot.py 2330 0050 NVDA ...
輸出 dist/snapshot.html（資料內嵌，不需伺服器）。"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from invest import analyze, to_dict  # noqa: E402

DEFAULT = ["2330", "0050", "2454", "2317", "NVDA", "AAPL"]


def main(symbols: list[str]) -> None:
    with ThreadPoolExecutor(3) as ex:
        results = list(ex.map(lambda s: analyze(s, use_ai=True), symbols))
    reports = {s: to_dict(r) for s, r in zip(symbols, results) if r}
    missing = [s for s, r in zip(symbols, results) if not r]
    if missing:
        print("找不到：", ", ".join(missing))
    snapshot = {"generated_at": datetime.now(timezone.utc).isoformat(), "reports": reports}
    data = json.dumps(snapshot, ensure_ascii=False).replace("</", "<\\/")
    page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    out = ROOT / "dist" / "snapshot.html"
    out.parent.mkdir(exist_ok=True)
    marker = "<script>\n(() => {"
    out.write_text(page.replace(marker, f"<script>window.__SNAPSHOT__ = {data};</script>\n{marker}", 1), encoding="utf-8")
    print(f"已輸出 {out}（{len(reports)} 檔）")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)
