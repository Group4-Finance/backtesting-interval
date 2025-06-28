# 整合鉅亨與兆豐新聞情緒、折溢價、VIX，輸出情緒燈號與圖表
import pandas as pd
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import sys

# 各資料路徑
path_SentimentAnalyze = 'C:/Users/USER/PycharmProjects/Group4/GITHUB/SentimentAnalyze'
path_cnyes_headlines = 'C:/Users/USER/PycharmProjects/Group4/GITHUB/cnyes_headlines'
path_MagaBank_NEWS = 'C:/Users/USER/PycharmProjects/Group4/GITHUB/MagaBank_NEWS'
path_ETF_PremiumDiscount = 'C:/Users/USER/PycharmProjects/Group4/GITHUB/ETF_PremiumDiscount'
path_VIX_Data = 'C:/Users/USER/PycharmProjects/Group4/GITHUB/VIX_Data'

# 參數
data_year_list = ['2020', '2021', '2022', '2023', '2024']
ETF_list = ['00757','0052', '00713', '00830', '00733', '00850', '00692', '0050', '00662','00646' ]

# data_year_list = ['2020']
# ETF_list = ['0052' ]

# --- 參數設定（可調整） ---
WEIGHT_PREMIUM = 0.5  # 折溢價率占比
WEIGHT_CNYES = 0.1    # 鉅亨新聞權重
WEIGHT_MEGA = 0.1     # 兆豐新聞權重
WEIGHT_PTT = 0.1      # PTT 輿情權重
WEIGHT_VIX = 0.2      # VIX 占比權重

# --- 設定字體避免中文亂碼 ---
matplotlib.rcParams['font.family'] = 'Microsoft JhengHei'
matplotlib.rcParams['axes.unicode_minus'] = False

# --- 詞庫讀取 ---
positive_words = pd.read_csv(os.path.join(f"{path_SentimentAnalyze}", "positive.txt"), header=None)[0].dropna().tolist()
negative_words = pd.read_csv(os.path.join(f"{path_SentimentAnalyze}", "negative.txt"), header=None)[0].dropna().tolist()

# function
def classify_score_index(vix):
    if pd.isna(vix): return pd.NA
    if vix > 22.72:
        return 1
    elif vix < 17.12:
        return -1
    else:
        return 0

# def score_PremiumDiscount_weighted(p):
#     if pd.isna(p): return pd.NA
#     try:
#         val = float(p.replace('%', '')) if isinstance(p, str) else float(p)
#     except:
#         return pd.NA
#
#     if val <= -0.49:
#         return 0.5
#     elif val <= -0.16:
#         return 0.25
#     elif val <= 0.09:
#         return 0
#     elif val <= 0.38:
#         return -0.25
#     else:
#         return -0.5

# --- 動態 z-score 分數函式（含擴大補強） ---
def score_PremiumDiscount_z_dynamic(df, window=60):
    df = df.copy()
    df["折溢價率"] = df["折溢價利率(%)"].str.replace('%', '').astype(float)
    df["z_mean"] = df["折溢價率"].rolling(window=window).mean()
    df["z_std"] = df["折溢價率"].rolling(window=window).std()
    df["z_score"] = (df["折溢價率"] - df["z_mean"]) / df["z_std"]

    scores = []
    no_positive_days = 0
    for z in df["z_score"]:
        score = 0
        if pd.isna(z):
            scores.append(pd.NA)
            continue

        if z <= -1.2:
            score = 0.5
        elif z <= -0.3:
            score = 0.25
        elif z >= 1.2:
            score = -0.5
        elif z >= 0.3:
            score = -0.25
        else:
            score = 0

        # 擴大補強條件：若連續 120 天未出現 score >= 0.25 則強制補 +0.25
        if score >= 0.25:
            no_positive_days = 0
        else:
            no_positive_days += 1
            if no_positive_days >= 120 and -0.5 <= z <= 0.3:
                score = 0.25

        scores.append(score)

    df["折溢價分數"] = scores
    return df

def classify_signal(score):
    if pd.isna(score): return pd.NA
    if score >= 0.8: return "深綠燈"
    elif 0.1 <= score < 0.8: return "淺綠燈"
    elif -0.3 < score < 0.1: return "黃燈"
    elif -0.8 < score <= -0.3: return "淺紅燈"
    elif score <= -0.8: return "紅燈"
    else: return pd.NA

