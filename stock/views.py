# ------------------------------------- 장우석

import datetime
from modules import database as db


oracleDB = db.oracleDB

from dateutil.relativedelta import relativedelta
from django.shortcuts import render

# Create your views here.
from stock import models
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from django.http import HttpResponse, JsonResponse
from pandas_datareader import data
from datetime import datetime
import pandas as pd
import chart_studio
chart_studio.tools.set_credentials_file(username='osjang1996', api_key='Bf1UtHInSojLKXJyUKfc')
from stock import models
import chart_studio.plotly as py
import cufflinks as cf
cf.go_offline(connected=True)
import plotly.express as pt


from django.shortcuts import render
from pandas_datareader import data

def company_code(request):
    return render(request, "stock/CORPCODE.xml")


def getQuantChart(request):
    m_id = request.GET['m_id']
    print('hostid:',m_id)

    likeList = models.getLikeStock(m_id)
    print('date 번위치')
    dt_now = datetime.now()

    # 데이터를 가져올 날짜 설정(1년)
    end_date = dt_now.date()
    start_date = end_date + relativedelta(years=-1)
    print(end_date)
    print(start_date)

    # samsung = data.get_data_yahoo("005930.ks", start_date, end_date)
    print('차트 시작 위치')
    # 관심종목 리스트중 첫번째
    # like1 = data.get_data_yahoo()
    # 관심종목 리스트중 첫번째
    like1 = data.get_data_yahoo(likeList[0][0] + ".ks", start_date, end_date)
    print('데이터 겟')
    qf = cf.QuantFig(like1, title=likeList[0][1], legend='top', name=likeList[0][1])
    qf.add_cci()
    qf.add_adx()
    qf.add_dmi()
    qf.iplot()

    print('0번위치')
    data1 = qf.iplot(asFigure=True, dimensions=(850, 550))
    # data1 = data1.to_json()  # 차트를 json 데이터로
    dd = json.loads(data1.to_json())
    print('1번위치')
    json_callback = request.GET.get("callback")
    print('2번위치')
    if json_callback:
        print('3번위치')
        # callback(jsonData)응답 객체를 임의로 만들어 준다 . ********
        response = HttpResponse(
            "%s(%s);" % (json_callback, json.dumps(dd, ensure_ascii=False)))  # json.dump --> json으로 만든다 (파싱한다)
        # response MIME TYPE
        response["Content-Type"] = "text/javascript; charset=utf-8"
        print("JsonP")
        print(response.getvalue())
    else:
        print('4번위치')
        response = JsonResponse(dd, json_dumps_params={'ensure_ascii': False}, safe=False)
        print("Json")
        print(response.getvalue())

    return response


# ------------------------------------- 허태준, 김나영

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
# Create your views here.
from django.views.decorators.csrf import csrf_exempt




########## Final #####


### CompanyDetail에 종목 별 차트 띄우기 ###
class show_chart:

    def __init__(self):
        stock_code = \
        pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0, index_col=1)[0]
        self.stock_code = stock_code[['회사명']]
        self.stock_code.index = stock_code.index.map('{:06d}'.format)

    def input_close(self, code):

        self.now = datetime.now() # 오늘 날짜
        self.start = self.now - relativedelta(years=1) # 오늘날짜 - 1년
        self.start = self.start.strftime('%Y-%m-%d')
        self.name = self.stock_code.loc[code]['회사명']
        return self.chart_json(code, self.start)

    def chart_json(self, code, start):

        df = fdr.DataReader(code, start)
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

@csrf_exempt
def make_chart(request):
    code = request.GET['code'] # 스프링에서 넘어온 코드
    chart = show_chart()
    fig = chart.input_close(code)
    fig_json = json.loads(fig)
    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


########### TreeMap #############
def query_OracleSQL(sql):
    db = oracleDB
    try:
        conn = ora.connect(db)
        cursor = conn.cursor()
        res = pd.read_sql(sql, conn)
    finally:
        cursor.close()
        conn.close()
    return res

# 거래량 상위종목 목록 받아오기
def get_stock_names():
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

def get_dict_data():
    stock_list = get_stock_names()
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
def make_dataframe():
    dict_data = get_dict_data()
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


def make_treeMap(request):
    # make_dataframe() # <===== 얘를 1시간 마다??
    now = datetime.now()
    title = now.strftime("%Y-%m-%d %H시 기준")
    print(sorted(os.listdir('stock/static/treemap'))[-1])
    try:
        df_tm = pd.read_csv('stock/static/treemap/{} 트리맵.csv'.format(title),index_col=0) # 파일 없을때 예외처리 필요
    except:
        # hour_ago = datetime.now() - relativedelta(hours=1) # 현재 시간 파일이 없으면 1시간 전 파일
        # title = hour_ago.strftime("%Y-%m-%d %H시 기준")     # 을 하려 했는데 얘까지 없으면 어짜누
        title = sorted(os.listdir('stock/static/treemap'))[-1][:-8]   # treemap 폴더에 제일 최신값 가져옴 (없으면??)
        df_tm = pd.read_csv('stock/static/treemap/{} 트리맵.csv'.format(title), index_col=0)
        t = threading.Thread(target=make_dataframe)
        t.start()
        pass

    labels = ['(?)', '-8% 이하', '-6 ~ -8%', '-4 ~ -6%', '-2 ~ -4%', '0 ~ -2%', '0 ~ 2%', '2 ~ 4%', '4 ~ 6%', '6 ~ 8%',
              '8% 이상']
    col = ['#00FF00', '#00CC00', '#009900', '#006600', '#135213', '#440000', '#660000', '#960000', '#CC0000', '#FF0000',
           '#303030']
    col.reverse()
    cmap = dict(zip(labels, col))

    opt = request.GET['opt']
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
    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response



