# -----------------------------------------------------
# 需要以下檔案
# 折溢價數據: MoneyDJ_ETF_PremiumDiscount_{ETF_CODE}.csv
# vix指數數據: vix_daily.csv
# 輿情情緒分數數據: sentiment_score.csv
#
# 最後匯出 {ETF_CODE}買入評分回測{START_DATE}至{END_DATE}
# 以及 {etf_code}_燈號視覺化_{start_date}_至_{end_date}
# -----------------------------------------------------

import pandas as pd
import datetime as dt
from tabulate import tabulate
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

# ------------------------------------------------------

ETF_CODE = "0050"
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

# 權重設定
DISCOUNT_WEIGHT = 0.5   # 折溢價分數權重
SENTIMENT_WEIGHT = 0.1  # 輿情情緒分數權重
VIX_WEIGHT = 0.2        # VIX指數分數權重

# ------------------------------------------------------
# 折溢價分數分類 & VIX指數分數分類 設定
# ------------------------------------------------------
def classify_discount(rate):

    if pd.isna(rate):
        return pd.NA

    try:
        value = float(str(rate).replace('%', ''))
    except:
        return pd.NA

    if value <= -1:  # 折價大於1%
        return 1
    elif value >= 1:  # 溢價大於1%
        return -1
    else:  # -1%~1%之間
        return 0


def classify_vix(vix_value):

    if pd.isna(vix_value):
        return pd.NA

    if vix_value <= 17.12:
        return -1
    elif vix_value <= 22.72:
        return 0
    else:
        return 1

# ------------------------------------------------------
# 燈號分類
# ------------------------------------------------------

def classify_signal(score):

    if pd.isna(score):
        return pd.NA

    if score >= 0.8:
        return "深綠燈"
    elif score >= 0.3:
        return "淺綠燈"
    elif score >= -0.3:
        return "黃燈"
    elif score >= -0.8:
        return "淺紅燈"
    else:
        return "紅燈"

# ------------------------------------------------------
# 計算總分: 折溢價分數 * DISCOUNT_WEIGHT + (三情緒總和) * SENTIMENT_WEIGHT + vix * VIX_WEIGHT
# ------------------------------------------------------

def calculate_total_score(row):
    """計算總分"""
    # 取得各分數，若為空值則設為0
    discount = row["折溢價分數"] if not pd.isna(row["折溢價分數"]) else 0
    vix = row["VIX分數"] if not pd.isna(row["VIX分數"]) else 0
    cnyes = row["鉅亨網左側情緒"] if not pd.isna(row["鉅亨網左側情緒"]) else 0
    megabank = row["兆豐左側情緒"] if not pd.isna(row["兆豐左側情緒"]) else 0
    ptt = row["PTT左側情緒"] if not pd.isna(row["PTT左側情緒"]) else 0
    sentiment_sum = cnyes + megabank + ptt

    total = (discount * DISCOUNT_WEIGHT +
             sentiment_sum * SENTIMENT_WEIGHT +
             vix * VIX_WEIGHT)

    return round(total, 2)

# ------------------------------------------------------
# 繪製評分趨勢圖
# ------------------------------------------------------

