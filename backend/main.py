from fastapi import FastAPI, HTTPException
import yfinance as yf
from data_loader import load_data
from data_preprocessing import get_close
from metrics import *

app = FastAPI()

@app.get("/")
def root():
    return {"Hello": "World"}

@app.get("/stock/{ticker}")
async def get_stock(ticker:str, period:str = "5y"):
    # try :
    #     ticker_obj = yf.Ticker(ticker)
    #     df = load_data(ticker, period)
    #     close = df['Close'][ticker]
    #     daily_return = daily_returns(close)
    #     return {
    #         ticker: {'total_returns':float(total_returns(daily_return).iloc[-1]),
    #                 'annual_volatility':float(annual_volatility(daily_return)),
    #                 'sharpe ratio':float(sharpe_ratio(daily_return)),
    #                 'value_at_risk':float(value_at_risk(daily_return)),
    #                 'rolling_returns':float(rolling_returns(df)),
    #                 'revenue_growth':float(revenue_growth(ticker_obj)),
    #                 'profit_margin':float(profit_margin(ticker_obj))}
    #          }
    # except ValueError as v:
    #     raise HTTPException(status_code=400, detail=str(v))

    try:
        df = load_data(ticker, period)
        return {ticker:str(df['Close'][ticker])}
    except:
        raise HTTPException(status_code=400, detail="Invalid Ticker")


@app.get('/compare')
async def comparing_stocks(ticker1:str, ticker2:str , period:str ="5y"):
    try:
        ticker_obj1 = yf.Ticker(ticker1)
        ticker_obj2 = yf.Ticker(ticker2)
        stock1 = load_data(ticker1, period)
        stock2 = load_data(ticker2, period)
        close1 = stock1['Close'][ticker1]
        close2 = stock2['Close'][ticker2]
        daily_return1 = daily_returns(close1)
        daily_return2 = daily_returns(close2)
        metrics1 = {'total_returns':float(total_returns(daily_return1).iloc[-1]) ,
                    'annual_volatility':float(annual_volatility(daily_return1)),
                    'sharpe ratio':float(sharpe_ratio(daily_return1)),
                    'value_at_risk':float(value_at_risk(daily_return1)),
                    'rolling_returns':(rolling_returns(stock1)),
                    'revenue_growth':float(revenue_growth(ticker_obj1)),
                    'profit_margin':float(profit_margin(ticker_obj1)),}
        return {ticker1: metrics1}
    except ValueError as V:
        raise HTTPException(status_code=400, detail=str(V))