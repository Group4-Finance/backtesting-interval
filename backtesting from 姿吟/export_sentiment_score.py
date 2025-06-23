# -----------------------------------------------------
# 需要以下檔案
# cnyes_headlines_*.csv
# megabank_news.csv
# PTT_sentiment
#
# 最後匯出 sentiment_score.csv (鉅亨&兆豐&PTT 每日情緒總分 以及 左側情緒分數)
# -----------------------------------------------------
import pandas as pd
import datetime as dt
import glob
from tabulate import tabulate

# ------------------------------------------------------

START_DATE = "2020-01-01"
END_DATE = "2025-05-31"


# ------------------------------------------------------

def load_keywords(positive_path, negative_path):
    """載入正負面關鍵詞"""
    with open(positive_path, "r", encoding="utf-8") as f:
        positive = [line.strip() for line in f]
    with open(negative_path, "r", encoding="utf-8") as f:
        negative = [line.strip() for line in f]
    return positive, negative


def calculate_sentiment(title, positive_words, negative_words):
    """計算情緒分數"""
    if pd.isna(title):
        return 0
    pos = sum(word in title for word in positive_words)
    neg = sum(word in title for word in negative_words)
    return pos - neg


def classify_sentiment(score):
    """將情緒分數轉換為交易信號"""
    if score > 0:
        return -1  # 正面情緒
    elif score < 0:
        return 1  # 負面情緒
    else:
        return 0  # 中立


def export_sentiment_scores():
    """匯出輿情分數到CSV檔"""
    start_date = pd.to_datetime(START_DATE).date()
    end_date = pd.to_datetime(END_DATE).date()

    result_df = pd.DataFrame({
        "日期": pd.date_range(start=start_date, end=end_date, freq="D").date
    })

    # 載入關鍵詞
    positive_words, negative_words = load_keywords("positive.txt", "negative.txt")

    # ------------------------------------------------------
    # 1. 鉅亨網新聞 (讀取cnyes_headlines_*.csv)
    # ------------------------------------------------------

    cnyes_sentiment = pd.DataFrame(columns=["日期", "鉅亨網情緒總分"])
    try:
        news_files = glob.glob("cnyes_headlines_*.csv")
        all_news = []

        for file in news_files:
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip()
            df['日期'] = pd.to_datetime(df['時間']).dt.date
            all_news.append(df[['日期', '標題']])

        if all_news:
            news_df = pd.concat(all_news, ignore_index=True)
            news_df = news_df[(news_df["日期"] >= start_date) &
                              (news_df["日期"] <= end_date)]

            # 計算每篇新聞的情緒分數
            news_scores = []
            for date, title in zip(news_df['日期'], news_df['標題']):
                score = calculate_sentiment(title, positive_words, negative_words)
                news_scores.append({'日期': date, '原始分數': score})

            scores_df = pd.DataFrame(news_scores)

            cnyes_sentiment = scores_df.groupby('日期')['原始分數'].sum().reset_index()
            cnyes_sentiment = cnyes_sentiment.rename(columns={'原始分數': '鉅亨網情緒總分'})
            cnyes_sentiment['鉅亨網情緒總分'] = cnyes_sentiment['鉅亨網情緒總分'].round(2)

    except Exception as e:
        print(f"處理鉅亨網新聞時發生錯誤: {e}")

    # ------------------------------------------------------
    # 2. 兆豐新聞  (讀取megabank_news.csv)
    # ------------------------------------------------------
    megabank_sentiment = pd.DataFrame(columns=["日期", "兆豐情緒總分"])
    try:

        megabank_df = pd.read_csv("megabank_news.csv")
        megabank_df['日期'] = pd.to_datetime(megabank_df['日期']).dt.date
        megabank_df = megabank_df[(megabank_df['日期'] >= start_date) &
                                  (megabank_df['日期'] <= end_date)]

        # 計算每篇標題的情緒分數
        megabank_scores = []
        for index, row in megabank_df.iterrows():
            score = calculate_sentiment(row['標題'], positive_words, negative_words)
            megabank_scores.append({'日期': row['日期'], '原始分數': score})

        scores_df = pd.DataFrame(megabank_scores)
        megabank_sentiment = scores_df.groupby('日期')['原始分數'].sum().reset_index()
        megabank_sentiment = megabank_sentiment.rename(columns={'原始分數': '兆豐情緒總分'})
        megabank_sentiment['兆豐情緒總分'] = megabank_sentiment['兆豐情緒總分'].round(2)

    except Exception as e:
        print(f"處理兆豐新聞時發生錯誤: {e}")
    # ------------------------------------------------------
    # 3. 處理PTT輿情 (讀取PTT_sentiment.csv)
    # ------------------------------------------------------
    ptt_sentiment = pd.DataFrame(columns=["日期", "PTT情緒總分"])
    try:
        ptt_df = pd.read_csv("PTT_sentiment.csv")
        ptt_df.columns = ptt_df.columns.str.strip()

        # 日期格式處理
        ptt_df['日期'] = pd.to_datetime(ptt_df['日期']).dt.date

        # 篩選日期範圍
        ptt_df = ptt_df[(ptt_df["日期"] >= start_date) &
                        (ptt_df["日期"] <= end_date)]

        # 重新命名欄位
        ptt_sentiment = ptt_df[['日期', '每日原始總分']].copy()
        ptt_sentiment = ptt_sentiment.rename(columns={'每日原始總分': 'PTT情緒總分'})

        # 確保分數是數值類型
        ptt_sentiment['PTT情緒總分'] = pd.to_numeric(ptt_sentiment['PTT情緒總分'], errors='coerce').fillna(0)

    except Exception as e:
        print(f"處理PTT輿情時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    # ------------------------------------------------------
    # 合併所有輿情數據
    # ------------------------------------------------------
    result_df = pd.merge(result_df, cnyes_sentiment[["日期", "鉅亨網情緒總分"]],
                         on="日期", how="left")
    result_df = pd.merge(result_df, megabank_sentiment[["日期", "兆豐情緒總分"]],
                         on="日期", how="left")
    result_df = pd.merge(result_df, ptt_sentiment[["日期", "PTT情緒總分"]],
                         on="日期", how="left")

    # 填充缺失值為0
    with pd.option_context('future.no_silent_downcasting', True):
        result_df.fillna(0, inplace=True)

    # ------------------------------------------------------
    # 新增左側情緒欄位
    # ------------------------------------------------------

    # 鉅亨網左側情緒
    result_df['鉅亨網左側情緒'] = result_df['鉅亨網情緒總分'].apply(classify_sentiment)

    # 兆豐左側情緒
    result_df['兆豐左側情緒'] = result_df['兆豐情緒總分'].apply(classify_sentiment)

    # PTT左側情緒
    result_df['PTT左側情緒'] = result_df['PTT情緒總分'].apply(classify_sentiment)

    # ------------------------------------------------------

    # 選擇要輸出的欄位
    output_columns = [
        "日期",
        "鉅亨網情緒總分", "鉅亨網左側情緒",
        "兆豐情緒總分", "兆豐左側情緒",
        "PTT情緒總分", "PTT左側情緒"
    ]

    print(tabulate(
        result_df[output_columns],
        headers='keys',
        tablefmt='grid',
        stralign='center',
        numalign='center',
        showindex=False,
        missingval='nan',
        colalign=("center",) * len(output_columns)
    ))

    # 保存結果
    output_file = f"sentiment_score.csv"
    result_df[output_columns].to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\n輿情數結果已保存到: {output_file}")

    return output_file


if __name__ == "__main__":
    export_sentiment_scores()
