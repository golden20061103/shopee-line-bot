"""選用：設定 ANTHROPIC_API_KEY 後，由 Claude 閱讀所有抓到的資料並寫出綜合研判。"""
import os

MODEL = os.environ.get("INVEST_AI_MODEL", "claude-opus-5-5")

SYSTEM = (
    "你是嚴謹的投資研究助理。根據使用者提供的即時股價技術指標、個股新聞、財經新聞與政治新聞，"
    "用繁體中文寫出 150 字內的綜合研判：點出最關鍵的利多與利空、它們對該股的可能影響，"
    "最後一行以「AI 建議：買進／持有／賣出」作結。不要捏造資料中沒有的數字。"
)


def ai_commentary(context: str) -> str | None:
    """回傳 Claude 的研判文字；未設定金鑰、未安裝 SDK 或呼叫失敗時回傳 None（系統仍以規則評分運作）。"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic(timeout=60.0)
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM,
            output_config={"effort": "low"},
            # 安全分類器拒答時，伺服器端自動改用其他模型重試
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": context}],
        )
    except anthropic.APIError:
        return None
    if response.stop_reason == "refusal":
        return None
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    return text or None
