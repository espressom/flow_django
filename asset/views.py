from modules import database as db

oracleDB = db.oracleDB

# 차트
# 리눅스에서 한글 설정
import warnings as wr
import matplotlib as mpl
import matplotlib.pyplot as plt
# 유니코드 깨짐현상 해결
mpl.rcParams['axes.unicode_minus'] = False
# 나눔고딕 폰트 적용
plt.rcParams["font.family"] = 'NanumGothic'
wr.filterwarnings('ignore')
import cx_Oracle as ora
import plotly.express as pt
from modules import bank_connect as bankconn
from modules import asset_chart as achart

# 월 카테고리 차트 만들기
def category_chart(request):
    print(' >>> category_chart 진입 >>>')
    m_id = request.GET['m_id']
    fig = achart.asset_chart.category_cash(m_id)
    fig_json = json.loads(fig.to_json())
    json_callback = request.GET.get('callback')

    if json_callback:
        response = HttpResponse('%s(%s);' % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response['Content-Type'] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response

# 월 유입유출 차트 만들기...0803
def month_cash_chart(request):
    print(' >>> month_cash_chart 진입 >>>')
    m_id = request.GET['m_id']
    fig = achart.asset_chart.month_cash(m_id)
    fig_json = json.loads(fig.to_json())
    json_callback = request.GET.get('callback')

    if json_callback:
        response = HttpResponse('%s(%s);' % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response['Content-Type'] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


def addcashflow(request):
    print(' >>> addcashflow 진입 >>>')
    bank = request.GET['bank']
    m_id = request.GET['m_id']
    print(bank)
    print(m_id)
    if bank:
        bankconn.bank_connect.incashUpasset(bank, m_id)
        msg = "성공"
    else:
        msg = "실패"

    response = JsonResponse(msg, json_dumps_params={'ensure_ascii': False}, safe=False)
    # return msg
    return response

# ------------------------------------- 정주은
import json
from django.http import HttpResponse, JsonResponse
import requests
import xmltodict
import datetime
from datetime import datetime
import pandas as pd
import plotly.express as px

# 한국은행 API 키
API_KEY = "Y9IPT4EI62PC2SLTLQI8"

# 오늘 날짜 가져오는 함수
def today():
    todayv = datetime.now().date()
    todayv = todayv.strftime("%Y%m%d")
    return todayv

# data 자료 갯수 구하기
def cntData():
    url = "http://ecos.bok.or.kr/api/StatisticItemList/"+API_KEY+"/xml/kr/1/1/098Y001/"
    data_cnt = requests.get(url)
    data_cnt = data_cnt.text
    bok = xmltodict.parse(data_cnt)
    r = bok['StatisticItemList']['row']['DATA_CNT']
    return r


# 일별 기준금리 가져와서 데이터 프레임화
def dayBaseRate():
    todayv = today()
    r1 = cntData()
    url = "http://ecos.bok.or.kr/api/StatisticSearch/" + API_KEY + "/xml/kr/1/" + r1 + "/098Y001/MM/19940103/" + todayv + "/0101000/"
    dict_data = requests.get(url)
    rate = dict_data.text
    bok = xmltodict.parse(rate)
    r2 = bok['StatisticSearch']['row']
    data = []
    for e in r2:
        data.append([e['TIME'], e['DATA_VALUE']])

    df_column = ['기준년월', '기준금리']
    df = pd.DataFrame(data, columns=df_column)

    ## 기준년월을 object -> datetime 으로 변경
    df['기준년월'] = df['기준년월'].apply(lambda _: datetime.strptime(_, '%Y%m'))

    ## 기준금리를 object -> float 형으로 변경
    df['기준금리'] = df['기준금리'].astype('float')
    return df

def baseRate_jsonp(request):
    df = dayBaseRate()
    # print(df)
    fig = px.line(df, y='기준금리', x='기준년월', title="기준금리 추이")
    fig_json = json.loads(fig.to_json())
    json_callback = request.GET.get("callback")
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


# ------------------------------------- 하태근

##카테고리별 지출 분포 차트###########################################
def load_category_data (request) :
    m_id = request.GET['m_id']
    conn = ora.connect(oracleDB)
    cursor = conn.cursor()
    c_flow = '유출'
    column = ["category", "count"]
    sql_select = 'select c_category, count(c_category) from cashflow  ' \
                 'where m_id = :m_id and c_flow= :c_flow group by c_category'
    cursor.execute(sql_select, m_id=m_id, c_flow=c_flow)
    category_count = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(category_count, columns=column)
    fig = pt.pie(df, values=df['count'], names=df['category'],
                 title='카테고리별 지출 분포 차트'
                 , width=500)
    fig_json = json.loads(fig.to_json())
    json_callback = request.GET.get('callback')
    if json_callback:
        response = HttpResponse('%s(%s);' % (json_callback,
                                             json.dumps(fig_json,
                                            ensure_ascii=False)))
        response['Content-Type'] = "text/javascript; charset=utf-8"
    else:
        print("실패!")
        response = "실패"
    return response
########################################################################