# 開始跑數據
for ETF in ETF_list:
    for data_year in data_year_list:
        # --- 讀取資料 ---
        df_PremiumDiscount = pd.read_csv(os.path.join(f"{path_ETF_PremiumDiscount}", f"MoneyDJ_ETF_PremiumDiscount_{ETF}.csv"))
        # df_PremiumDiscount.set_index("交易日期", inplace=True)
        # df_PremiumDiscount.index = pd.to_datetime(df_PremiumDiscount.index)
        df_PremiumDiscount["交易日期"] = pd.to_datetime(df_PremiumDiscount["交易日期"])
        df_PremiumDiscount.set_index("交易日期", inplace=True)
        df_PremiumDiscount = score_PremiumDiscount_z_dynamic(df_PremiumDiscount)

        df_sentiment = pd.read_csv(os.path.join(f"{path_SentimentAnalyze}", "sentiment_result.csv"))
        df_sentiment["日期"] = pd.to_datetime(df_sentiment["日期"]).dt.date
        df_sentiment.set_index("日期", inplace=True)

        df_VIX = pd.read_csv(os.path.join(f"{path_VIX_Data}", "vix_daily.csv"))
        df_VIX["Date"] = pd.to_datetime(df_VIX["Date"])
        df_VIX.set_index("Date", inplace=True)

        # --- 初始化主資料表 ---
        start_date = f"{data_year}-01-01"
        end_date = f"{data_year}-12-31"
        all_dates = pd.date_range(start=start_date, end=end_date, freq="D")

        result = pd.DataFrame({
            "Date": all_dates,
            "市價": pd.Series([pd.NA] * len(all_dates), dtype="object"),
            "折溢價利率(%)": pd.Series([pd.NA] * len(all_dates), dtype="object"),
            "折溢價利率分數": pd.Series([np.nan] * len(all_dates), dtype="float"),
            "新聞輿情分數": pd.Series([np.nan] * len(all_dates), dtype="float"),
            "VIX": pd.Series([pd.NA] * len(all_dates), dtype="object"),
            "指數綜合分數": pd.Series([pd.NA] * len(all_dates), dtype="Int64"),
        })

        # --- 填入每日資料 ---
        for d in all_dates:
            d_date = d.date()
            result.loc[result["Date"] == d, "市價"] = df_PremiumDiscount["市價"].get(d, pd.NA)
            result.loc[result["Date"] == d, "折溢價利率(%)"] = df_PremiumDiscount["折溢價利率(%)"].get(d, pd.NA)
            result.loc[result["Date"] == d, "折溢價分數"] = df_PremiumDiscount["折溢價分數"].get(d, pd.NA)


            cnyes = df_sentiment["鉅亨_左側情緒分類"].get(d_date, pd.NA)
            mega = df_sentiment["兆豐_左側情緒分類"].get(d_date, pd.NA)
            ptt = df_sentiment["PTT_左側情緒分類"].get(d_date, pd.NA)
            score = (
                    (float(cnyes) if not pd.isna(cnyes) else 0) * WEIGHT_CNYES +
                    (float(mega) if not pd.isna(mega) else 0) * WEIGHT_MEGA +
                    (float(ptt) if not pd.isna(ptt) else 0) * WEIGHT_PTT
            )
            result.loc[result["Date"] == d, "新聞輿情分數"] = score

            vix = df_VIX["Close"].get(d, pd.NA)
            result.loc[result["Date"] == d, "VIX"] = vix
            result.loc[result["Date"] == d, "指數綜合分數"] = classify_score_index(vix)

        # --- 總分與燈號 ---
        result["總分"] = (
                result["折溢價分數"] * WEIGHT_PREMIUM +
                result["新聞輿情分數"].astype("float") +
                result["指數綜合分數"].astype("float") * WEIGHT_VIX
        )

        result["燈號"] = result["總分"].apply(classify_signal)
        result.to_csv(f"燈號結果_{ETF}_{data_year}.csv", index=False, encoding="utf-8-sig")
        print("✅ 已輸出燈號結果.csv")

        # --- 動態互動圖 ---
        # 過濾掉「黃燈」和 NA 的燈號資料，以及市價為 NA 的列
        plot_df = result[(result["燈號"].notna()) & (result["燈號"] != "黃燈")].dropna(subset=["市價"])

        # 市價轉為數值型別（確保是可畫的數值）
        plot_df["市價"] = pd.to_numeric(plot_df["市價"], errors="coerce")

        # 繪製互動圖（點）
        fig = px.scatter(
            plot_df,
            x="Date", y="市價", color="燈號",
            title=f"互動式：市價與燈號標記（不含黃燈）_{ETF}_{data_year}",
            hover_data=["總分", "折溢價利率(%)"],
            color_discrete_map={
                "紅燈": "red",
                "淺紅燈": "salmon",
                "淺綠燈": "lightgreen",
                "深綠燈": "green"
            }
        )

        # 折線：市價走勢（過濾掉 NA）
        fig.add_scatter(
            x=result["Date"],
            y=result["市價"],
            mode="lines",
            name="收盤價",
            line=dict(color="blue")
        )


        # 輸出為 HTML
        fig.write_html(f"signal_plot_interactive_{ETF}_{data_year}.html")
        print("✅ 互動圖已儲存為 signal_plot_interactive.html")

        # 輸出 PNG
        # fig.write_image("signal_plot_interactive.png", scale=2)
        # print("✅ 靜態圖已儲存為 signal_plot_interactive.png")

