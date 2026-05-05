import yfinance as yf

def load_data(ticker, period):
    df = yf.download(ticker, period = period)
    if df.empty:
        raise ValueError("Invalid Ticker")
    return df