def plot_signal_with_background(df, etf_code, start_date, end_date):

    try:
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Microsoft JhengHei']
        plt.rcParams['axes.unicode_minus'] = False
    except:
        pass

    plt.figure(figsize=(15, 7))
    ax = plt.gca()

    # 轉換日期格式
    df = df.sort_values("日期")
    dates = pd.to_datetime(df["日期"])
    scores = df["總分"]

    # 定義Y軸範圍和對應顏色
    y_ranges = [
        (-2, -1.5, "#FF0000"),  # 紅燈
        (-1.5, -0.8, "#FFA07A"),  # 淺紅燈
        (-0.8, 0.8, "#FFFF00"),  # 黃燈
        (0.8, 1.5, "#90EE90"),  # 淺綠燈
        (1.5, 2, "#006400")  # 深綠燈
    ]

    # 繪製背景色（基於Y軸範圍）
    for y_min, y_max, color in y_ranges:
        ax.axhspan(y_min, y_max, facecolor=color, alpha=0.3)

    # 繪製曲線
    ax.plot(dates, scores, marker='o', linestyle='-', color='blue', linewidth=2, markersize=6)

    # 添加參考線
    ax.axhline(y=1.5, color='green', linestyle='--', alpha=0.5)  # 深綠燈下限
    ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.3)  # 淺綠燈下限
    ax.axhline(y=-0.8, color='red', linestyle='--', alpha=0.3)  # 淺紅燈上限
    ax.axhline(y=-1.5, color='red', linestyle='--', alpha=0.5)  # 紅燈上限
    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)  # 中線

    # 設定標題和標籤
    ax.set_title(f"ETF {etf_code} 買入評分系統 - 燈號視覺化 ({start_date} 至 {end_date})", fontsize=16, pad=20)
    ax.set_xlabel("日期", fontsize=12)
    ax.set_ylabel("總分", fontsize=12)

    # 設定圖例
    legend_elements = [
        Rectangle((0, 0), 1, 1, fc="#006400", alpha=0.3, label='深綠燈 (>=1.5)'),
        Rectangle((0, 0), 1, 1, fc="#90EE90", alpha=0.3, label='淺綠燈 (0.8~1.49)'),
        Rectangle((0, 0), 1, 1, fc="#FFFF00", alpha=0.3, label='黃燈 (-0.79~0.79)'),
        Rectangle((0, 0), 1, 1, fc="#FFA07A", alpha=0.3, label='淺紅燈 (-1.49~-0.8)'),
        Rectangle((0, 0), 1, 1, fc="#FF0000", alpha=0.3, label='紅燈 (<=-1.5)'),
        Line2D([0], [0], color='blue', lw=2, label='總分')
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    # 設定日期格式和範圍
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    ax.set_ylim(-2, 2)  # Y軸範圍固定為-2到2
    plt.tight_layout()

    # 保存圖片
    plot_file = f"{etf_code}_燈號視覺化_{start_date}_至_{end_date}.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()

    return plot_file


# ------------------------------------------------------

def main():
    start_date = pd.to_datetime(START_DATE).date()
    end_date = pd.to_datetime(END_DATE).date()

    # 創建日期範圍的DataFrame
    result_df = pd.DataFrame({
        "日期": pd.date_range(start=start_date, end=end_date, freq="D").date
    })

    # ------------------------------------------------------
    # 1. 載入輿情分數數據 (讀取 sentiment_score.csv)
    # ------------------------------------------------------
    try:
        sentiment_df = pd.read_csv("sentiment_score.csv")
        sentiment_df["日期"] = pd.to_datetime(sentiment_df["日期"]).dt.date
        sentiment_df = sentiment_df[["日期", "鉅亨網左側情緒", "兆豐左側情緒", "PTT左側情緒"]]
        result_df = pd.merge(result_df, sentiment_df, on="日期", how="left")

        result_df[["鉅亨網左側情緒", "兆豐左側情緒", "PTT左側情緒"]] = result_df[
            ["鉅亨網左側情緒", "兆豐左側情緒", "PTT左側情緒"]].fillna(0)

    except Exception as e:
        print(f"載入輿情分數數據時發生錯誤: {e}")
        # 如果讀取失敗，初始化這三個欄位為0
        result_df["鉅亨網左側情緒"] = 0
        result_df["兆豐左側情緒"] = 0
        result_df["PTT左側情緒"] = 0

    # ------------------------------------------------------
    # 2. 載入折溢價數據 (讀取 MoneyDJ_ETF_PremiumDiscount_{ETF_CODE}.csv)
    # ------------------------------------------------------
    try:
        discount_df = pd.read_csv(f"MoneyDJ_ETF_PremiumDiscount_{ETF_CODE}.csv")
        discount_df["日期"] = pd.to_datetime(discount_df["交易日期"]).dt.date
        discount_df = discount_df.sort_values("日期")
        discount_df = discount_df.drop_duplicates("日期", keep="last")
        discount_df = discount_df[(discount_df["日期"] >= start_date) &
                                  (discount_df["日期"] <= end_date)].copy()
        # 計算折溢價分數
        discount_df["折溢價分數"] = discount_df["折溢價利率(%)"].apply(classify_discount)

        result_df = pd.merge(result_df, discount_df[["日期", "市價", "折溢價利率(%)", "折溢價分數"]],
                             on="日期", how="left")
    except Exception as e:
        print(f"載入折溢價數據時發生錯誤: {e}")
        result_df["折溢價分數"] = pd.NA
        result_df["折溢價利率(%)"] = pd.NA
        result_df["市價"] = pd.NA

    # ------------------------------------------------------
    # 3. 載入VIX數據 (讀取 vix_daily.csv)
    # ------------------------------------------------------
    try:
        vix_df = pd.read_csv("vix_daily.csv")
        vix_df["日期"] = pd.to_datetime(vix_df["Date"]).dt.date
        vix_df = vix_df.drop_duplicates("日期", keep="last")
        vix_df = vix_df[(vix_df["日期"] >= start_date) &
                        (vix_df["日期"] <= end_date)].copy()

        # 計算VIX分數
        vix_df["VIX分數"] = vix_df["Close"].apply(classify_vix)

        result_df = pd.merge(result_df, vix_df[["日期", "Close", "VIX分數"]],
                             on="日期", how="left")
        result_df.rename(columns={"Close": "VIX收盤價"}, inplace=True)
    except Exception as e:
        print(f"載入VIX數據時發生錯誤: {e}")
        result_df["VIX分數"] = pd.NA
        result_df["VIX收盤價"] = pd.NA

    # ------------------------------------------------------
    # 4. 計算總分和燈號
    # ------------------------------------------------------
    # 計算總分
    result_df["總分"] = result_df.apply(calculate_total_score, axis=1)

    # 判斷燈號
    result_df["燈號"] = result_df["總分"].apply(classify_signal)

    # 標記是否為交易日
    result_df["is_trading_day"] = ~result_df["市價"].isna()

    # ------------------------------------------------------
    # 5. 輸出結果
    # ------------------------------------------------------
    # 定義輸出欄位
    output_columns = [
        "日期",
        "is_trading_day",
        "折溢價分數",
        "VIX分數",
        "鉅亨網左側情緒",
        "兆豐左側情緒",
        "PTT左側情緒",
        "總分",
        "燈號"
    ]

    print("\n最終回測結果:")
    print(tabulate(
        result_df[output_columns],
        headers='keys',
        tablefmt='grid',
        stralign='center',
        numalign='center',
        colalign=("center",) * len(output_columns)
    ))

    # 保存結果
    output_file = f"{ETF_CODE}買入評分回測{START_DATE}至{END_DATE}.csv"
    result_df[output_columns].to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\n結果已保存到: {output_file}")

    # ------------------------------------------------------
    # 6. 繪製燈號視覺化圖
    # ------------------------------------------------------
    try:
        plot_file = plot_signal_with_background(result_df, ETF_CODE, START_DATE, END_DATE)
        print(f"\n燈號視覺化圖已保存到: {plot_file}")
    except Exception as e:
        print(f"\n繪製燈號視覺化圖時發生錯誤: {e}")


if __name__ == "__main__":
    main()