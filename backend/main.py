from fastapi import FastAPI, HTTPException
import yfinance as yf
from data_loader import load_data
from data_preprocessing import get_close
from metrics import *
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import time
from functools import wraps
from predictor import train_and_predict

# ----- Simple TTL cache -----
_cache: dict = {}
TTL = 600  # seconds (10 min)

def cached(key_fn):
    """Decorator that caches the return value of a route function by a dynamic key."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = key_fn(**kwargs)
            now = time.time()
            if key in _cache:
                value, ts = _cache[key]
                if now - ts < TTL:
                    return value
            result = fn(*args, **kwargs)
            _cache[key] = (result, now)
            return result
        return wrapper
    return decorator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"Hello": "World"}

RANGE_CONFIG = {
    "1D":  {"period": "1d",  "interval": "5m"},
    "5D":  {"period": "5d",  "interval": "15m"},
    "1M":  {"period": "1mo", "interval": "1d"},
    "6M":  {"period": "6mo", "interval": "1d"},
    "YTD": {"period": "ytd", "interval": "1d"},
    "1Y":  {"period": "1y",  "interval": "1d"},
    "5Y":  {"period": "5y",  "interval": "1wk"},
    "MAX": {"period": "max", "interval": "1mo"},
}
INTRADAY = {"1m", "5m", "15m", "30m", "1h"}

@app.get("/price-history")
@cached(key_fn=lambda ticker, rng="1Y": f"price-history:{ticker.upper()}:{rng.upper()}")
def price_history(ticker: str, rng: str = "1Y"):
    rng = rng.upper()
    if rng not in RANGE_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid range. Choose from {list(RANGE_CONFIG)}")

    cfg = RANGE_CONFIG[rng]
    df = load_data(ticker, period=cfg["period"], interval=cfg["interval"])
    close = df['Close'].squeeze()
    volume = df['Volume'].squeeze()

    fmt = "%y-%m-%d %H:%M" if cfg["interval"] in INTRADAY else "%y-%m-%d"
    dates = close.index.strftime(fmt).to_list()
    prices = close.round(2).to_list()
    volumes = volume.astype(int).to_list()

    return {'dates': dates, 'price': prices, 'volume': volumes}

@app.get("/compare")
@cached(key_fn=lambda ticker1, ticker2, rng="1Y": f"compare:{ticker1.upper()}:{ticker2.upper()}:{rng.upper()}")
def compare(ticker1: str, ticker2: str, rng: str = "1Y"):
    rng = rng.upper()
    if rng not in RANGE_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid range. Choose from {list(RANGE_CONFIG)}")

    cfg = RANGE_CONFIG[rng]
    df1 = load_data(ticker1, period=cfg["period"], interval=cfg["interval"])
    df2 = load_data(ticker2, period=cfg["period"], interval=cfg["interval"])

    close1 = df1['Close'].squeeze()
    close2 = df2['Close'].squeeze()
    volume1 = df1['Volume'].squeeze()
    volume2 = df2['Volume'].squeeze()

    t1, t2 = ticker1.upper(), ticker2.upper()

    combined = pd.concat([close1, close2], axis=1, join='inner')
    combined.columns = [t1, t2]

    vol_combined = pd.concat([volume1, volume2], axis=1, join='inner')
    vol_combined.columns = [f"{t1}_vol", f"{t2}_vol"]

    if combined.empty:
        raise HTTPException(status_code=404, detail="No overlapping data between the two tickers")

    normalized = (combined / combined.iloc[0] - 1) * 100

    fmt = "%y-%m-%d %H:%M" if cfg["interval"] in INTRADAY else "%y-%m-%d"
    dates = combined.index.strftime(fmt).to_list()

    return {
        "dates": dates,
        t1: normalized[t1].round(2).tolist(),
        t2: normalized[t2].round(2).tolist(),
        f"{t1}_vol": vol_combined[f"{t1}_vol"].astype(int).tolist(),
        f"{t2}_vol": vol_combined[f"{t2}_vol"].astype(int).tolist(),
    }

@app.get("/company-info")
@cached(key_fn=lambda ticker: f"company-info:{ticker.upper()}")
def get_company_info(ticker: str):
    try:
        t = yf.Ticker(ticker)
        info = t.info

        if not info or len(info) <= 1:
            raise HTTPException(status_code=404, detail="No info available for this ticker")

        name = info.get("longName") or info.get("shortName") or ticker.upper()
        sector = info.get("sector") or info.get("industryDisp") or "N/A"
        market_cap = info.get("marketCap")
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        currency = info.get("currency", "USD")

        def fmt_market_cap(mc):
            if mc is None: return "N/A"
            if mc >= 1e12: return f"${mc / 1e12:.2f}T"
            if mc >= 1e9:  return f"${mc / 1e9:.2f}B"
            if mc >= 1e6:  return f"${mc / 1e6:.2f}M"
            return f"${mc:,.0f}"

        return {
            "name": name,
            "sector": sector,
            "market_cap": fmt_market_cap(market_cap),
            "price": round(price, 2) if price else None,
            "currency": currency,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/daily-returns")
def get_daily_returns(ticker: str):
    df = load_data(ticker, period="5y")
    close = df["Close"].squeeze()  # flatten to Series if MultiIndex
    returns = daily_returns(close)
    return {"daily_returns": returns.dropna().round(4).tolist()}

@app.get("/total-returns")
def get_total_returns(ticker: str):
    df = load_data(ticker, period="5y")
    close = df["Close"].squeeze()
    d_returns = daily_returns(close)
    t_returns = total_returns(d_returns)
    return {"total_returns": t_returns.dropna().round(4).tolist()}

@app.get("/annual-volatility")
def get_annual_volatility(ticker: str):
    df = load_data(ticker, period="5y")
    close = df["Close"].squeeze()
    d_returns = daily_returns(close)
    av_returns = annual_volatility(d_returns)
    return {"annual_volatility": round(av_returns, 4)}

@app.get("/sharpe_ratio")
def get_sharpe_ratio(ticker: str):
    df = load_data(ticker, period="5y")
    close = df["Close"].squeeze()
    d_returns = daily_returns(close)
    sr_returns = sharpe_ratio(d_returns, 0.05)
    return {"sharpe_ratio":round(sr_returns, 4)}

@app.get("/value_at_risk")
def get_value_at_risk(ticker:str):
    df = load_data(ticker, period = "5y")
    close = df["Close"].squeeze()
    d_returns = daily_returns(close)
    var = value_at_risk(d_returns)
    return {"value_at_risk": round(var, 4)}

@app.get("/beta")
def get_beta(ticker: str, market: str = "^GSPC"):
    df = load_data(ticker, period="5y")
    market_df = load_data(market, period="5y")
    close = df["Close"].squeeze()
    market_close = market_df["Close"].squeeze()
    d_returns = daily_returns(close)
    m_returns = daily_returns(market_close)
    b = beta(d_returns, m_returns)
    return {"beta": round(b, 4)}

@app.get("/revenue-growth")
def get_revenue_growth(ticker: str):
    t = yf.Ticker(ticker)
    result = revenue_growth(t)
    return {"revenue_growth": result.dropna().round(4).tolist()}

@app.get("/profit-margin")
def get_profit_margin(ticker: str):
    t = yf.Ticker(ticker)
    result = profit_margin(t)
    return {"profit_margin": result.dropna().round(4).tolist()}

@app.get("/pe-ratio")
def get_pe_ratio(ticker: str):
    df = load_data(ticker, period="5y")
    t = yf.Ticker(ticker)
    result = PE_Share(t, df)
    if result is None:
        raise HTTPException(status_code=404, detail="EPS not available for this ticker")
    return {"pe_ratio": round(result, 4)}

@app.get("/roe")
def get_roe(ticker: str):
    t = yf.Ticker(ticker)
    result = ROE(t)
    return {"roe": result.dropna().round(4).tolist()}

@app.get("/earnings-growth")
def get_earnings_growth(ticker: str):
    t = yf.Ticker(ticker)
    result = earnings_growth(t)
    return {"earnings_growth": result.dropna().round(4).tolist()}

@app.get("/operating-cash-flow")
def get_operating_cash_flow(ticker: str):
    t = yf.Ticker(ticker)
    result = operating_cash_flow(t)
    return {"operating_cash_flow": result.dropna().round(4).tolist()}

@app.get("/free-cash-flow")
def get_free_cash_flow(ticker: str):
    t = yf.Ticker(ticker)
    result = free_cash_flow(t)
    return {"free_cash_flow": result.dropna().round(4).tolist()}

@app.get("/free-cash-flow-growth")
def get_free_cash_flow_growth(ticker: str):
    t = yf.Ticker(ticker)
    result = free_cash_flow_growth(t)
    return {"free_cash_flow_growth": result.dropna().round(4).tolist()}

@app.get("/debt-to-equity")
def get_debt_to_equity(ticker: str):
    t = yf.Ticker(ticker)
    result = debt_to_equity(t)
    return {"debt_to_equity": result.dropna().round(4).tolist()}

@app.get("/asset-turnover")
def get_asset_turnover(ticker: str):
    t = yf.Ticker(ticker)
    result = asset_turnover(t)
    return {"asset_turnover": result.dropna().round(4).tolist()}

@app.get("/rolling-returns")
def get_rolling_returns(ticker: str):
    df = load_data(ticker, period="5y")
    result = rolling_returns(df)
    return {
        "roll_20": result["roll_20"].dropna().round(4).tolist(),
        "roll_252": result["roll_252"].dropna().round(4).tolist()
    }

@app.get("/gross-margin")
def get_gross_margin(ticker: str):
    t = yf.Ticker(ticker)
    result = Gross_margin(t)
    return {"gross_margin": result.dropna().round(4).tolist()}

@app.get("/dividend-yield")
def get_dividend_yield(ticker: str):
    df = load_data(ticker, period="5y")
    t = yf.Ticker(ticker)
    result = dividend_yield(df, t)
    if result is None:
        raise HTTPException(status_code=404, detail="Dividend not available for this ticker")
    return {"dividend_yield": round(result, 4)}

@app.get("/pb-ratio")
def get_pb_ratio(ticker: str):
    df = load_data(ticker, period="5y")
    t = yf.Ticker(ticker)
    result = pb_ratio(t, df)
    return {"pb_ratio": result.dropna().round(4).tolist()}

@app.get("/ps-ratio")
def get_ps_ratio(ticker: str):
    df = load_data(ticker, period="5y")
    t = yf.Ticker(ticker)
    result = ps_ratio(t, df)
    return {"ps_ratio": result.dropna().round(4).tolist()}

@app.get("/cache/clear")
def clear_cache():
    _cache.clear()
    return {"cleared": True}

@app.get("/predict")
@cached(key_fn=lambda ticker: f"predict:{ticker.upper()}")
def predict(ticker: str):
    try:
        df = load_data(ticker, period="5y")
        spy_df = load_data("SPY", period="5y")
        close = df["Close"].squeeze()
        spy_close = spy_df["Close"].squeeze()

        stock_pct, spy_pct, relative_pct, predicted_prices = train_and_predict(
            close, benchmark_series=spy_close, days=30
        )

        return {
            "ticker": ticker.upper(),
            "absolute_pct": stock_pct,
            "spy_pct": spy_pct,
            "relative_pct": relative_pct,
            "direction": "outperform" if relative_pct > 0 else "underperform",
            "direction_absolute": "up" if stock_pct > 0 else "down",
            "predicted_prices": predicted_prices
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/all-metrics")
@cached(key_fn=lambda ticker: f"all-metrics:{ticker.upper()}")
def get_all_metrics(ticker: str):
    df = load_data(ticker, period="5y")
    close = df["Close"].squeeze()
    t = yf.Ticker(ticker)
    d_returns = daily_returns(close)

    def safe(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None

    result = {}

    result["annual_volatility"] = round(annual_volatility(d_returns), 4)
    result["sharpe_ratio"] = round(sharpe_ratio(d_returns, 0.05), 4)
    result["value_at_risk"] = round(value_at_risk(d_returns), 4)

    pe = safe(PE_Share, t, df)
    result["pe_ratio"] = round(pe, 4) if pe is not None else None

    div = safe(dividend_yield, df, t)
    result["dividend_yield"] = round(div, 4) if div is not None else None

    pb = safe(pb_ratio, t, df)
    result["pb_ratio"] = pb.dropna().round(4).tolist() if pb is not None else None

    ps = safe(ps_ratio, t, df)
    result["ps_ratio"] = ps.dropna().round(4).tolist() if ps is not None else None

    result["revenue_growth"]       = safe(lambda: revenue_growth(t).dropna().round(4).tolist())
    result["profit_margin"]        = safe(lambda: profit_margin(t).dropna().round(4).tolist())
    result["gross_margin"]         = safe(lambda: Gross_margin(t).dropna().round(4).tolist())
    result["earnings_growth"]      = safe(lambda: earnings_growth(t).dropna().round(4).tolist())
    result["roe"]                  = safe(lambda: ROE(t).dropna().round(4).tolist())
    result["operating_cash_flow"]  = safe(lambda: operating_cash_flow(t).dropna().round(4).tolist())
    result["free_cash_flow"]       = safe(lambda: free_cash_flow(t).dropna().round(4).tolist())
    result["free_cash_flow_growth"]= safe(lambda: free_cash_flow_growth(t).dropna().round(4).tolist())
    result["debt_to_equity"]       = safe(lambda: debt_to_equity(t).dropna().round(4).tolist())
    result["asset_turnover"]       = safe(lambda: asset_turnover(t).dropna().round(4).tolist())

    return result
