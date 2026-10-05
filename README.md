# 柏君選物 LINE Bot + 自動化投資分析系統

## 功能
1. **蝦皮搜尋**：在 LINE 輸入商品關鍵字，回傳蝦皮搜尋連結。
2. **股票分析**（`invest/`）：輸入「股票 2330」或「分析 AAPL」，系統會即時上網抓資料並評估買賣。

## 投資分析系統怎麼運作

所有資料都在分析當下從網路抓取，不需要 API key：

| 因素 | 資料來源 | 怎麼評分 | 權重 |
|---|---|---|---|
| 技術面 | Yahoo Finance 一年日 K | 月線/季線位置、均線排列、RSI、MACD、20 日動能 | 35% |
| 個股新聞 | Google News（近 7 天） | 新聞標題利多/利空關鍵字 | 20% |
| 大盤/總經 | Yahoo：加權指數或 S&P500、VIX、美債 10 年殖利率、美元/台幣 | 大盤趨勢、恐慌程度、利率與匯率變化 | 20% |
| 財經新聞 | Google News：聯準會利率、外資盤勢、財報經濟數據 | 同上 | 10% |
| 政治因素 | Google News：關稅貿易戰、台海地緣政治、選舉政策、戰爭制裁 | 同上 | 15% |

每個因素算出 -100 ~ +100 分，加權後得到綜合分數：

- ≥ +40 強力買進、≥ +15 買進、-15 ~ +15 持有／觀望、≤ -15 賣出、≤ -40 強力賣出

權重與門檻在 `invest/analyzer.py` 的 `WEIGHTS`、`verdict()`；新聞關鍵字詞典在 `invest/sentiment.py`，都可以自行調整。

### 選用：AI 綜合研判
設定環境變數 `ANTHROPIC_API_KEY` 後，系統會把抓到的所有指標與新聞交給 Claude 閱讀，
在報告最後附上一段 AI 研判（關鍵詞判斷看不懂的語意，例如「油價飆漲」其實是利空，AI 能判斷）。
LINE Bot 預設不開 AI 以免超過回覆時限，要開啟請設 `LINE_STOCK_AI=1`。

## 使用方式

```bash
pip install -r requirements.txt

# 命令列：可一次分析多檔（台股輸入數字代號、上櫃自動辨識；美股輸入英文代號）
python -m invest 2330 0050 6488 AAPL NVDA
python -m invest 2330 --no-ai     # 不呼叫 AI

# 測試
python -m unittest discover tests
```

## 檔案

| 檔案 | 用途 |
|---|---|
| `app.py` | LINE Bot 主程式 |
| `invest/data.py` | 抓取股價（Yahoo Finance）與新聞（Google News RSS） |
| `invest/indicators.py` | 技術指標：SMA、RSI、MACD |
| `invest/sentiment.py` | 新聞標題情緒分析 |
| `invest/macro.py` | 大盤、總經、財經與政治新聞因素 |
| `invest/analyzer.py` | 綜合評分與報告格式 |
| `invest/ai.py` | 選用的 Claude AI 研判 |
| `Procfile` | Render 啟動設定 |

## 環境變數

| 變數 | 說明 |
|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` / `LINE_CHANNEL_SECRET` | LINE Bot 憑證 |
| `ANTHROPIC_API_KEY` | （選用）開啟 AI 綜合研判 |
| `LINE_STOCK_AI` | （選用）設 `1` 讓 LINE 回覆也附 AI 研判 |

> ⚠️ 本系統只提供分析參考，**不會自動下單**，也不構成投資建議。關鍵字情緒分析與技術指標都有侷限，請自行判斷並承擔風險。
