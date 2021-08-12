import collections
from time import time

import numpy as np
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
import os
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from django.template.defaultfilters import time
import FinanceDataReader as fdr
from pykrx import stock
import cx_Oracle as ora
import requests
from bs4 import BeautifulSoup
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
import cufflinks as cf
from tqdm import tqdm
import time
import threading




########## Final #####
def query_OracleSQL(sql):
    db = "flow79/kosmo7979@192.168.0.47/xe" # 본인 윈도우 IP
    try:
        conn = ora.connect(db)
        cursor = conn.cursor()
        res = pd.read_sql(sql, conn)
    finally:
        cursor.close()
        conn.close()
    return res

### CompanyDetail에 종목 별 차트 띄우기 ###
class Company_Chart:

    def __init__(self, code):
        sql = 'SELECT c_code, c_name FROM company'
        self.code = code
        self.companies = query_OracleSQL(sql)
        self.companies.index = self.companies['C_CODE']
        self.now = datetime.now()  # 오늘 날짜
        self.start = self.now - relativedelta(years=1)  # 오늘날짜 - 1년
        self.start = self.start.strftime('%Y-%m-%d')
        self.name = self.companies.loc[code]['C_NAME']


    def chart_json(self):
        df = fdr.DataReader(self.code, self.start)
        print('{} Graph'.format(self.name))
        qf = cf.QuantFig(df,
                         title=self.name ,
                         legend='top',
                         name=self.name,
                         up_color='red',
                         down_color='blue')
        qf.add_bollinger_bands(periods=20, boll_std=2)
        qf.add_volume()
        data = qf.iplot(asFigure=True, dimensions=(850, 550)) # 크기 조절 필요
        return data.to_json() # 차트를 json 데이터로


########### TreeMap #############


