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
    print('>>>> getQuantChart 진입 >>>>')
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

    print('차트 시작 위치')
    print(likeList)
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

from modules import flow_predict_close
from modules import flow_predict_close_month

def load_stock_data (request) :
    print(' >>>> load_stock_data 진입 >>>> ')
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


# 종가 예측 모듈 적용
def predict_close (request) :
    c_code = request.GET['c_code']
    close = round(flow_predict_close.predict_close(c_code).get_close()[0])
    month_close = round(flow_predict_close_month.predict_close(c_code).get_close()[0])

    print (c_code , "close prediction  : ", close)
    print(c_code, "close prediction (month)  : ", month_close)

    json_callback = request.GET.get('callback')
    print(json_callback)

    if json_callback :
        response = HttpResponse('%s(%s);'%(json_callback, json.dumps([close, month_close], ensure_ascii=False)))
        response['Content-Type'] = "text/javascript; charset=utf-8"
        print('JsonP')
    else :
        response = JsonResponse([close, month_close], json_dumps_params={'ensure_ascii':False} , safe=False)
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


def get_company_figure(request):
    print(' >>>>>> get_company_figure 진입 >>>>>> ')
    stock_code = request.GET['stock_code']

    corp = Corp_Info()
    corp_code, corp_name = corp.get_corp_code_N_name(stock_code)
    cfs = corp.get_fs_from_corp_code(corp_code, cfs_or_ofs='CFS')
    부채총계 = corp.get_data_from_fs(cfs, keyword='부채총계', bs_is='재무상태표')[0]
    자본총계 = corp.get_data_from_fs(cfs, keyword='자본총계', bs_is='재무상태표')[0]
    유동부채 = corp.get_data_from_fs(cfs, keyword='유동부채', bs_is='재무상태표')[0]
    유동자산 = corp.get_data_from_fs(cfs, keyword='유동자산', bs_is='재무상태표')[0]
    당기순이익 = corp.get_data_from_fs(cfs, keyword='당기순이익', bs_is='손익계산서')[0]
    매출액 = corp.get_data_from_fs(cfs, keyword='매출액', bs_is='손익계산서')[0]

    aa = Asset_Accounter()
    chart1 = aa.get_status_plot(['유동자산', '유동부채'], [유동자산, 유동부채], opt='유동성 비율')
    chart2 = aa.get_status_plot(['부채총계', '자본총계'], [부채총계, 자본총계], opt='안정성 비율')
    chart3 = aa.get_status_plot(['당기순이익', '매출액'], [당기순이익, 매출액], opt='수익성 비율')

    res = {'figures':{'매출액':str(매출액), '당기순이익':str(당기순이익), '자본총계':str(자본총계), '부채총계':str(부채총계)}, 'chart1':json.loads(chart1), 'chart2':json.loads(chart2), 'chart3':json.loads(chart3)}

    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(res, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(res, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


# ------------------------------------ 정주은

from modules.flow_index import *

# JE
def makeCountryStockIndex(request):
    contryIndex = ['^KS11', '^KQ11', '^DJI', '^IXIC']
    stockIndex = []

    for e in contryIndex:
        index = bringCountryStockIndex(e)
        stockIndex.append(index)

    fig = make_subplots(rows=2, cols=2, subplot_titles=("코스피", "코스닥", "다우", "나스닥"))
    fig.add_trace(go.Line(x=stockIndex[0]['날짜'], y=stockIndex[0]['주가'], name='코스피'),
                  row=1, col=1)
    fig.add_trace(go.Line(x=stockIndex[1]['날짜'], y=stockIndex[1]['주가'], name='코스닥'),
                  row=1, col=2)
    fig.add_trace(go.Line(x=stockIndex[2]['날짜'], y=stockIndex[2]['주가'], name='다우'),
                  row=2, col=1)
    fig.add_trace(go.Line(x=stockIndex[3]['날짜'], y=stockIndex[3]['주가'], name='나스닥'),
                  row=2, col=2)
    fig.update_layout(title_text="주요 주가 지수")

    fig_json = json.loads(fig.to_json())

    json_callback = request.GET.get("callback")
    if json_callback:
        print("성공!")
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        print("실패!")
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)

    return response


#################### 효율적 포트폴리오

from pykrx import stock
from datetime import datetime, timedelta

def load_portfolio_data(m_id):
    print(' >>>> load_stock_data 진입 >>>>')
    conn = ora.connect(oracleDB)
    cursor = conn.cursor()
    column = ["code", "stocks", "count"]
    sql_select = "SELECT C.C_CODE, C.C_NAME, SM.SM_QTY FROM STOCK_MINE SM, COMPANY C WHERE C.C_CODE = SM.SM_CODE AND M_ID =:m_id"
    cursor.execute(sql_select, m_id=m_id)
    myStocks = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(myStocks, columns=column)
    dfcount = df['count'].sum()
    e = (df['count'].values / dfcount)
    df['perc'] = e
    return df

def mystock(m_id):
    mystock = load_portfolio_data(m_id)
    stocks = mystock['code']
    todayv = datetime.today().strftime("%Y%m%d")
    yearago = (datetime.today() - timedelta(1095)).strftime("%Y%m%d")
    # 내가 보유한 종목의 주가
    myStockValue = []
    for e in stocks:
        df1 = stock.get_market_ohlcv_by_date(yearago, todayv, e)
        # 컬럼명 종가에서 회사명으로 수정
        df1.rename(columns={'종가': e}, inplace=True)
        # 회사의 주가 데이터 추출
        bb = df1[e]
        myStockValue.append(bb)

    myStock = pd.DataFrame(myStockValue)
    dfv = myStock.T
    dfv = dfv.dropna()
    return dfv

def calmyPortfolio(m_id):
    # m_id = request.GET['m_id']
    dfv = mystock(m_id)
    # 일간변동률 pct_change()
    daily_ret = dfv.pct_change()
    # 연간수익률
    annual_ret = daily_ret.mean() * 252
    # 일간 리스크 (일간 공분산) cov()
    daily_cov = daily_ret.cov()
    # 연간 리스크 (연간 공분산)
    annual_cov = daily_cov * 252
    # 포트폴리오 수익률
    port_ret = []
    # 포트폴리오 리스크
    port_risk = []
    # 포트폴리오 비중
    port_weights = []
    # 샤프 지수
    sharpe_ratio = []
    # 내 보유 주식
    stocks = load_portfolio_data(m_id)['stocks']

    for _ in range(20000):  # 20000개의 임의의 포트폴리오 작성
        weights = np.random.random(len(stocks))  # 종목숫자별로 임의의 랜덤 숫자를 구성
        weights /= np.sum(weights)  # 종목 비중의 합이 1이 되도록 조정
        # 랜덤하게 생성한 종목별 비중 배열과 종목별 연간 수익률을 곱해 해당 포트폴리오 전체 수익률을 구함
        returns = np.dot(weights, annual_ret)
        # 해당 포트폴리오 전체 리스크(Risk)를 구함
        risk = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights)))
        # 포트폴리오 20,000개의 수익률, 리스크, 종목별 비중을 각각 리스트에 추가
        port_ret.append(returns)
        port_risk.append(risk)
        port_weights.append(weights)
        sharpe_ratio.append(returns / risk)  # 샤프지수 추가

    # 포트폴리오 딕셔너리에 비중값 추가
    portfolio = {'Returns': port_ret, 'Risk': port_risk, 'Sharpe': sharpe_ratio}

    # 내 포트폴리오 ##########Start
    myWeight = load_portfolio_data(m_id)
    myWeights = myWeight['perc']  # 현재 내 포트폴리오의 비중
    myWeights = myWeights.values
    myPort_ret = np.dot(myWeights, annual_ret)
    myPort_risk = np.sqrt(np.dot(myWeights.T, np.dot(annual_cov, myWeights)))

    for i, s in enumerate(stocks):
        portfolio[s] = [weight[i] for weight in port_weights]
    df = pd.DataFrame(portfolio)
    df = df[['Returns', 'Risk', 'Sharpe'] + [s for s in stocks]]

    ## 샤프지수 최대값, 리스크 최소값 출력
    max_sharpe = df.loc[df['Sharpe'] == df['Sharpe'].max()]
    min_risk = df.loc[df['Risk'] == df['Risk'].min()]

    ###################### 차트
    main = go.Scatter(x=df['Risk'], y=df['Returns'],  # y축 값 sepal_length 값에 따라 배치
                      mode='markers',  # Scatter Plot을 그리기 위해 Markers
                      marker=dict(  # Marker에 대한 세부적은 설정을 지정
                          size=5,  # 점 크기
                          color=df['Sharpe'],  # 색깔 값을 petal_length에 따라 변하도록 설정
                          colorscale='Viridis',  # one of plotly colorscales
                          showscale=True,  # colorscales 보여줌
                          line_width=1,  # 마커 라인 두께 설정
                      ))
    maxSharpe = go.Scatter(x=max_sharpe['Risk'], y=max_sharpe['Returns'],
                           mode='markers', marker=dict(size=10, color='#ff0000', line_width=1))
    # x = min_risk['Risk'], y = min_risk['Returns']
    min_risk = go.Scatter(x=min_risk['Risk'], y=min_risk['Returns'],
                          mode='markers', marker=dict(size=10, color='#0300ff', line_width=1))
    myPortfolio = go.Scatter(x=[myPort_risk], y=[myPort_ret],
                             mode='markers',  marker=dict(size=10, color='#0300ff', line_width=1))

    fig = go.Figure(data=[main, maxSharpe, min_risk, myPortfolio])
    fig.update_layout(title='효율적 투자선', xaxis_title='Risk', yaxis_title='Return')

    springChk = []
    springChk.append((myPort_ret * 100).astype('int') )
    springChk.append((np.squeeze(max_sharpe['Returns'].values) * 100).astype('int'))
    print(np.squeeze(max_sharpe['Returns'].values))

    delmax_sharpe = max_sharpe
    del delmax_sharpe['Returns']
    del delmax_sharpe['Risk']
    del delmax_sharpe['Sharpe']
    springChk.append(delmax_sharpe)
    springChk.append(fig)

    return springChk

def myPortfolioChart(request):

    m_id = request.GET['m_id']
    print("주식 추천 비중")
    springChk = calmyPortfolio(m_id)
    df = springChk[2]
    fig = pt.pie(df, names=df.columns, values=np.squeeze(df.values), height=700, width=700)
    fig.update_traces(hole=.6, hoverinfo="label+percent+name")

    fig_json = json.loads(fig.to_json())
    json_callback = request.GET.get("callback")
    if json_callback:
        print("성공!")
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps([fig_json,str(springChk[0]),str(springChk[1])], ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        print("실패!")
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)

    return response


def effPortfolio(request):
    m_id = request.GET['m_id']
    springChk = calmyPortfolio(m_id)
    fig = springChk[3]

    fig_json = json.loads(fig.to_json())
    json_callback = request.GET.get('callback')

    if json_callback:
        response = HttpResponse('%s(%s);' % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response['Content-Type'] = "text/javascript; charset=utf-8"

    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


