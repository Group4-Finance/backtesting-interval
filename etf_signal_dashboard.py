import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# === 載入資料 ===
df = pd.read_csv("ETF_signal/ETF_data/ETF_signal_00646.csv", parse_dates=["Date"])
df = df[df["總分"].notna()].sort_values("Date")
available_dates = df["Date"].dt.date.unique()

# === 標題 ===
st.title("📈 ETF 買賣決策信號儀表")

# === 使用 selectbox 選擇日期（只列出有資料的日期）===
selected_date = st.selectbox("請選擇查詢日期", available_dates)

# === 取得當日與昨日資料 ===
try:
    today = df[df["Date"].dt.date == selected_date].iloc[0]
    idx = df[df["Date"].dt.date == selected_date].index[0]
    yesterday = df.iloc[idx - 1] if idx > 0 else None
except:
    st.warning(f"⚠️ 選擇的日期 {selected_date} 沒有資料。")
    st.stop()

# === 計算 Δ 分數 ===
delta_score = today["總分"] - yesterday["總分"] if yesterday is not None else 0

# === 儀表圖 ===
fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=today["總分"],
    delta={'reference': yesterday["總分"] if yesterday is not None else 0},
    gauge={
        'axis': {'range': [-1, 1]},
        'bar': {'color': "black"},
        'steps': [
            {'range': [-1, -0.7], 'color': "#B00000"},     # 紅燈
            {'range': [-0.7, -0.5], 'color': "salmon"},    # 淺紅燈
            {'range': [-0.5, 0.2], 'color': "#FFD700"},    # 黃燈
            {'range': [0.2, 0.5], 'color': "lightgreen"},  # 淺綠燈
            {'range': [0.5, 1], 'color': "#008000"},       # 深綠燈
        ],
    },
    title={'text': f"{selected_date} 信號燈分數"}
))

# === 顯示儀表圖 ===
st.plotly_chart(fig)

# === 顯示摘要 ===
st.markdown(f"""
### 🧾 分析摘要：
- **日期：** {selected_date}
- **今日燈號：** {today['燈號']}
- **總分：** {today['總分']:.2f}
- **昨日燈號：** {yesterday['燈號'] if yesterday is not None else '無'}
- **分數變化：** Δ {delta_score:+.2f}
""")