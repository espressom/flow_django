from pandas_datareader import data as pdr
from plotly.subplots import make_subplots
import yfinance as yf

# JE
def yfinance(request):
    yf.pdr_override()
    datav = pdr.get_data_yahoo(request)
    return datav

# JE
def bringCountryStockIndex(market):
    df = yfinance(market)
    dfv = df.index
    df['날짜'] = dfv
    df = df.rename(columns={'Close': '주가'})
    return df