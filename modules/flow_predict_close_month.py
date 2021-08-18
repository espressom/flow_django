
# 종목의 종가 예측 모듈

class predict_close :
    """
    설명 : 종목의 종가를 예측 해 주는 모듈
    param : 종목코드
    return : 다음날의 예측 종가
    """

    from sklearn.svm import SVR
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pandas_datareader import data as pdr # 주식데이터를 읽어온다
    from pykrx import stock
    from datetime import datetime, timedelta
    
    def __init__ (self, code) :
        today = self.datetime.today().strftime("%Y%m%d")  
        monthago = (self.datetime.today() - self.timedelta(365)).strftime("%Y%m%d")
        self.df =  self.stock.get_market_ohlcv_by_date( monthago , today, code)['종가']
        self.days = [ [j+1] for j in range(len(self.df)) ]
        
    def get_close (self) :
        rbf_srv = self.SVR(kernel = 'rbf', C=1000, gamma=0.05)
        rbf_srv.fit(self.days, self.df)
        day = [[ len(self.days)+30 ]]
        return rbf_srv.predict(day) # 예측 종가 리턴



