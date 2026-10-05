"""網路資料抓取：Yahoo Finance 股價、Google News 新聞（皆免 API key）。"""
import re
import urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

# Yahoo 會對完整瀏覽器 UA 回 429，用簡短 UA 反而穩定
UA = {"User-Agent": "Mozilla/5.0"}
YAHOO_HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]
YAHOO_CHART = "https://{host}/v8/finance/chart/{symbol}"
GOOGLE_NEWS = "https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
TIMEOUT = 10


def fetch_prices(symbol: str, range_: str = "1y", interval: str = "1d") -> dict | None:
    """回傳 {'symbol','name','currency','closes','volumes','meta'}；查無資料回傳 None。"""
    result = None
    for host in YAHOO_HOSTS:
        url = YAHOO_CHART.format(host=host, symbol=urllib.parse.quote(symbol))
        try:
            r = requests.get(url, params={"range": range_, "interval": interval}, headers=UA, timeout=TIMEOUT)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            result = (r.json().get("chart") or {}).get("result")
            break
        except (requests.RequestException, ValueError):
            continue
    if not result:
        return None
    res = result[0]
    quote = res.get("indicators", {}).get("quote", [{}])[0]
    rows = zip(res.get("timestamp") or [], quote.get("close") or [], quote.get("volume") or [])
    pairs = [(c, v or 0, t) for t, c, v in rows if c is not None]
    if not pairs:
        return None
    meta = res.get("meta", {})
    return {
        "symbol": meta.get("symbol", symbol),
        "name": meta.get("shortName") or meta.get("longName") or symbol,
        "currency": meta.get("currency", ""),
        "closes": [p[0] for p in pairs],
        "volumes": [p[1] for p in pairs],
        "timestamps": [p[2] for p in pairs],
        "meta": meta,
    }


def resolve_symbol(user_input: str) -> dict | None:
    """把使用者輸入轉成 Yahoo 代號並抓價格。純數字視為台股（先上市 .TW，再上櫃 .TWO）。"""
    s = user_input.strip().upper()
    candidates = [f"{s}.TW", f"{s}.TWO"] if re.fullmatch(r"\d{4,6}[A-Z]?", s) else [s]
    for sym in candidates:
        data = fetch_prices(sym)
        if data:
            return data
    return None


def fetch_news(query: str, limit: int = 15, days: int = 7) -> list[dict]:
    """Google News RSS 搜尋最近 days 天的新聞，回傳 [{'title','source','published','link'}]。"""
    url = GOOGLE_NEWS.format(q=urllib.parse.quote(f"{query} when:{days}d"))
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except (requests.RequestException, ET.ParseError):
        return []
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        source = (item.findtext("source") or "").strip()
        # Google News 標題結尾會附「 - 來源」，去掉以免干擾情緒判讀
        if source and title.endswith(f" - {source}"):
            title = title[: -len(source) - 3]
        try:
            published = parsedate_to_datetime(item.findtext("pubDate") or "")
        except (TypeError, ValueError):
            published = None
        items.append({"title": title, "source": source, "published": published, "link": item.findtext("link") or ""})
        if len(items) >= limit:
            break
    return items