class TreeMap:

    # 거래량 상위종목 목록 받아오기
    def get_stock_names(self):
        urls = ['https://finance.naver.com/sise/sise_quant.nhn?sosok=0',
                'https://finance.naver.com/sise/sise_quant.nhn?sosok=1'] # KOSPI, KOSDAQ
        header = {'User-Agent': 'Mozilla/5.0'}
        stock_names = []
        for url in urls:
            res = requests.get(url, headers=header)
            soup = BeautifulSoup(res.text, 'html.parser')
            stocks = soup.find("table", attrs={"class": "type_2"}).find_all("tr")
            for stock in stocks:
                if len(stock.find_all("td")) > 1:
                    data = stock.find_all("td")[1].text
                    stock_names.append(data)
        return stock_names

    def get_dict_data(self):
        stock_list = self.get_stock_names()
        sql = 'SELECT c_code, c_name, c_category, c_market FROM company'
        stock_code = query_OracleSQL(sql)
        dict_data = dict()
        count = 0
        stock_code = stock_code[(stock_code['C_NAME'].isin(stock_list))]
        for company in tqdm(stock_code['C_NAME']):
            code = stock_code[stock_code['C_NAME'] == company]['C_CODE'].values[0].strip()
            category = stock_code[stock_code['C_NAME'] == company]['C_CATEGORY'].values[0].strip()
            market = stock_code[stock_code['C_NAME'] == company]['C_MARKET'].values[0].strip()
            header = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit 537.36 (KHTML, like Gecko) Chrome"}
            page = 1

            url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=code)
            url = '{url}&page={page}'.format(url=url, page=page)
            #     print(url)
            try:
                res = requests.get(url, headers=header)
            except:
                pass
            data = pd.read_html(res.text, header=0)[0].dropna()
            dict_data[company] = data.iloc[0]
            if len(data) != 1:
                dict_data[company].전일비 = data.iloc[0].종가 - data.iloc[1].종가
                dict_data[company]['등락률'] = dict_data[company].전일비 / data.iloc[1].종가 * 100
            dict_data[company]['카테고리'] = category
            dict_data[company]['마켓'] = market
            count += 1
            if count % 99 == 0:
                time.sleep(2)
        return dict_data

    # 얘를 1시간마다 갱신해야될것같음
    def make_dataframe(self):
        dict_data = self.get_dict_data()
        df = pd.DataFrame(dict_data.values(), index=dict_data.keys())
        df.fillna(0, inplace=True)
        labels = ['-8% 이하', '-6 ~ -8%', '-4 ~ -6%', '-2 ~ -4%', '0 ~ -2%', '0 ~ 2%', '2 ~ 4%', '4 ~ 6%', '6 ~ 8%', '8% 이상']
        df['등락률그룹'] = pd.cut(df['등락률'], [-np.inf, -8, -6, -4, -2, 0, 2, 4, 6, 8, np.inf], labels=labels)
        df['날짜'] = pd.to_datetime(df['날짜'])
        df[['종가', '전일비', '시가', '고가', '저가', '거래량']] = df[['종가', '전일비', '시가', '고가', '저가', '거래량']].astype('int64')
        df[['등락률그룹']] = df[['등락률그룹']].astype('object')

        df_tm = df.sort_values(["거래량"], ascending=False)[:150]
        df_tm.to_csv('stock/static/treemap/'+datetime.now().strftime("%Y-%m-%d %H시 기준 트리맵.csv"))
        print(datetime.now().strftime("%Y-%m-%d %H시 기준 트리맵.csv"))


    def treeMap_json(self, opt):
        # make_dataframe() # <===== 얘를 1시간 마다??
        now = datetime.now()
        title = now.strftime("%Y-%m-%d %H시 기준")
        # print(sorted(os.listdir('stock/static/treemap'))[-1])
        try:
            df_tm = pd.read_csv('stock/static/treemap/{} 트리맵.csv'.format(title),index_col=0) # 파일 없을때 예외처리 필요
        except:
            # hour_ago = datetime.now() - relativedelta(hours=1) # 현재 시간 파일이 없으면 1시간 전 파일
            # title = hour_ago.strftime("%Y-%m-%d %H시 기준")     # 을 하려 했는데 얘까지 없으면 어짜누
            title = sorted(os.listdir('stock/static/treemap'))[-1][:-8]   # treemap 폴더에 제일 최신값 가져옴 (없으면??)
            df_tm = pd.read_csv('stock/static/treemap/{} 트리맵.csv'.format(title), index_col=0)
            t = threading.Thread(target=self.make_dataframe)
            t.start()
            pass

        labels = ['(?)', '-8% 이하', '-6 ~ -8%', '-4 ~ -6%', '-2 ~ -4%', '0 ~ -2%', '0 ~ 2%', '2 ~ 4%', '4 ~ 6%', '6 ~ 8%',
                  '8% 이상']
        col = ['#00FF00', '#00CC00', '#009900', '#006600', '#135213', '#440000', '#660000', '#960000', '#CC0000', '#FF0000',
               '#303030']
        col.reverse()
        cmap = dict(zip(labels, col))

        # opt = request.GET['opt']
        if opt == 'volume':
            path = ['마켓', '카테고리', df_tm.index]
            values = '거래량'
            c_data = ['등락률', '전일비', '종가']
            texttemplate = "%{label}<br>%{customdata[2]}<br>%{customdata[0]:.2f}%"
        elif opt == 'close':
            path = ['마켓', '카테고리', df_tm.index]
            values = '종가'
            c_data = ['등락률', '전일비', '거래량']
            texttemplate = "%{label}<br>%{value}<br>%{customdata[0]:.2f}%"
        elif opt == 'fgroup':
            path = ['마켓', '등락률그룹', df_tm.index]
            values = '거래량'
            c_data = ['등락률', '전일비', '종가']
            texttemplate = "%{label}<br>%{customdata[2]}<br>%{customdata[0]:.2f}%"

        fig = px.treemap(df_tm,
                         path=path,
                         values=values,
                         color='등락률그룹',
                         color_discrete_map=cmap,
                         title=title,
                         template='presentation',
                         custom_data=c_data,
                         height=600,width=900 # 크기 조정 필요
                         )

        fig.data[0].hovertemplate = "종목명:%{label}<br>"+values+":%{value}<br>"+c_data[0]+":%{customdata[0]:.2f}%\
            <br>"+c_data[1]+":%{customdata[1]:,}\
            <br>"+c_data[2]+":%{customdata[2]:,}\
            "
        fig.data[0].texttemplate = texttemplate
        fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
        # fig.show()
        # fig.write_html("treemap.html")
        fig_json = json.loads(fig.to_json())
        return fig_json

