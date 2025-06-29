import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# === 1. 載入資料並處理 ===
STOCK_ID = "00646"
base_path = os.path.dirname(__file__)
filename = f"ETF_signal_{STOCK_ID}.csv"
df = pd.read_csv(os.path.join(base_path, filename))
df['Date'] = pd.to_datetime(df['Date'])
df = df.rename(columns={'Date': 'date', '市價': 'close', '燈號': 'signal'})
df = df.sort_values('date').reset_index(drop=True)

# === 載入調整收盤價資料（Adj Close） ===
price_filename = f"{STOCK_ID}_price_data.csv"
price_df = pd.read_csv(price_filename)
price_df['Date'] = pd.to_datetime(price_df['Date'])
price_df = price_df.rename(columns={'Adj Close': 'adj_close'})
df = df.merge(price_df[['Date', 'adj_close']], how='left', left_on='date', right_on='Date')
df['close'] = df['adj_close'].fillna(df['close'])
df.drop(columns=['Date', 'adj_close'], inplace=True)

# 燈號轉換邏輯
signal_map = {
    '淺綠燈': 1,
    '綠燈': 1,
    '淺紅燈': -1,
    '紅燈': -1,
    '黃燈': 0
}
df['signal'] = df['signal'].map(signal_map).fillna(0).astype(int)

# === 2. 設定參數 ===
transaction_cost_rate = 0.001
tax_rate = 0.003
position_fraction = 0.1  # 每次固定投入10%資金


# === 3. 多筆倉位回測主程式 ===
positions = []
equity = 100000  # 初始資金
equity_curve = []
trades = []

for i, row in df.iterrows():
    date = row['date']
    price = row['close']
    signal = row['signal']

    if signal == 1:
        position_size = equity * position_fraction
        entry_price = price * (1 + transaction_cost_rate)
        positions.append({
            'entry_date': date,
            'entry_price': entry_price,
            'position_size': position_size
        })

    elif signal == -1 and positions:
        position = positions.pop(0)
        exit_price = price * (1 - transaction_cost_rate - tax_rate)
        ret = (exit_price / position['entry_price']) - 1
        profit = position['position_size'] * ret
        equity += profit
        trades.append({
            'entry_date': position['entry_date'],
            'exit_date': date,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'return': ret,
            'position_size': position['position_size'],
            'profit': profit,
            'holding_days': (date - position['entry_date']).days
        })

    equity_curve.append(equity)

df['equity'] = equity_curve

# === 4. 回撤與績效計算 ===
df['peak'] = df['equity'].cummax()
df['drawdown'] = (df['equity'] - df['peak']) / df['peak']
df['drawdown'] = pd.to_numeric(df['drawdown'], errors='coerce').fillna(0.0).astype(float)

trade_df = pd.DataFrame(trades)
# 安全提取 equity 起訖值
if 'equity' in df.columns and not df['equity'].isna().all():
    start_equity = df['equity'].iloc[0]
    end_equity = df['equity'].iloc[-1]
else:
    start_equity = end_equity = np.nan
# 安全計算報酬率
if pd.notna(start_equity) and pd.notna(end_equity) and start_equity > 0:
    total_return = (end_equity / start_equity) - 1
else:
    total_return = np.nan
# 安全計算年化報酬
if 'date' in df.columns and not df['date'].empty:
    total_days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
    if total_days > 0 and not np.isnan(total_return):
        annualized_return = (1 + total_return) ** (365 / total_days) - 1
    else:
        annualized_return = np.nan
else:
    total_days = 0
    annualized_return = np.nan

win_rate = (trade_df['return'] > 0).mean() if not trade_df.empty else 0
avg_return = trade_df['return'].mean() if not trade_df.empty else 0
max_drawdown_trade = trade_df['return'].min() if not trade_df.empty else 0
max_drawdown_pct = df['drawdown'].min()

# === 5. 繪製資金曲線圖（log Y 軸） ===
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['equity'], label='Equity Curve', color='blue')
plt.yscale('log')
plt.title(f'Equity Curve (Fixed {int(position_fraction * 100)}% Position, Log Scale)')
plt.xlabel('Date')
plt.ylabel('Equity Value (log scale)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(f"equity_curve_multi_position_{STOCK_ID}.png")
plt.close()

# === 6. 輸出績效 ===
print(f"績效報告：{STOCK_ID}")
print(f"初始資金: {start_equity:,.2f}")
print(f"結束資金: {end_equity:,.2f}")
print(f"交易次數: {len(trade_df)}")
print(f"總報酬率: {total_return:.2%}" if not np.isnan(total_return) else "總報酬率: N/A")
print(f"勝率: {win_rate:.2%}")
print(f"平均每筆報酬: {avg_return:.2%}")
print(f"最大單次虧損: {max_drawdown_trade:.2%}")
print(f"年化報酬率: {annualized_return:.2%}" if not np.isnan(annualized_return) else "年化報酬率: N/A")
print(f"最大回撤: {max_drawdown_pct:.2%}")

# === 7. 匯出交易紀錄 ===
trade_df.to_csv(f"multi_position_trade_log_{STOCK_ID}.csv", index=False)
