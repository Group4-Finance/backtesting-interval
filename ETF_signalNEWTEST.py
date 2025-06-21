# 整合鉅亨與兆豐新聞情緒、折溢價、VIX，輸出情緒燈號與圖表
import pandas as pd
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# --- 路徑與詞庫讀取 ---
base_path = "C:/Users/winni/PycharmProjects/PythonProject1/ETF_signal/ETF_data"
positive_words = pd.read_csv(os.path.join(base_path, "positive.txt"), header=None)[0].dropna().tolist()
negative_words = pd.read_csv(os.path.join(base_path, "negative.txt"), header=None)[0].dropna().tolist()

def get_sentiment_score(title, pos_words, neg_words):
    if pd.isna(title): return 0
    pos = sum(word in title for word in pos_words)
    neg = sum(word in title for word in neg_words)
    return pos - neg

def left_side_label(score):
    if score > 0: return -1
    elif score < 0: return 1
    else: return 0

# --- 讀取鉅亨與兆豐新聞 ---
df_cnyes = pd.read_csv(os.path.join(base_path, "cnyes_headlines.csv"))
df_cnyes.columns = df_cnyes.columns.str.strip()
df_cnyes = df_cnyes.rename(columns={"時間": "日期", "標題": "title"})
df_cnyes["來源"] = "鉅亨"
df_cnyes["日期"] = pd.to_datetime(df_cnyes["日期"]).dt.date

df_mega = pd.read_csv(os.path.join(base_path, "megabank_news.csv"))
df_mega = df_mega.rename(columns={"標題": "title"})
df_mega["來源"] = "兆豐"
df_mega["日期"] = pd.to_datetime(df_mega["日期"]).dt.date

# --- 整合並計算情緒分數 ---
df_all = pd.concat([df_cnyes[["日期", "title", "來源"]], df_mega[["日期", "title", "來源"]]], ignore_index=True)
df_all["每日原始總分"] = df_all["title"].apply(lambda x: get_sentiment_score(x, positive_words, negative_words))
df_all_grouped = df_all.groupby(["日期", "來源"])["每日原始總分"].sum().reset_index()
df_all_grouped["左側情緒分類"] = df_all_grouped["每日原始總分"].apply(left_side_label)

# --- 展開兩來源欄位 ---
df_cnyes_final = df_all_grouped[df_all_grouped["來源"] == "鉅亨"].rename(columns={
    "每日原始總分": "鉅亨_每日原始總分",
    "左側情緒分類": "鉅亨_左側情緒分類"
})[["日期", "鉅亨_每日原始總分", "鉅亨_左側情緒分類"]]

df_mega_final = df_all_grouped[df_all_grouped["來源"] == "兆豐"].rename(columns={
    "每日原始總分": "兆豐_每日原始總分",
    "左側情緒分類": "兆豐_左側情緒分類"
})[["日期", "兆豐_每日原始總分", "兆豐_左側情緒分類"]]

df_sentiment = pd.merge(df_cnyes_final, df_mega_final, on="日期", how="outer").sort_values("日期")
df_sentiment.to_csv(os.path.join(base_path, "sentiment_result.csv"), index=False, encoding="utf-8-sig")
print("✅ 已產出 sentiment_result.csv")

# --- 讀入其他資料 ---
matplotlib.rcParams['font.family'] = 'Microsoft JhengHei'
matplotlib.rcParams['axes.unicode_minus'] = False

df_PremiumDiscount = pd.read_csv("MoneyDJ_ETF_PremiumDiscount_00830.csv")
df_PremiumDiscount.set_index("交易日期", inplace=True)
df_PremiumDiscount.index = pd.to_datetime(df_PremiumDiscount.index)

df_sentiment = pd.read_csv(os.path.join(base_path, "sentiment_result.csv"))
df_sentiment["日期"] = pd.to_datetime(df_sentiment["日期"]).dt.date
df_sentiment.set_index("日期", inplace=True)

df_VIX = pd.read_csv("vix_daily.csv")
df_VIX["Date"] = pd.to_datetime(df_VIX["Date"])
df_VIX.set_index("Date", inplace=True)

# --- 初始化主資料表 ---
start_date = "2020-01-01"
end_date = "2025-05-31"
all_dates = pd.date_range(start=start_date, end=end_date, freq="D")

