import streamlit as st
import pandas as pd
import numpy as np
from pyecharts import options as opts
from pyecharts.charts import Gauge
from streamlit_echarts import st_pyecharts

# === ETF 選單設定 ===
etf_list = {
    "00646": "元大S&P500",
    "0050": "元大台灣50",
    "0056": "元大高股息",
    "00757": "統一FANG+",
    "00878": "國泰永續高股息",
    "00881": "國泰台灣5G",
    "00692": "富邦公司治理",
    "00713": "元大高息低波",
    "00830": "國泰費城半導體",
    "00733": "富邦中小"
}

# === Streamlit 介面 ===
st.title("📈 ETF 買賣決策訊號儀錶板")
selected_etf = st.selectbox("請選擇欲查詢的 ETF", options=list(etf_list.keys()),
                            format_func=lambda x: f"{x} - {etf_list[x]}")

# === 載入資料 ===
file_path = f"C:/Users/andre/Desktop/ETF_signal_{selected_etf}.csv"
df = pd.read_csv(file_path, parse_dates=["Date"])
df = df[df["總分"].notna()].sort_values("Date")
available_dates = df["Date"].dt.date.unique()
selected_date = st.selectbox("請選擇查詢日期", available_dates)

# === 取得資料 ===
try:
    today = df[df["Date"].dt.date == selected_date].iloc[0]
    idx = df[df["Date"].dt.date == selected_date].index[0]
    yesterday = df.iloc[idx - 1] if idx > 0 else None
except:
    st.warning(f"⚠️ 選擇的日期 {selected_date} 沒有資料。")
    st.stop()

score = round(today["總分"], 2)
delta_score = round(score - (yesterday["總分"] if yesterday is not None else 0), 2)

# === 使用 pyecharts 建立儀表板 ===
gauge = (
    Gauge(init_opts=opts.InitOpts(width="900px", height="800px"))
    .add(
        series_name="",
        data_pair=[("", score)],
        min_=-1,
        max_=1,
        split_number=10,
        axislabel_opts={"show": False},
        pointer=opts.GaugePointerOpts(length="65%"),
        detail_label_opts=opts.GaugeDetailOpts(
            formatter="{value|總分：%.2f}\n{delta|Δ %+.2f}" % (score, delta_score),
            rich={
                "value": {"fontSize": 24, "color": "#000", "fontWeight": "bold"},
                "delta": {"fontSize": 20, "color": "#2ECC71" if delta_score >= 0 else "#E74C3C", "fontWeight": "bold"},
            },
            offset_center=[0, "85%"]
        ),
        title_label_opts=opts.GaugeTitleOpts(
            offset_center=[0, "-30%"],
            font_size=22,
            color="#000",
            font_weight="bold"
        )
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title=f"{selected_date} 訊號燈分數",
            pos_top="2%"
        ),
        legend_opts=opts.LegendOpts(is_show=False),
        tooltip_opts=opts.TooltipOpts(formatter="{a} <br/>{b} : {c}")
    )
    .set_series_opts(
        axisline_opts=opts.AxisLineOpts(
            linestyle_opts=opts.LineStyleOpts(
                width=30,
                opacity=1,
                color=[
                    (0.15, "#E74C3C"),
                    (0.25, "#EC7063"),
                    (0.6, "#F4D03F"),
                    (0.75, "#2ECC71"),
                    (1.0, "#27AE60"),
                ]
            )
        ),
        axis_tick_opts=opts.AxisTickOpts(is_show=False),
        split_line_opts=opts.SplitLineOpts(is_show=False),
    )
)

# === 顯示圖表 ===
st_pyecharts(gauge)

# === 燈號與建議 ===
if score >= 0.5:
    level = "深綠燈"
    color = "#27AE60"
    suggestion = "積極佈局、逢低買進"
elif 0.2 <= score < 0.5:
    level = "淺綠燈"
    color = "#2ECC71"
    suggestion = "小額佈局、觀察追蹤"
elif -0.5 < score < 0.2:
    level = "黃燈"
    color = "#F4D03F"
    suggestion = "觀望，等待訊號明確"
elif -0.7 < score <= -0.5:
    level = "淺紅燈"
    color = "#EC7063"
    suggestion = "保守操作，停看聽"
else:
    level = "紅燈"
    color = "#E74C3C"
    suggestion = "分階段止盈、降低曝險"

# === 分數摘要與建議 ===
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="font-size:22px; font-weight:bold;">🧾 分析摘要：</div>
    <div style="font-size:20px;">
    ● <b>日期：</b> {selected_date}<br>
    ● <b>今日燈號：</b> <span style="color:{color}; font-weight:bold">{level}</span><br>
    ● <b>總分：</b> {score:.2f}<br>
    ● <b>昨日燈號：</b> {yesterday['燈號'] if yesterday is not None else '無'}<br>
    ● <b>分數變化：</b> Δ {delta_score:+.2f}
    </div>

    <br>
    <div style="font-size:22px; font-weight:bold;">🧠 決策建議：</div>
    <div style="font-size:20px; font-weight:bold; color:{color};">
    {suggestion}
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="font-size:22px; font-weight:bold;">📊 燈號分數對照表</div>

    <table style="font-size:18px; border-collapse: collapse;">
        <thead>
            <tr>
                <th style="text-align:left;">顏色</th>
                <th style="text-align:left;">燈號</th>
                <th style="text-align:left;">分數範圍</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><span style="color:#27AE60">●</span></td>
                <td>深綠燈</td>
                <td>≧ 0.5</td>
            </tr>
            <tr>
                <td><span style="color:#2ECC71">●</span></td>
                <td>淺綠燈</td>
                <td>0.2 ～ 0.5</td>
            </tr>
            <tr>
                <td><span style="color:#F4D03F">●</span></td>
                <td>黃燈</td>
                <td>-0.5 ～ 0.2</td>
            </tr>
            <tr>
                <td><span style="color:#EC7063">●</span></td>
                <td>淺紅燈</td>
                <td>-0.7 ～ -0.5</td>
            </tr>
            <tr>
                <td><span style="color:#E74C3C">●</span></td>
                <td>紅燈</td>
                <td>≦ -0.7</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
