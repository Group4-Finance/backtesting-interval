import pandas as pd
import tabulate

# --- 讀入 CSV 並轉換時間格式 ---
# 讀入某一支ETF的折溢價利率(%)
df_PremiumDiscount = pd.read_csv("MoneyDJ_ETF_PremiumDiscount_0050.csv")
df_PremiumDiscount.set_index("交易日期", inplace=True)

# 讀入某一則新聞輿情的情緒分數 (請先跑 Winnie 的sentiment_result.py)
df_NewsAndPublicOpinion = pd.read_csv("sentiment_result.csv")
df_NewsAndPublicOpinion.set_index("日期", inplace=True)

# 讀入恐懼貪婪指數
df_Fear_And_Greed = pd.read_csv("Fear_And_Greed_index.csv")
df_Fear_And_Greed.set_index("Date", inplace=True)

# 讀入VIX
df_VIX = pd.read_csv("vix_daily.csv")
df_VIX["Date"] = pd.to_datetime(df_VIX["Date"])
df_VIX.set_index("Date", inplace=True)

# --- 時間範圍 ---
start_date = "2025-05-01" # 可自行挑選起始日期
end_date = "2025-06-05" # 可自行挑選終止日期

# 建立完整日期範圍
all_dates = pd.date_range(start=start_date, end=end_date, freq="D")

# 篩選 df 的資料範圍
df_range = df_Fear_And_Greed.loc[start_date:end_date]

# 初始化結果 DataFrame，包含目標欄位
result = pd.DataFrame({
    "Date": all_dates,
    "is_trading_day": pd.Series([pd.NA] * len(all_dates), dtype="boolean"),
    "市價": pd.Series([pd.NA] * len(all_dates), dtype="object"),
    "折溢價利率(%)": pd.Series([pd.NA] * len(all_dates), dtype="object"),
    "折溢價利率分數": pd.Series([pd.NA] * len(all_dates), dtype="Int64"),
    "新聞輿情分數": pd.Series([pd.NA] * len(all_dates), dtype="Int64"),
    # "fear_and_greed_index": pd.Series([pd.NA] * len(all_dates), dtype="object"),
    "VIX": pd.Series([pd.NA] * len(all_dates), dtype="object"),
    "指數綜合分數": pd.Series([pd.NA] * len(all_dates), dtype="Int64"),
})

# 分數分類函式：根據 vix 決定
def classify_score_index( vix):
    if pd.isna(vix):
        return pd.NA
    total = (vix *0.8) # 可自行調整數字
    if total > 25: # 依照簡報p.17 指標綜合分數(已修改為只抓VIX)
        return 1
    elif total < 15: # 依照簡報p.17 指標綜合分數
        return -1
    else:
        return 0 # 依照簡報p.17 指標綜合分數

# 分數分類函式：根據 折溢價率(%) 決定
def classify_score_PremiumDiscount(PremiumDiscount):
    if pd.isna(PremiumDiscount):
        return pd.NA
    try:
        value = float(PremiumDiscount.replace('%', ''))  # 直接處理字串中的 %
    except:
        return pd.NA

    if value <= -0.1:
        return 1
    elif value >= 0.1:
        return -1
    else:
        return 0


# 填入數據
for d in df_range.index:
    result.loc[result["Date"] == d, "is_trading_day"] = df_Fear_And_Greed.at[d, "is_trading_day"]

    marketprice = df_PremiumDiscount["市價"].get(d, pd.NA)
    result.loc[result["Date"] == d, "市價"] = marketprice

    rate = df_PremiumDiscount["折溢價利率(%)"].get(d, pd.NA)
    result.loc[result["Date"] == d, "折溢價利率(%)"] = rate
    result.loc[result["Date"] == d, "折溢價利率分數"] = classify_score_PremiumDiscount(rate)
    # result.loc[result["Date"] == d, "fear_and_greed_index"] = df_Fear_And_Greed.at[d, "fear_and_greed_index"]

    NewsAndPublicOpinion = df_NewsAndPublicOpinion["左側情緒分類"].get(d, pd.NA)
    result.loc[result["Date"] == d, "新聞輿情分數"] = NewsAndPublicOpinion

    # fgi = df_Fear_And_Greed["fear_and_greed_index"].get(d, pd.NA)
    vix_close = df_VIX["Close"].get(d, pd.NA)
    result.loc[result["Date"] == d, "VIX"] = vix_close
    result.loc[result["Date"] == d, "指數綜合分數"] = classify_score_index(vix_close)


# 計算總分欄位
result["總分"] = (
    result["折溢價利率分數"].astype("float") * 0.5 +
    result["新聞輿情分數"].astype("float") * 0.3 +
    result["指數綜合分數"].astype("float") * 0.2
)

# 定義燈號分類函式
def classify_signal(score):
    if pd.isna(score):
        return pd.NA
    if score >= 1.5:
        return "深綠燈"
    elif 0.8 <= score < 1.5:
        return "淺綠燈"
    elif -0.79 <= score <= 0.79:
        return "黃燈"
    elif -1.49 <= score < -0.8:
        return "淺紅燈"
    elif score <= -1.5:
        return "紅燈"
    else:
        return pd.NA

# 套用燈號分類
result["燈號"] = result["總分"].apply(classify_signal)


# print(tabulate.tabulate(result, headers='keys', tablefmt='grid'))

# --- 輸出 ---
result.to_csv("簡易回測結果.csv", index=False, encoding='utf-8-sig')