#############################  NY ####

# todo : 오라클에서 데이터 받아와서 json 으로 보낸 후 시각화
# todo : 관심종목의 '카테고리' 비중

def load_stock_data (request) :
    m_id = request.GET['m_id']
    conn = ora.connect(oracleDB)
    cursor = conn.cursor()
    print('연결됐니? cursor : ', cursor)

    column = ["category" , "count"]
    sql_select ='select c.c_category, count (c.c_category) from stock_like sl, company c ' \
                'where c.c_code = sl.slike_code and sl.m_id=:m_id group by c.c_category'
    cursor.execute(sql_select, m_id=m_id)
    like_list =  [e for e in cursor.fetchall() if e[0] != '없음']
    print(like_list)
    conn.close()

    df = pd.DataFrame(like_list, columns=column)
    fig = pt.pie(df, values=df['count'], names=df['category'], title='이런 산업에 관심이 많으시군요!'
                 , width=500)
    # fig.show()
    fig_json = json.loads(fig.to_json())
    json_callback = request.GET.get('callback')

    if json_callback:
        response = HttpResponse('%s(%s);' % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response['Content-Type'] = "text/javascript; charset=utf-8"

    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


# JsonP 방식을 사용
def load_stock_data2 (request) :
    m_id = request.GET['m_id']
    conn = ora.connect(oracleDB)
    cursor = conn.cursor()
    print('연결됐니? cursor : ', cursor)

    column = ["category", "count"]
    sql_select = 'select c.c_category, count (c.c_category) from stock_like sl, company c ' \
                 'where c.c_code = sl.slike_code and sl.m_id=:m_id group by c.c_category'
    cursor.execute(sql_select, m_id=m_id)
    like_list =  [e for e in cursor.fetchall() if e[0] != '없음']
    conn.close()
    print (like_list)
    json_callback = request.GET.get('callback')

    if json_callback :
        response = HttpResponse('%s(%s);'%(json_callback, json.dumps(like_list, ensure_ascii=False)))
        response['Content-Type'] = "text/javascript; charset=utf-8"
        print('JsonP')
        print('response : ', response.getvalue())
    else :
        response = JsonResponse(like_list, json_dumps_params={'ensure_ascii':False} , safe=False)
        print('Json')
        print('response : ', response.getvalue())
    return response


def like_cloud (request) :
    m_id = request.GET['m_id']
    conn = ora.connect(oracleDB)
    cursor = conn.cursor()
    print('연결됐니? cursor : ', cursor)

    column = ["category", "count"]
    sql_select = 'select c.c_category, count (c.c_category) from stock_like sl, company c ' \
                 'where c.c_code = sl.slike_code and sl.m_id=:m_id group by c.c_category'
    cursor.execute(sql_select, m_id=m_id)
    like_list =  [e for e in cursor.fetchall() if e[0] != '없음']
    conn.close()
    print ('like_cloud  : ', like_list)
    json_callback = request.GET.get('callback')
    print(json_callback)

    if json_callback :
        response = HttpResponse('%s(%s);'%(json_callback, json.dumps(like_list, ensure_ascii=False)))
        response['Content-Type'] = "text/javascript; charset=utf-8"
        print('JsonP')
    else :
        response = JsonResponse(like_list, json_dumps_params={'ensure_ascii':False} , safe=False)
        print('Json')
    return response


# ------------------------------------ 위유랑

from modules.flow_corp import *


def make_company_asset_chart(request):
    print(' >>>>>> make_company_asset_chart 진입 >>>>>> ')

    stock_code = request.GET['stock_code']

    corp = Corp_Info()
    corp_code, corp_name = corp.get_corp_code_N_name(stock_code)
    cfs = corp.get_fs_from_corp_code(corp_code, cfs_or_ofs='CFS')
    x_index = corp.get_report_index_from_fs(cfs)
    부채총계 = corp.get_data_from_fs(cfs, keyword='부채총계', bs_is='재무상태표')
    자본총계 = corp.get_data_from_fs(cfs, keyword='자본총계', bs_is='재무상태표')

    fig_json = corp.get_capital_debt_chart(자본총계, 부채총계, x_index, corp_name)
    fig_json = json.loads(fig_json)

    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


def make_sales_profit_chart(request):
    print(' >>>>>> make_sales_profit_chart 진입 >>>>>> ')
    opt = request.GET['opt']

    corp = Corp_Info()
    fig_json = corp.get_bubble_chart(by=opt)
    fig_json = json.loads(fig_json)

    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response



