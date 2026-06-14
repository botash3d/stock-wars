import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from model import StockLSTM

SEQ_LEN = 60
EPOCHS = 100
LR = 0.001

def prepare_sequences(returns, seq_len, horizon=30):
    X, y = [], []
    for i in range(seq_len, len(returns) - horizon):
        X.append(returns[i - seq_len:i])
        future = returns[i:i + horizon]
        cumulative = float((1 + future).prod() - 1)
        y.append([cumulative])
    return np.array(X), np.array(y)

def train_model(returns, seq_len=SEQ_LEN, epochs=EPOCHS, lr=LR, horizon=30):
    input_scaler = MinMaxScaler()
    scaled_returns = input_scaler.fit_transform(returns.reshape(-1, 1)).flatten()

    X, y = prepare_sequences(returns, seq_len, horizon)

    target_scaler = MinMaxScaler()
    y_scaled = target_scaler.fit_transform(y)

    X_tensor = torch.tensor(X.reshape(X.shape[0], X.shape[1], 1), dtype=torch.float32)
    y_tensor = torch.tensor(y_scaled, dtype=torch.float32)

    model = StockLSTM()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.5)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(X_tensor)
        loss = criterion(output, y_tensor)
        loss.backward()
        optimizer.step()
        scheduler.step()

    model.eval()
    last_seq = scaled_returns[-seq_len:]
    last_seq_tensor = torch.tensor(
        last_seq.reshape(1, seq_len, 1), dtype=torch.float32
    )

    with torch.no_grad():
        pred_scaled = model(last_seq_tensor).numpy()

    pred_cumulative = float(target_scaler.inverse_transform(pred_scaled)[0][0])
    return pred_cumulative

def train_and_predict(close_series, benchmark_series=None, days=30):
    prices = close_series.values.astype(np.float32)
    returns = np.diff(prices) / prices[:-1]

    stock_cumulative = train_model(returns, horizon=days)
    stock_pct = round(stock_cumulative * 100, 2)

    if benchmark_series is not None:
        bench_prices = benchmark_series.values.astype(np.float32)
        bench_returns = np.diff(bench_prices) / bench_prices[:-1]
        bench_cumulative = train_model(bench_returns, horizon=days)
        spy_pct = round(bench_cumulative * 100, 2)
        relative_pct = round(stock_pct - spy_pct, 2)
    else:
        spy_pct = None
        relative_pct = None

    current_price = float(prices[-1])
    predicted_prices = [
        round(current_price * (1 + stock_cumulative * (i + 1) / days), 2)
        for i in range(days)
    ]

    return stock_pct, spy_pct, relative_pct, predicted_prices