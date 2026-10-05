"""綜合評分：技術面 + 個股新聞 + 大盤/總經 + 財經新聞 + 政治新聞 → 買賣建議。"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from .ai import ai_commentary
from .data import fetch_news, resolve_symbol
from .indicators import macd, pct_change, rsi, sma
from .macro import FINANCE_QUERIES, POLITICS_QUERIES, market_factor, news_factor
from .sentiment import score_news

# 各因素權重（合計 1.0）
WEIGHTS = {
    "technical": 0.35,
    "stock_news": 0.20,
    "market": 0.20,
    "finance_news": 0.10,
    "politics_news": 0.15,
}
LABELS = {
    "technical": "技術面",
    "stock_news": "個股新聞",
    "market": "大盤/總經",
    "finance_news": "財經新聞",
    "politics_news": "政治因素",
}
DISCLAIMER = "⚠️ 本分析由程式依公開網路資料自動產生，僅供參考，不構成投資建議，投資請自行判斷並承擔風險。"


def technical_factor(closes: list[float]) -> dict:
    price = closes[-1]
    ma20, ma60 = sma(closes, 20), sma(closes, 60)
    r = rsi(closes)
    m = macd(closes)
    chg20 = pct_change(closes, 20)
    score, notes = 0.0, []
    if ma20:
        score += 0.25 if price > ma20 else -0.25
        notes.append(f"股價{'站上' if price > ma20 else '跌破'}月線 ({ma20:.2f})")
    if ma20 and ma60:
        score += 0.25 if ma20 > ma60 else -0.25
        notes.append("均線多頭排列" if ma20 > ma60 else "均線空頭排列")
    if r is not None:
        if r > 70:
            score -= 0.3
            notes.append(f"RSI {r:.0f} 過熱，留意拉回")
        elif r < 30:
            score += 0.3
            notes.append(f"RSI {r:.0f} 超賣，可能反彈")
        else:
            notes.append(f"RSI {r:.0f} 中性")
    if m:
        score += 0.2 if m[0] > m[1] else -0.2
        notes.append("MACD 黃金交叉（偏多）" if m[0] > m[1] else "MACD 死亡交叉（偏空）")
    if chg20 is not None:
        score += max(-0.3, min(0.3, chg20 / 20))
        notes.append(f"近20日漲跌 {chg20:+.1f}%")
    return {"score": max(-1.0, min(1.0, score / 1.3)), "notes": notes, "rsi": r, "ma20": ma20, "ma60": ma60}


def verdict(total: float) -> str:
    if total >= 40:
        return "🟢🟢 強力買進"
    if total >= 15:
        return "🟢 買進"
    if total > -15:
        return "🟡 持有／觀望"
    if total > -40:
        return "🔴 賣出"
    return "🔴🔴 強力賣出"


def analyze(user_input: str, use_ai: bool = True) -> dict | None:
    """分析單一股票。輸入台股代號（2330）或美股代號（AAPL）。查無代號回傳 None。"""
    stock = resolve_symbol(user_input)
    if not stock:
        return None
    is_taiwan = stock["symbol"].endswith((".TW", ".TWO"))
    code = stock["symbol"].split(".")[0]
    stock_query = f"{code} 股價" if is_taiwan else f"{code} {stock['name']} stock"

    with ThreadPoolExecutor(4) as ex:
        f_news = ex.submit(fetch_news, stock_query, 15)
        f_market = ex.submit(market_factor, is_taiwan)
        f_fin = ex.submit(news_factor, FINANCE_QUERIES)
        f_pol = ex.submit(news_factor, POLITICS_QUERIES)
        stock_items = f_news.result()
        factors = {
            "technical": technical_factor(stock["closes"]),
            "stock_news": {**score_news(stock_items), "items": stock_items},
            "market": f_market.result(),
            "finance_news": f_fin.result(),
            "politics_news": f_pol.result(),
        }

    total = 100 * sum(WEIGHTS[k] * factors[k]["score"] for k in WEIGHTS)
    result = {
        "stock": stock,
        "is_taiwan": is_taiwan,
        "factors": factors,
        "total": total,
        "verdict": verdict(total),
        "generated_at": datetime.now(timezone.utc),
        "ai": None,
    }
    if use_ai:
        result["ai"] = ai_commentary(_ai_context(result))
    return result


def _top_headlines(factor: dict, n: int = 3) -> list[tuple[int, str]]:
    """挑情緒最強烈的標題（正負都取），讓使用者看到分數背後的依據。"""
    scored = sorted(factor.get("scored", []), key=lambda x: abs(x[0]), reverse=True)
    return [s for s in scored if s[0] != 0][:n]


def _ai_context(r: dict) -> str:
    s, f = r["stock"], r["factors"]
    lines = [f"股票：{s['name']} ({s['symbol']}) 現價 {s['closes'][-1]:.2f} {s['currency']}"]
    lines.append("技術面：" + "；".join(f["technical"]["notes"]))
    lines.append("大盤/總經：" + "；".join(f["market"]["notes"]))
    for key in ("stock_news", "finance_news", "politics_news"):
        lines.append(f"\n【{LABELS[key]}】")
        lines += [f"- {it['title']}" for it in f[key]["items"][:15]]
    lines.append(f"\n規則模型綜合分數：{r['total']:+.0f}（-100~+100），結論：{r['verdict']}")
    return "\n".join(lines)


def _bar(score: float) -> str:
    n = round(abs(score) * 5)
    return ("+" if score >= 0 else "-") * n or "0"


def format_report(r: dict) -> str:
    s, f = r["stock"], r["factors"]
    meta = s["meta"]
    price = s["closes"][-1]
    day_chg = pct_change(s["closes"], 1)
    lines = [
        f"📊 {s['name']} ({s['symbol']})",
        f"現價 {price:,.2f} {s['currency']}" + (f"（{day_chg:+.2f}%）" if day_chg is not None else ""),
    ]
    if meta.get("fiftyTwoWeekHigh"):
        lines.append(f"52週區間 {meta['fiftyTwoWeekLow']:,.2f} ~ {meta['fiftyTwoWeekHigh']:,.2f}")
    lines += ["", f"🧭 綜合評分：{r['total']:+.0f} / 100", f"👉 建議：{r['verdict']}", "", "【各因素分數】"]
    for k in WEIGHTS:
        lines.append(f"{LABELS[k]}（權重{WEIGHTS[k]:.0%}）：{f[k]['score'] * 100:+.0f}  {_bar(f[k]['score'])}")

    lines += ["", "📈 技術面"] + [f"• {n}" for n in f["technical"]["notes"]]
    if f["market"]["notes"]:
        lines += ["", "🌐 大盤/總經"] + [f"• {n}" for n in f["market"]["notes"]]
    for key, icon in (("stock_news", "📰"), ("finance_news", "💰"), ("politics_news", "🏛️")):
        fac = f[key]
        lines += ["", f"{icon} {LABELS[key]}（利多{fac['pos']}／利空{fac['neg']}／中性{fac['neu']}）"]
        heads = _top_headlines(fac)
        lines += [f"{'🔺' if sc > 0 else '🔻'} {t}" for sc, t in heads] or ["• 無明顯情緒新聞"]

    if r.get("ai"):
        lines += ["", "🤖 AI 綜合研判", r["ai"]]
    lines += ["", DISCLAIMER]
    return "\n".join(lines)
