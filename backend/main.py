from fastapi import FastAPI, HTTPException
import yfinance as yf
from data_loader import load_data
from data_preprocessing import get_close
from metrics import *
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

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
def price_history(ticker: str, rng: str = "1Y"):
    rng = rng.upper()
    if rng not in RANGE_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid range. Choose from {list(RANGE_CONFIG)}")

    cfg = RANGE_CONFIG[rng]
    df = load_data(ticker, period=cfg["period"], interval=cfg["interval"])
    close = df['Close'].squeeze()

    fmt = "%y-%m-%d %H:%M" if cfg["interval"] in INTRADAY else "%y-%m-%d"
    dates = close.index.strftime(fmt).to_list()
    prices = close.round(2).to_list()
    return {'dates': dates, 'price': prices}

@app.get("/compare")
def compare(ticker1: str, ticker2: str, rng: str = "1Y"):
    rng = rng.upper()
    if rng not in RANGE_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid range. Choose from {list(RANGE_CONFIG)}")

    cfg = RANGE_CONFIG[rng]
    df1 = load_data(ticker1, period=cfg["period"], interval=cfg["interval"])
    df2 = load_data(ticker2, period=cfg["period"], interval=cfg["interval"])

    close1 = df1['Close'].squeeze()
    close2 = df2['Close'].squeeze()

    t1, t2 = ticker1.upper(), ticker2.upper()

    combined = pd.concat([close1, close2], axis=1, join='inner')
    combined.columns = [t1, t2]

    if combined.empty:
        raise HTTPException(status_code=404, detail="No overlapping data between the two tickers")

    normalized = (combined / combined.iloc[0] - 1) * 100

    fmt = "%y-%m-%d %H:%M" if cfg["interval"] in INTRADAY else "%y-%m-%d"
    dates = combined.index.strftime(fmt).to_list()

    return {
        "dates": dates,
        t1: normalized[t1].round(2).tolist(),
        t2: normalized[t2].round(2).tolist(),
    }

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


@app.get("/all-metrics")
def get_all_metrics(ticker: str):
    df = load_data(ticker, period="5y")
    close = df["Close"].squeeze()
    t = yf.Ticker(ticker)
    d_returns = daily_returns(close)

    result = {}

    # Price metrics
    # result["daily_returns"] = d_returns.dropna().round(4).tolist()
    # result["total_returns"] = total_returns(d_returns).dropna().round(4).tolist()
    # result["rolling_returns"] = {
    #     "roll_20": rolling_returns(df)["roll_20"].dropna().round(4).tolist(),
    #     "roll_252": rolling_returns(df)["roll_252"].dropna().round(4).tolist()
    # }

    # Risk metrics

    result["annual_volatility"] = round(annual_volatility(d_returns), 4)
    result["sharpe_ratio"] = round(sharpe_ratio(d_returns, 0.05), 4)
    result["value_at_risk"] = round(value_at_risk(d_returns), 4)

    # Valuation
    pe = PE_Share(t, df)
    result["pe_ratio"] = round(pe, 4) if pe is not None else None
    pb = pb_ratio(t, df)
    result["pb_ratio"] = pb.dropna().round(4).tolist() if pb is not None else None
    div = dividend_yield(df, t)
    result["dividend_yield"] = round(div, 4) if div is not None else None
    ps = ps_ratio(t, df)
    result["ps_ratio"] = ps.dropna().round(4).tolist()

    # Fundamentals
    result["revenue_growth"] = revenue_growth(t).dropna().round(4).tolist()
    result["profit_margin"] = profit_margin(t).dropna().round(4).tolist()
    result["gross_margin"] = Gross_margin(t).dropna().round(4).tolist()
    result["earnings_growth"] = earnings_growth(t).dropna().round(4).tolist()
    result["roe"] = ROE(t).dropna().round(4).tolist()

    # Cash flow
    result["operating_cash_flow"] = operating_cash_flow(t).dropna().round(4).tolist()
    result["free_cash_flow"] = free_cash_flow(t).dropna().round(4).tolist()
    result["free_cash_flow_growth"] = free_cash_flow_growth(t).dropna().round(4).tolist()

    # Leverage & efficiency
    result["debt_to_equity"] = debt_to_equity(t).dropna().round(4).tolist()
    result["asset_turnover"] = asset_turnover(t).dropna().round(4).tolist()

    return result