result = pd.DataFrame({
    "Date": all_dates,
    "is_trading_day": pd.Series([pd.NA] * len(all_dates), dtype="boolean"),
    "市價": pd.Series([pd.NA] * len(all_dates), dtype="object"),
    "折溢價利率(%)": pd.Series([pd.NA] * len(all_dates), dtype="object"),
    "折溢價利率分數": pd.Series([pd.NA] * len(all_dates), dtype="Int64"),
    "新聞輿情分數": pd.Series([np.nan] * len(all_dates), dtype="float"),
    "VIX": pd.Series([pd.NA] * len(all_dates), dtype="object"),
    "指數綜合分數": pd.Series([pd.NA] * len(all_dates), dtype="Int64"),
})

def classify_score_index(vix):
    if pd.isna(vix): return pd.NA
    if vix > 23: return 1
    elif vix < 17: return -1
    else: return 0

def classify_score_PremiumDiscount(p):
    if pd.isna(p): return pd.NA
    try: val = float(p.replace('%', ''))
    except: return pd.NA
    if val <= -0.2: return 1
    elif val >= 0.2: return -1
    else: return 0

# --- 填入每日資料 ---
for d in all_dates:
    d_date = d.date()
    result.loc[result["Date"] == d, "市價"] = df_PremiumDiscount["市價"].get(d, pd.NA)
    rate = df_PremiumDiscount["折溢價利率(%)"].get(d, pd.NA)
    result.loc[result["Date"] == d, "折溢價利率(%)"] = rate
    result.loc[result["Date"] == d, "折溢價利率分數"] = classify_score_PremiumDiscount(rate)

    # 情緒來源：鉅亨 + 兆豐 各 0.15
    cnyes = df_sentiment["鉅亨_左側情緒分類"].get(d_date, pd.NA)
    mega = df_sentiment["兆豐_左側情緒分類"].get(d_date, pd.NA)
    score = (float(cnyes) if not pd.isna(cnyes) else 0) * 0.15 + (float(mega) if not pd.isna(mega) else 0) * 0.15
    result.loc[result["Date"] == d, "新聞輿情分數"] = score

    vix = df_VIX["Close"].get(d, pd.NA)
    result.loc[result["Date"] == d, "VIX"] = vix
    result.loc[result["Date"] == d, "指數綜合分數"] = classify_score_index(vix)

# --- 總分與燈號 ---
result["總分"] = (
    result["折溢價利率分數"].astype("float") * 0.5 +
    result["新聞輿情分數"].astype("float") +
    result["指數綜合分數"].astype("float") * 0.2
)

def classify_signal(score):
    if pd.isna(score): return pd.NA
    if score >= 0.7: return "深綠燈"
    elif 0.1 <= score < 0.7: return "淺綠燈"
    elif -0.5 < score < 0.1: return "黃燈"
    elif -0.8 < score <= -0.5: return "淺紅燈"
    elif score <= -0.8: return "紅燈"
    else: return pd.NA

result["燈號"] = result["總分"].apply(classify_signal)
result.to_csv("簡易回測結果.csv", index=False, encoding="utf-8-sig")
print("✅ 已輸出簡易回測結果.csv")

# --- 畫圖 ---
result = result.dropna(subset=["市價"])
result["市價"] = pd.to_numeric(result["市價"], errors="coerce")

plt.figure(figsize=(14, 6))
plt.plot(result["Date"], result["市價"], label="收盤價", linewidth=2, color='blue')

colors = {
    "紅燈": "red", "淺紅燈": "salmon", "黃燈": "gold",
    "淺綠燈": "lightgreen", "深綠燈": "green"
}
markers = {
    "紅燈": "v", "淺紅燈": "v", "黃燈": "o", "淺綠燈": "^", "深綠燈": "^"
}

for label in result["燈號"].dropna().unique():
    subset = result[result["燈號"] == label]
    plt.scatter(subset["Date"], subset["市價"], color=colors.get(label, "gray"),
                marker=markers.get(label, "x"), label=label, s=80)

plt.title("收盤價與燈號標記")
plt.xlabel("日期")
plt.ylabel("市價")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("signal_plot.png", dpi=300)
print("✅ 圖表已儲存為 signal_plot.png")
