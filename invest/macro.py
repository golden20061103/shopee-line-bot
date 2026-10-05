"""大盤、總體經濟與政治因素。"""
from concurrent.futures import ThreadPoolExecutor

from .data import fetch_news, fetch_prices
from .indicators import pct_change, sma
from .sentiment import score_news

# 新聞搜尋主題：財經 / 政治（Google News 關鍵字）
FINANCE_QUERIES = ["聯準會 利率 股市", "台股 外資 盤勢", "美股 財報 經濟數據"]
POLITICS_QUERIES = ["關稅 貿易戰 股市", "台海 地緣政治 股市", "選舉 政策 股市", "戰爭 制裁 市場"]


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def market_factor(is_taiwan: bool) -> dict:
    """大盤趨勢 + VIX 恐慌指數 + 美債殖利率 (+ 台股看新台幣匯率)。分數 -1~1。"""
    symbols = {"index": "^TWII" if is_taiwan else "^GSPC", "vix": "^VIX", "tnx": "^TNX"}
    if is_taiwan:
        symbols["fx"] = "TWD=X"
    with ThreadPoolExecutor(len(symbols)) as ex:
        data = dict(zip(symbols, ex.map(lambda s: fetch_prices(s, "6mo"), symbols.values())))

    parts, notes = [], []
    idx = data.get("index")
    if idx:
        c = idx["closes"]
        ma60 = sma(c, 60)
        chg20 = pct_change(c, 20) or 0
        trend = (0.5 if ma60 and c[-1] > ma60 else -0.5) + _clamp(chg20 / 10, -0.5, 0.5)
        parts.append(trend)
        notes.append(f"大盤{'站上' if ma60 and c[-1] > ma60 else '跌破'}季線，近20日 {chg20:+.1f}%")
    vix = data.get("vix")
    if vix:
        v = vix["closes"][-1]
        parts.append(0.5 if v < 15 else 0.0 if v < 20 else -0.5 if v < 30 else -1.0)
        notes.append(f"VIX 恐慌指數 {v:.1f}（{'平穩' if v < 20 else '偏高' if v < 30 else '恐慌'}）")
    tnx = data.get("tnx")
    if tnx:
        chg = pct_change(tnx["closes"], 20) or 0
        parts.append(_clamp(-chg / 10))  # 殖利率急升壓抑股市評價
        notes.append(f"美國10年債殖利率 {tnx['closes'][-1]:.2f}%（20日 {chg:+.1f}%）")
    fx = data.get("fx")
    if fx:
        chg = pct_change(fx["closes"], 20) or 0
        parts.append(_clamp(-chg / 2))  # USD/TWD 下跌 = 台幣升值 = 熱錢流入
        notes.append(f"美元/台幣 {fx['closes'][-1]:.2f}（20日 {chg:+.1f}%，{'台幣升值' if chg < 0 else '台幣貶值'}）")

    score = sum(parts) / len(parts) if parts else 0.0
    return {"score": _clamp(score), "notes": notes}


def news_factor(queries: list[str], per_query: int = 10) -> dict:
    with ThreadPoolExecutor(len(queries)) as ex:
        batches = list(ex.map(lambda q: fetch_news(q, per_query), queries))
    seen, items = set(), []
    for batch in batches:
        for it in batch:
            if it["title"] not in seen:
                seen.add(it["title"])
                items.append(it)
    ignore = frozenset(word for q in queries for word in q.split())
    result = score_news(items, ignore)
    result["items"] = items
    return result
