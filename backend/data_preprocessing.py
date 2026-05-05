import yfinance as yf

def get_close(df):
    if df.empty:
        return None
    df.reset_index(inplace=True)
    close = df['Close']
    return close

