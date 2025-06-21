# TestResult
回測結果

使用前請詳閱說明書:
1. 前置作業: 先下載fear-greed-2011-2023.csv (參考:repository: Fear_And_Greed_Index)
2. 先跑fear_and_greed_index.py (為了抓取到最新的日期 & 休息日)
3. 下載vix_daily.csv (參考:repository: VIX_Data)
4. 挑選一則新聞輿情，先跑Winnie的sentiment_result.py，下載sentiment_result.csv
5. 挑選某一支ETF的折溢價.csv (參考:repository: ETF_PremiumDiscount)(若要取最新資料，則要重跑ETF_PremiumDiscount_to_NAV.py)
6. 進入本repository 的TestResult.py，調整你/妳要的起始與結束日期
7. 以上所有csv檔案都要放在同一個地方喔!!!
8. 執行TestResult.py !
