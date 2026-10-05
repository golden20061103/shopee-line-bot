"""自動化投資分析系統：抓取網路上的股價、新聞、總經與政治資訊，綜合評估買賣訊號。"""
from .analyzer import analyze, format_report

__all__ = ["analyze", "format_report"]
