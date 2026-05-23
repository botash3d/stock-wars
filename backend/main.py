from fastapi import FastAPI, HTTPException
import yfinance as yf
from data_loader import load_data
from data_preprocessing import get_close
from metrics import *

app = FastAPI()

@app.get("/")
def root():
    return {"Hello": "World"}

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
