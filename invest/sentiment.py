"""新聞標題情緒分析：中英文關鍵字詞典法（免費、離線）。設定 ANTHROPIC_API_KEY 時另有 AI 綜合研判（見 ai.py）。"""

POSITIVE = [
    "上漲", "大漲", "漲停", "飆", "創新高", "新高", "利多", "看好", "成長", "增長", "獲利", "賺", "轉盈",
    "優於預期", "超預期", "樂觀", "回升", "反彈", "買超", "加碼", "上修", "調升", "擴產", "訂單", "強勁", "走揚", "走高", "收紅", "天價",
    "降息", "寬鬆", "停火", "和談", "協議", "達成共識", "紓困", "刺激", "突破", "旺", "復甦", "亮眼",
    "surge", "soar", "rally", "beat", "upgrade", "record high", "bullish", "growth", "profit", "rate cut",
]
NEGATIVE = [
    "下跌", "大跌", "重挫", "暴跌", "跌停", "崩", "創新低", "利空", "看壞", "衰退", "虧損", "轉虧", "低於預期",
    "不如預期", "悲觀", "賣超", "減碼", "下修", "調降", "砍單", "疲弱", "升息", "緊縮", "通膨", "制裁",
    "關稅", "貿易戰", "戰爭", "衝突", "開戰", "飛彈", "軍演", "緊張", "危機", "違約", "倒閉", "裁員",
    "調查", "罰款", "禁令", "管制", "封鎖", "停工", "動盪", "疑慮", "警告", "風險", "泡沫", "拋售",
    "plunge", "slump", "crash", "miss", "downgrade", "bearish", "recession", "tariff", "sanction", "war",
]
NEGATORS = ["不", "未", "沒有", "無", "停止", "解除", "暫緩", "取消", "緩解", "減緩", "擺脫", "降溫"]


def score_text(text: str, ignore: frozenset[str] = frozenset()) -> int:
    """單則標題分數：正詞 +1、負詞 -1；前方三字內有否定詞則反轉（例：「解除制裁」視為正面）。
    ignore：不計分的詞，通常是搜尋關鍵字本身（搜「關稅」的新聞幾乎都含「關稅」，不代表利空）。"""
    t = text.lower()
    score = 0
    for words, sign in ((POSITIVE, 1), (NEGATIVE, -1)):
        for w in words:
            if w in ignore:
                continue
            idx = t.find(w.lower())
            if idx < 0:
                continue
            prefix = t[max(0, idx - 3):idx]
            score += -sign if any(n in prefix for n in NEGATORS) else sign
    return score


def score_news(items: list[dict], ignore: frozenset[str] = frozenset()) -> dict:
    """回傳 {'score': -1~1, 'pos','neg','neu', 'scored': [(分數, 標題)]}。"""
    scored = [(score_text(it["title"], ignore), it["title"]) for it in items]
    pos = sum(1 for s, _ in scored if s > 0)
    neg = sum(1 for s, _ in scored if s < 0)
    neu = len(scored) - pos - neg
    # 以有情緒傾向的新聞比例計分；中性新聞稀釋分數，避免少量新聞就給出極端值
    score = (pos - neg) / (pos + neg + 0.5 * neu + 1) if scored else 0.0
    return {"score": max(-1.0, min(1.0, score)), "pos": pos, "neg": neg, "neu": neu, "scored": scored}
