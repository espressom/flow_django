#!/usr/bin/env python
# coding: utf-8




class get_Stock_info :
    import cx_Oracle as ora
    import pandas as pd 
    from bs4 import BeautifulSoup
    from pykrx import stock 

    # 클래스 내부에서 사용하겠다고 초기화 한 것
    def __init__(self):
        self.kospi = self.stock.get_market_ticker_list(market="KOSPI")  # 929
        self.kosdaq = self.stock.get_market_ticker_list(market="KOSDAQ")  # 1506
        self.konex = self.stock.get_market_ticker_list(market="KONEX")  # 137
        self.index = self.sect_info()
        
        self.db = "flow79/kosmo7979@192.168.0.6/xe" # 각자의 윈도우 IP로 수정할 것 
        self.conn = self.ora.connect(self.db)
        self.cursor = self.conn.cursor()
        
 
    # 1. url 에서 기본 정보를 받아온다
    def basic_info(self) :
        url = "http://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
        column = ['C_NAME','C_CODE','C_TYPE','C_PRODUCT','C_IPO','C_CLOSINGMONTH', 
          'C_CEO','C_HOMEPAGE','C_LOCATION']
        krxV = self.pd.read_html(url,header=0)[0]
        krxV.columns = column
        krxV = krxV[['C_CODE', 'C_NAME', 'C_TYPE','C_PRODUCT','C_IPO','C_CLOSINGMONTH', 
          'C_CEO','C_HOMEPAGE','C_LOCATION' ]]
        krxV.C_CODE = krxV.C_CODE.map('{:06d}'.format) 
        return krxV
    
    # 2. C_CATEGORY : 섹터 정보 받아오기
    def sect_info(self) : # 각 섹터에 해당하는 딕셔너리를 만듦
        index = {}
        for idx, ticker in enumerate(self.stock.get_index_ticker_list(market="KOSPI")):
            if idx in range(4,26):
                ticker_name = self.stock.get_index_ticker_name(ticker)
                codes = self.stock.get_index_portfolio_deposit_file(ticker)
                index.update( {ticker : {'ticker_name':ticker_name,'codes':codes} } )
            
        for idx, ticker in enumerate(self.stock.get_index_ticker_list(market="KOSDAQ")):
            if idx in range(4,38):
                ticker_name = self.stock.get_index_ticker_name(ticker)
                codes = self.stock.get_index_portfolio_deposit_file(ticker)
                index.update( {ticker : {'ticker_name':ticker_name,'codes':codes} } )
        return index
    
    def sect_function(self, code):
        for ticker in self.index.keys():
            if code in self.index.get(ticker).get('codes'):
                return self.index.get(ticker).get('ticker_name')
        return '없음'

        
    
    # C_MARKET : 시장 정보를 받아온다 (KOSPI / KOSDAQ / KONEX)
    def market_function(self, code): 
        if code in  self.kospi:
            return 'KOSPI'
        elif code in  self.kosdaq:
            return 'KOSDAQ'
        elif code in  self.konex:
            return 'KONEX'
        
    def add_info (self) :
        # 기본 정보를 받아온다
        krxV = self.basic_info()
        # market_function 함수의 return 값을 C_MARKET에 넣는다 
        krxV['C_MARKET'] = krxV['C_CODE'].map(self.market_function)
 

        # sect_function 함수의 반환값을C_CATEGORY 컬럼을 체우고, 
        # C_IPO 컬럼을 날짜 형식으로 바꿔준다
        krxV['C_CATEGORY'] = krxV['C_CODE'].map(self.sect_function) 
 

        krxV = krxV.fillna('없음')
        krxV['C_IPO'] = self.pd.to_datetime(krxV['C_IPO'])
        return krxV
    
    def add_to_db(self): 
        krxV = self.add_info()
        
        column = ['C_CODE','C_NAME','C_TYPE','C_PRODUCT','C_IPO','C_CLOSINGMONTH', 
                  'C_CEO','C_HOMEPAGE','C_LOCATION', 'C_MARKET', 'C_CATEGORY']
        columns= ','.join(krxV.columns)  
        values=','.join([':{:d}'.format(i+1) for i in range(len(krxV.columns))])  
        sql = "MERGE INTO COMPANY USING DUAL ON (C_CODE = :1) WHEN MATCHED THEN UPDATE SET C_NAME =  :2, C_TYPE= :3 , C_PRODUCT = :4, C_IPO = :5, C_CLOSINGMONTH= :6, C_CEO= :7, C_HOMEPAGE= :8, C_LOCATION =:9 , C_MARKET = :10 , C_CATEGORY = :11 WHEN NOT MATCHED THEN INSERT ({columns:}) VALUES ({values:})"
        sql.format(columns=columns, values=values) 
        
        self.cursor.executemany(sql.format(columns=columns, values=values), krxV.values.tolist())
        self.conn.commit() 
        self.conn.close()
        print('COMPANY DB에 상장기업 데이터 삽입 완료')

 

