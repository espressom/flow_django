from time import time
import numpy as np
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
from modules import database as db


oracleDB = db.oracleDB



########## Final #####
def query_OracleSQL(sql):
    # db = "flow79/kosmo7979@192.168.0.47/xe" # 본인 윈도우 IP
    try:
        conn = ora.connect(oracleDB)
        cursor = conn.cursor()
        res = pd.read_sql(sql, conn)
    finally:
        cursor.close()
        conn.close()
    return res

### CompanyDetail에 종목 별 차트 띄우기 ###
class Company_Chart:
    """
    종목 별 차트
    """

    def __init__(self):
        sql = 'SELECT c_code, c_name FROM company'
        self.companies = query_OracleSQL(sql)
        self.companies.index = self.companies['C_CODE']
        self.start = datetime.now() - relativedelta(years=1)  # 오늘날짜 - 1년
        self.start = self.start.strftime('%Y-%m-%d')



    def chart_json(self, code):
        """
        :param code: 기업 코드
        :return: 해당 기업의 최근 1년 캔들차트, 볼린저 밴드, 거래량 그래프 json Data
        """
        name = self.companies.loc[code]['C_NAME']
        df = fdr.DataReader(code, self.start)
        print('{} Graph'.format(name))
        qf = cf.QuantFig(df,
                         title=name ,
                         legend='top',
                         name=name,
                         up_color='red',
                         down_color='blue')
        qf.add_bollinger_bands(periods=20, boll_std=2)
        qf.add_volume()
        data = qf.iplot(asFigure=True) # 크기 조절 필요 , dimensions=(850, 550)
        return data.to_json() # 차트를 json 데이터로


########### TreeMap #############


class TreeMap:
    """
    당일 거래량 상위종목의 섹터(등락률 그룹)별 트리맵
    """

    # 거래량 상위종목 목록 받아오기
    def get_stock_names(self):
        """
        :return: KOSPI, KOSDAQ 거래량 상위종목 리스트
        """
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

    def __get_dict_data(self):
        stock_list = self.get_stock_names()
        sql = 'SELECT c_code, c_name, c_category, c_market FROM company'
        companies = query_OracleSQL(sql)
        dict_data = dict()
        count = 0
        companies = companies[(companies['C_NAME'].isin(stock_list))]
        for company in tqdm(companies['C_NAME']):
            code = companies[companies['C_NAME'] == company]['C_CODE'].values[0].strip()
            category = companies[companies['C_NAME'] == company]['C_CATEGORY'].values[0].strip()
            market = companies[companies['C_NAME'] == company]['C_MARKET'].values[0].strip()
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
            dict_data[company]['코드'] = code
            count += 1
            if count % 99 == 0:
                time.sleep(2)
        return dict_data

    # 얘를 1시간마다 갱신해야될것같음
    def __make_dataframe(self):
        dict_data = self.__get_dict_data()
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


    def treeMap_json(self, m_id='non-login', opt='volume'):
        """
        :param opt: 트리맵 value 기준 =>
            'volume'(default) : 거래량, 'close' : 종가, 'fgroup' : 등락률 그룹
        :return: 트리맵 json Data
        """
        # make_dataframe() # <===== 얘를 1시간 마다??
        now = datetime.now()
        title = now.strftime("%Y-%m-%d %H시 기준")
        # print(sorted(os.listdir('stock/static/treemap'))[-1])
        try:
            df_tm = pd.read_csv('stock/static/treemap/{} 트리맵.csv'.format(title),index_col=0,converters={'코드':str}) # 파일 없을때 예외처리 필요
        except:
            t = threading.Thread(target=self.__make_dataframe)
            t.start()
            title = sorted(os.listdir('stock/static/treemap'))[-1][:-8]   # treemap 폴더에 제일 최신값 가져옴 (없으면??)
            df_tm = pd.read_csv('stock/static/treemap/{} 트리맵.csv'.format(title), index_col=0)
            pass

        labels = ['(?)', '-8% 이하', '-6 ~ -8%', '-4 ~ -6%', '-2 ~ -4%', '0 ~ -2%', '0 ~ 2%', '2 ~ 4%', '4 ~ 6%', '6 ~ 8%',
                  '8% 이상']
        col = ['#00FF00', '#00CC00', '#009900', '#006600', '#135213', '#440000', '#660000', '#960000', '#CC0000', '#FF0000',
               '#FFFFFF']
        col.reverse()
        cmap = dict(zip(labels, col))

        # opt = request.GET['opt']
        if opt == 'volume':
            path = ['마켓', '카테고리', df_tm.index]
            values = '거래량'
            c_data = ['등락률', '전일비', '종가', '코드']
            texttemplate = "<a href='companyDetail?c_code=%{customdata[3]:06d}&m_id="+m_id\
                           +"'>%{label}</a><br>%{customdata[2]}<br>%{customdata[0]:.2f}%"
        elif opt == 'close':
            path = ['마켓', '카테고리', df_tm.index]
            values = '종가'
            c_data = ['등락률', '전일비', '거래량', '코드']
            texttemplate = "<a href='companyDetail?c_code=%{customdata[3]:06d}&m_id="+m_id\
                           +"'>%{label}</a><br>%{value}<br>%{customdata[0]:.2f}%"
        elif opt == 'fgroup':
            path = ['마켓', '등락률그룹', df_tm.index]
            values = '거래량'
            c_data = ['등락률', '전일비', '종가', '코드']
            texttemplate = "<a href='companyDetail?c_code=%{customdata[3]:06d}&m_id="+m_id\
                           +"'>%{label}</a><br>%{customdata[2]}<br>%{customdata[0]:.2f}%"

        fig = px.treemap(df_tm,
                         path=path,
                         values=values,
                         color='등락률그룹',
                         color_discrete_map=cmap,
                         title=title,
                         template='presentation',
                         custom_data=c_data,
                         height=900,width=1200 # 크기 조정 필요
                         )

        fig.data[0].hovertemplate = "종목명:%{label}<br>"+values+":%{value}<br>"+c_data[0]+":%{customdata[0]:.2f}%\
            <br>"+c_data[1]+":%{customdata[1]:,}\
            <br>"+c_data[2]+":%{customdata[2]:,}\
            "
        fig.data[0].texttemplate = texttemplate
        fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
        fig_json = json.loads(fig.to_json())
        return fig_json

