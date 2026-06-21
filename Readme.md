# Stock-Wars 📈

An intelligent, full-stack stock analysis and prediction dashboard that combines real-time financial metrics, multi-stock comparison, and LSTM-based 30-day price forecasting — all in one interface.

**Live Demo:** [stock-wars-frontend.onrender.com](https://stock-wars-frontend.onrender.com)  
**Source Code:** [github.com/botash3d/stock-wars](https://github.com/botash3d/stock-wars)

> ⚠️ **Note:** The first prediction call per ticker may take 2–5 minutes on the live demo due to on-demand LSTM training on a free-tier CPU instance.

---

## Features

- **Price History Visualization** — Interactive OHLCV charts with configurable time ranges (1D to MAX)
- **Comprehensive Metrics** — Risk metrics (volatility, Sharpe ratio, Value at Risk) and fundamental metrics (P/E, P/B, P/S, ROE, revenue growth, free cash flow)
- **Multi-Stock Comparison** — Side-by-side normalized percentage-change comparison for two tickers
- **LSTM Price Prediction** — 30-day forward return prediction using a PyTorch LSTM model
- **Market-Relative Signals** — Predicts stock return *relative to SPY (S&P 500)*, producing actionable Outperform / Underperform signals that are robust to overall market direction
- **Fault-Tolerant** — Per-metric error isolation ensures ETFs and recently listed stocks don't crash the API
- **TTL Caching** — 10-minute in-memory cache on all heavy endpoints to avoid redundant data fetches

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, Tailwind CSS 4, Recharts, Axios |
| Backend | FastAPI, Python 3.11, Uvicorn |
| ML | PyTorch (CPU), scikit-learn, NumPy, pandas |
| Data | yfinance |
| Containerization | Docker, Docker Compose |
| Deployment | Render |

---

## Architecture

```
┌─────────────────────────────┐       ┌──────────────────────────────────┐
│     React Frontend           │       │         FastAPI Backend           │
│  (Vite + Tailwind + Recharts)│◄─────►│                                  │
└─────────────────────────────┘  HTTP │  ┌──────────┐  ┌─────────────┐  │
                                       │  │ metrics  │  │  predictor  │  │
                                       │  │   .py    │  │    .py      │  │
                                       │  └──────────┘  └─────────────┘  │
                                       │        │               │         │
                                       │        ▼               ▼         │
                                       │  ┌──────────────────────────┐   │
                                       │  │        yfinance           │   │
                                       │  │   (Yahoo Finance API)     │   │
                                       │  └──────────────────────────┘   │
                                       └──────────────────────────────────┘
```

The system follows a client-server architecture with three logical layers:
1. **Data layer** — `yfinance` fetches OHLCV data and financial statements
2. **Backend layer** — FastAPI exposes REST endpoints; `metrics.py` computes financial metrics; `model.py` and `predictor.py` implement the LSTM pipeline
3. **Frontend layer** — React renders interactive charts and communicates with the backend via Axios

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /price-history?ticker=AAPL&rng=1Y` | OHLCV data for a configurable time range |
| `GET /compare?ticker1=AAPL&ticker2=MSFT&rng=1Y` | Normalized % change for two tickers |
| `GET /company-info?ticker=AAPL` | Company name, sector, market cap, current price |
| `GET /all-metrics?ticker=AAPL` | All risk and fundamental metrics |
| `GET /predict?ticker=AAPL` | LSTM 30-day return prediction |
| `GET /cache/clear` | Manually invalidate the TTL cache |

All heavy endpoints are cached with a 10-minute TTL.

---

## ML Model

### Architecture
A 2-layer stacked LSTM (64 hidden units, 0.2 dropout) followed by a single linear layer. The model reads a **60-day window of daily returns** and predicts the **30-day cumulative return** in a single forward pass — avoiding the compounding error of autoregressive day-by-day prediction.

### Market-Relative Prediction
Two independent LSTM models are trained per prediction call — one on the target stock, one on SPY. The relative signal is:

```
relative_return = predicted_stock_return − predicted_SPY_return
```

This eliminates bull-market bias: a stock predicted to gain 3% in a market predicted to gain 5% correctly receives an **Underperform** signal.

### Training
- **Data:** 5 years of daily OHLCV (~1,250 trading days, ~1,160 sequence-target pairs)
- **Optimizer:** Adam with StepLR scheduler (γ=0.5 every 30 epochs)
- **Loss:** MSE
- **Epochs:** 100
- **Scaler:** Two independent MinMaxScaler instances for inputs and targets

---

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/) and Docker Compose
- Node.js 18+ (for local frontend development without Docker)
- Python 3.11+ (for local backend development without Docker)

### Run with Docker Compose (Recommended)

```bash
git clone https://github.com/botash3d/stock-wars.git
cd stock-wars
docker-compose up --build
```

This starts:
- **Backend** at `http://localhost:8000`
- **Frontend** at `http://localhost:5173`

### Run Locally (without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend/stocks-UI
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

---

## Project Structure

```
stock-wars/
├── backend/
│   ├── main.py              # FastAPI app, endpoints, TTL cache
│   ├── metrics.py           # Risk & fundamental metric computations
│   ├── model.py             # StockLSTM PyTorch model definition
│   ├── predictor.py         # Sequence prep, training loop, prediction
│   ├── data_loader.py       # yfinance data fetching helpers
│   ├── data_preprocessing.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── stocks-UI/
│       ├── src/
│       │   ├── App.jsx      # Main dashboard component
│       │   └── App.css
│       ├── package.json
│       └── Dockerfile
├── docker-compose.yml
└── Data/
```

---

## Configuration

The frontend reads the backend URL from an environment variable:

```env
VITE_API_URL=http://localhost:8000
```

Set this in a `.env` file inside `frontend/stocks-UI/` for local development, or pass it via `docker-compose.yml` as shown.

---

## Known Limitations

- The LSTM model uses only closing price returns as features — no volume, macro indicators, or sentiment data.
- Models are trained on-the-fly per request; a production system would pre-train and persist models to a registry.
- The predicted price curve uses linear interpolation between the current price and the predicted endpoint — the daily path is not modeled.
- Free-tier Render instances (0.1 CPU, 512 MB RAM) result in 2–5 minute first-call latency for predictions.

---

## Future Work

- [ ] Add volume, RSI, MACD, and macroeconomic indicators as model features
- [ ] Pre-train models offline and serve via a model registry
- [ ] Evaluate directional accuracy on a held-out test set
- [ ] Add a watchlist feature with persistent storage and alert notifications
- [ ] Extend predictions with uncertainty quantification (confidence intervals)

---

## References

- Hochreiter & Schmidhuber, "Long Short-Term Memory," *Neural Computation*, 1997
- Kingma & Ba, "Adam: A Method for Stochastic Optimization," ICLR 2015
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [yfinance](https://pypi.org/project/yfinance/)

---

## Author

**Ashwani Mishra** — B.Sc. (Honours) Data Science and Artificial Intelligence, IIT Guwahati  
[m.ashwani@op.iitg.ac.in](mailto:m.ashwani@op.iitg.ac.in)

Term Project (DA378), Trimester VIII
