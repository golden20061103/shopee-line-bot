"""命令列使用：python -m invest 2330 AAPL [--no-ai]"""
import sys

from .analyzer import analyze, format_report


def main(argv: list[str]) -> int:
    use_ai = "--no-ai" not in argv
    symbols = [a for a in argv if not a.startswith("--")]
    if not symbols:
        print("用法：python -m invest <股票代號...> [--no-ai]\n例如：python -m invest 2330 0050 AAPL NVDA")
        return 1
    for sym in symbols:
        result = analyze(sym, use_ai=use_ai)
        print(format_report(result) if result else f"❌ 找不到股票代號：{sym}")
        print("=" * 40)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
