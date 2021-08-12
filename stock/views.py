# ------------------------------------- 장우석

import datetime
from modules import database as db


oracleDB = db.oracleDB

# Create your views here.
import chart_studio
chart_studio.tools.set_credentials_file(username='osjang1996', api_key='Bf1UtHInSojLKXJyUKfc')
from stock import models
import cufflinks as cf
cf.go_offline(connected=True)
import plotly.express as pt

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

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import os
import pandas as pd
import cx_Oracle as ora
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta
import cufflinks as cf
import threading
# Create your views here.


# ########## Final #####
# ### CompanyDetail에 종목 별 차트 띄우기 ###

from modules.flow_stock_chart import Company_Chart
def make_chart(request):
    code = request.GET['code'] # 스프링에서 넘어온 코드
    fig = Company_Chart().chart_json(code)
    fig_json = json.loads(fig)
    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


# ########### TreeMap #############
from modules.flow_stock_chart import TreeMap
def make_treeMap(request):
    opt = request.GET['opt']
    fig_json = TreeMap().treeMap_json(opt)
    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response

####### 유사 종목 #######
from modules.flow_stock_model import Stock_Clustering
def similar(request):
    code = request.GET['code']
    res_df = Stock_Clustering().search(code)
    print(res_df)
    sample = res_df.sample(3 if len(res_df) >=3 else len(res_df))['C_NAME']  # 추천을 해야하지만 일단 랜덤으로..
    res = {k: v for k, v in sample.items()}  # 요렇게 전달하면 될듯

    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(res, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(res, json_dumps_params={'ensure_ascii': False}, safe=False)
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

import requests
import json
import plotly.graph_objects as go
import plotly.express as px

def str_to_int_processor(x):
    try:
        return int(x)
    except:
        return 0


def make_company_asset_chart(request):
    print(' >>>>>> make_company_asset_chart 진입 >>>>>> ')
    stock_code = request.GET['stock_code']
    print('stock_code ::::' , stock_code)
    # print('type(stock_code) ::::', type(stock_code))
    company_codes = pd.read_csv('stock/static/financial_statements/company_codes.csv', index_col=0)
    # print(company_codes)

    is_searched_company = company_codes['stock_code'] == stock_code
    res = company_codes[is_searched_company]
    corp_name = res.values[0][1]
    corp_code = res.values[0][0]
    corp_code = str(corp_code).zfill(8)

    url = 'https://opendart.fss.or.kr/api/fnlttMultiAcnt.json'
    params = {'crtfc_key': 'ead0486e8d1b91cc5f958b102a18a288943e97d5',
              'corp_code': corp_code, 'bsns_year': '2020', 'reprt_code': '11011'}
    res = requests.get(url, params)

    company_fs = pd.DataFrame(json.loads(res.text).get('list'))
    # print(company_fs)

    report_index = company_fs[['thstrm_nm', 'frmtrm_nm', 'bfefrmtrm_nm']].iloc[1]
    report_index = report_index.to_list()

    company_fs['thstrm_amount'] = company_fs['thstrm_amount'].str.replace('-|,', '').apply(str_to_int_processor)
    company_fs['frmtrm_amount'] = company_fs['frmtrm_amount'].str.replace('-|,', '').apply(str_to_int_processor)
    company_fs['bfefrmtrm_amount'] = company_fs['bfefrmtrm_amount'].str.replace('-|,', '').apply(str_to_int_processor)

    refined_company_fs = company_fs[['sj_nm', 'account_nm',
                                     'thstrm_nm', 'thstrm_dt', 'thstrm_amount',
                                     'frmtrm_nm', 'frmtrm_dt', 'frmtrm_amount',
                                     'bfefrmtrm_nm', 'bfefrmtrm_dt', 'bfefrmtrm_amount'
                                     ]]

    company_bs = company_fs.groupby('sj_nm').get_group('재무상태표')

    is_asset_sum = company_bs['account_nm'] == '자산총계'
    res = company_bs[is_asset_sum].iloc[0, :]
    asset_sum = [res.thstrm_amount, res.frmtrm_amount, res.bfefrmtrm_amount]

    is_debt_sum = company_bs['account_nm'] == '부채총계'
    res = company_bs[is_debt_sum].iloc[0, :]
    debt_sum = [res.thstrm_amount, res.frmtrm_amount, res.bfefrmtrm_amount]

    is_capital_sum = company_bs['account_nm'] == '자본총계'
    res = company_bs[is_capital_sum].iloc[0, :]
    capital_sum = [res.thstrm_amount, res.frmtrm_amount, res.bfefrmtrm_amount]

    x = report_index
    fig = go.Figure(go.Bar(x=x, y=capital_sum, name='자본'))
    fig.add_trace(go.Bar(x=x, y=debt_sum, name='부채'))

    fig.update_layout(
        title="{} 자산 추이표".format(corp_name),
        barmode='stack',
        yaxis_title="단위(원)",
        yaxis_tickformat=',',
    )

    # fig.show()

    fig_json = json.loads(fig.to_json())

    # print(fig.to_json())
    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


# 코스피 거래량 상위종목 목록 받아오기
def get_kospi_stock_names():
    url = 'https://finance.naver.com/sise/sise_quant.nhn?sosok=0'
    header = {'User-Agent': 'Mozilla/5.0'}
    stock_names = []
    res = requests.get(url, headers=header)
    soup = BeautifulSoup(res.text, 'html.parser')
    stocks = soup.find("table", attrs={"class": "type_2"}).find_all("tr")
    for stock in stocks:
        if len(stock.find_all("td")) > 1:
            data = stock.find_all("td")[1].text
            stock_names.append(data)
    return stock_names


# 코스닥 거래량 상위종목 목록 받아오기
def get_kosdaq_stock_names():
    url = 'https://finance.naver.com/sise/sise_quant.nhn?sosok=1'
    header = {'User-Agent': 'Mozilla/5.0'}
    stock_names = []
    res = requests.get(url, headers=header)
    soup = BeautifulSoup(res.text, 'html.parser')
    stocks = soup.find("table", attrs={"class": "type_2"}).find_all("tr")
    for stock in stocks:
        if len(stock.find_all("td")) > 1:
            data = stock.find_all("td")[1].text
            stock_names.append(data)
    return stock_names


# 코스피, 코스닥 거래량 상위종목 기업코드 및 이름 가져오기
def get_corp_codes_N_names(stock_names):
    company_codes = pd.read_csv('stock/static/financial_statements/company_codes.csv', index_col=0)
    is_searched_company = company_codes['corp_name'].isin(stock_names)
    company_codes = company_codes[is_searched_company]
    company_codes['corp_code'] = company_codes['corp_code'].astype('str')
    cond = company_codes['stock_code'] == ' '
    company_codes = company_codes[~cond]
    company_codes['corp_code'] = company_codes['corp_code'].str.zfill(8)
    corp_codes_N_names = company_codes[['corp_code', 'corp_name']].values.tolist()
    return corp_codes_N_names


def make_sales_profit_list(df_pool, corp_codes_N_names, market):
    url = 'https://opendart.fss.or.kr/api/fnlttMultiAcnt.json'
    for code, name in corp_codes_N_names:
        params = {'crtfc_key':'ead0486e8d1b91cc5f958b102a18a288943e97d5',
              'corp_code':code, 'bsns_year':'2020', 'reprt_code':'11011'}
        res = requests.get(url,params)
        data = json.loads(res.text).get('list')
        try:
            sales = int(data[22].get('thstrm_amount').replace(',',''))
            profit = int(data[24].get('thstrm_amount').replace(',',''))
            df_pool.append([name, sales, profit, market])
        except:
            pass
    return df_pool


def put_min_max_scaler_on_sales_N_profit(bubble_df):
    max_p = bubble_df.profit.max()
    min_p = bubble_df.profit.min()
    max_s = bubble_df.sales.max()
    min_s = bubble_df.sales.min()
    bubble_df['min_max_profit'] = bubble_df.profit.apply(lambda x : (x - min_p) / (max_p - min_p))
    bubble_df['min_max_sales'] = bubble_df.sales.apply(lambda x : (x - min_s) / (max_s - min_s))
    return bubble_df

def make_bubble_chart_dataframe():
    kospi_corp_codes_N_names = get_corp_codes_N_names(get_kospi_stock_names())
    kosdaq_corp_codes_N_names = get_corp_codes_N_names(get_kosdaq_stock_names())

    df_pool = []
    df_pool = make_sales_profit_list(df_pool, kospi_corp_codes_N_names, 'KOSPI')
    df_pool = make_sales_profit_list(df_pool, kosdaq_corp_codes_N_names, 'KOSDAQ')

    bubble_df = pd.DataFrame(df_pool, columns=['name', 'sales', 'profit', 'market'])

    bubble_df.to_csv('stock/static/financial_statements/sales_profit/'+datetime.now().strftime("%Y-%m-%d 기준 버블차트.csv"))
    print(datetime.now().strftime("%Y-%m-%d 기준 버블차트.csv"))


def make_sales_profit_chart(request):
    print(' >>>>>> make_sales_profit_chart 진입 >>>>>> ')
    now = datetime.now()
    title = now.strftime("%Y-%m-%d 기준")
    try:
        print('>>> try >>>')
        bubble_df = pd.read_csv('stock/static/financial_statements/sales_profit/{} 버블차트.csv'.format(title), index_col=0)
    except:
        print('>>> except >>>')
        t = threading.Thread(target=make_bubble_chart_dataframe)
        t.start()
        title = sorted(os.listdir('stock/static/financial_statements/sales_profit'))[-1][:-8]
        bubble_df = pd.read_csv('stock/static//financial_statements/sales_profit/{} 버블차트.csv'.format(title), index_col=0)

    opt = request.GET['opt']
    print('opt ::::', opt)

    bubble_df = put_min_max_scaler_on_sales_N_profit(bubble_df)

    fig = px.scatter(bubble_df, x="sales", y="profit",
                     size="min_max_"+opt, color="market",
                     hover_name="name", log_x=True, size_max=60, title=title)
    # fig.show()
    fig_json = json.loads(fig.to_json())

    # print(fig.to_json())
    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response



