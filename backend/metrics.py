from math import sqrt
import yfinance as yf

def daily_returns(close): #How much did the stock move each day in %?
    daily_return = close.pct_change()*100
    return daily_return

def total_returns(daily_return):           #If I invested once, what is my total % gain/loss over time?
    return ((1+daily_return/100).cumprod() - 1)*100

def annual_volatility(daily_return):        #How risky is this stock in a year?
    return ((daily_return/100).std()*sqrt(252))*100     #High volatility = unstableLow volatility = stable

def sharpe_ratio(daily_return, risk_free_rate=0.05):        #Return per unit of risk
    annual_returns = (daily_return/100).mean()*252           #Higher Sharpe = better investment
    annual_vola = (daily_return/100).std()*sqrt(252)
    sharpe = (annual_returns - risk_free_rate)/annual_vola
    return sharpe

def value_at_risk(daily_return):          #Loss on a bad day lol
    return daily_return.quantile(0.05)      #5th percentile lowest 5% of values


def beta(daily_return, market_return):       #how much a stock is affected by market
    beta_value = daily_return.cov(market_return)/market_return.var()     #=1 same/ >1 risky/ <1 safe
    return beta_value         #cov() → covariance how two things move together
                           # var() → variance how much market moves by itself

def rolling_returns(df):
    close = df["Close"].squeeze()  # fix MultiIndex
    roll_20 = close.pct_change(20) * 100
    roll_252 = close.pct_change(252) * 100
    return {
        'roll_20': roll_20,
        'roll_252': roll_252
    }

def revenue_growth(ticker):
    finans = ticker.financials
    revenue = finans.loc[[i for i in finans.index if "revenue" in i.lower()][0]]
    growth = revenue.pct_change() * 100
    return growth

def profit_margin(ticker):
    finans = ticker.financials
    net_income = finans.loc[[i for i in finans.index if "net income" in i.lower()][0]]
    revenue = finans.loc[[i for i in finans.index if "revenue" in i.lower()][0]]
    revenue = revenue.replace(0, float('nan'))
    profit = (net_income / revenue)*100
    return profit

def PE_Share(ticker, df):   #price per share/ earning per share
    price_per_stock = df['Close'].iloc[-1]
    earning_per_stock = ticker.info['trailingEps']
    if earning_per_stock is None or earning_per_stock == 0:
        return None
    PE = (price_per_stock / earning_per_stock)
    return PE

def ROE(ticker):                 #Return over equity
    finans = ticker.financials          #How well company uses investor money ????????????
    balance = ticker.balance_sheet          #Equity = ₹100, Profit = ₹20, ROE = 20%
    net_income = finans.loc[[i for i in finans.index if "net income" in i.lower()][0]]
    equity = balance.loc[[i for i in balance.index if "equity" in i.lower()][0]]
    equity = equity.replace(0, float('nan'))
    roe = (net_income / equity) * 100
    return roe

def Gross_margin(ticker):
    finans = ticker.financials
    revenue = finans.loc["Total Revenue"]
    gross_profit = finans.loc["Gross Profit"]
    revenue = revenue.replace(0, float('nan'))
    gross = (gross_profit / revenue) * 100
    return gross

def earnings_growth(ticker):
    finans = ticker.financials
    net_income = finans.loc[[i for i in finans.index if "net income" in i.lower()][0]]
    return net_income.pct_change() * 100


def operating_cash_flow(ticker):     #cash gen after business
    cashflow = ticker.cashflow
    cf = cashflow.loc[[i for i in cashflow.index if "operating" in i.lower()][0]]
    return cf

def free_cash_flow(ticker):          #cash left for your use
    cashflow = ticker.cashflow
    operating_cf = cashflow.loc[[i for i in cashflow.index if "operating" in i.lower()][0]]
    cap_ex = cashflow.loc[[i for i in cashflow.index if "capital ex" in i.lower()][0]]
    fcf = operating_cf - cap_ex
    return fcf

def free_cash_flow_growth(ticker):
    cashflow = ticker.cashflow
    operating_cf = cashflow.loc[[i for i in cashflow.index if "operating" in i.lower()][0]]
    cap_ex = cashflow.loc[[i for i in cashflow.index if "capital ex" in i.lower()][0]]
    cf = operating_cf - cap_ex
    return cf.pct_change()*100

def debt_to_equity(ticker):        #How much company depends on borrowing
    balance = ticker.balance_sheet
    debt = balance.loc[[i for i in balance.index if "debt" in i.lower()][0]]
    equity = balance.loc[[i for i in balance.index if "equity" in i.lower()][0]]
    equity = equity.replace(0, float('nan'))
    return (debt / equity)


def asset_turnover(ticker):        #How efficiently assets generate sales, are assests actually useful
    finans = ticker.financials
    balance = ticker.balance_sheet
    revenue = finans.loc[[i for i in finans.index if "revenue" in i.lower()][0]]
    assets = balance.loc[[i for i in balance.index if "asset" in i.lower()][0]]
    assets = assets.replace(0, float('nan'))
    return (revenue / assets)


def dividend_yield(df, ticker):           #WHAT??????????????
    price = df['Close'].squeeze().iloc[-1]        #dividend is None → company doesn’t pay dividend
    dividend = ticker.info.get('dividendRate')      # price == 0 → avoid division error
    if dividend is None or price == 0:
        return None
    return (dividend / price) * 100


def pb_ratio(ticker, df):
    balance = ticker.balance_sheet
    equity = balance.loc[[i for i in balance.index if "equity" in i.lower()][0]]
    shares = ticker.info['sharesOutstanding']
    if not shares or shares == 0:
        return None
    book_value_ps = equity / shares
    price = df['Close'].squeeze().iloc[-1]
    pb = (price / book_value_ps)
    return pb

def ps_ratio(ticker, df):
    finans = ticker.financials
    revenue = finans.loc[[i for i in finans.index if "revenue" in i.lower()][0]]
    revenue = revenue.replace(0, float('nan'))
    shares = ticker.info['sharesOutstanding']
    price = df['Close'].squeeze().iloc[-1]
    market_cap = price * shares
    ps = market_cap / revenue
    return ps


