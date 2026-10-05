"""離線單元測試：python -m unittest discover tests"""
import unittest

from invest.analyzer import technical_factor, verdict
from invest.indicators import macd, pct_change, rsi, sma
from invest.sentiment import score_news, score_text


class IndicatorTest(unittest.TestCase):
    def test_sma_and_pct(self):
        self.assertEqual(sma([1, 2, 3, 4], 2), 3.5)
        self.assertIsNone(sma([1], 5))
        self.assertAlmostEqual(pct_change([100, 110], 1), 10.0)

    def test_rsi_extremes(self):
        self.assertEqual(rsi(list(range(1, 30))), 100.0)
        self.assertLess(rsi(list(range(30, 1, -1))), 1)

    def test_macd_uptrend(self):
        line, signal = macd([float(i) for i in range(60)])
        self.assertGreater(line, 0)

    def test_technical_direction(self):
        up = [100 * 1.01 ** i for i in range(120)]
        self.assertGreater(technical_factor(up)["score"], 0)
        self.assertLess(technical_factor(up[::-1])["score"], 0)


class SentimentTest(unittest.TestCase):
    def test_keywords(self):
        self.assertGreater(score_text("台積電股價創新高 外資加碼"), 0)
        self.assertLess(score_text("美國宣布新關稅 股市重挫"), 0)

    def test_negation(self):
        self.assertGreater(score_text("美國宣布解除制裁"), 0)

    def test_ignore_query_terms(self):
        self.assertEqual(score_text("關稅談判今日登場", frozenset({"關稅"})), 0)

    def test_score_news_range(self):
        items = [{"title": t} for t in ["大漲", "大漲", "重挫", "今日開會"]]
        s = score_news(items)
        self.assertTrue(-1 <= s["score"] <= 1)
        self.assertEqual((s["pos"], s["neg"], s["neu"]), (2, 1, 1))

    def test_verdict_thresholds(self):
        self.assertIn("強力買進", verdict(50))
        self.assertIn("持有", verdict(0))
        self.assertIn("強力賣出", verdict(-50))


if __name__ == "__main__":
    unittest.main()
