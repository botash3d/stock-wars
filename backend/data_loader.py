import yfinance as yf

def load_data(ticker, period="1y",interval="1d"):
    df = yf.download(ticker, period = period,interval=interval)
    if df.empty:
        raise ValueError("Invalid Ticker")
    return df



