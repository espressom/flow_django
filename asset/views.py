from modules import database as db

oracleDB = db.oracleDB

# 차트
# 리눅스에서 한글 설정
import warnings as wr
#[f.name for f in matplotlib.font_manager.fontManager.ttflist if 'Nanum' in f.name]
import matplotlib as mpl
import matplotlib.pyplot as plt
# 유니코드 깨짐현상 해결
mpl.rcParams['axes.unicode_minus'] = False
# 나눔고딕 폰트 적용
plt.rcParams["font.family"] = 'NanumGothic'
wr.filterwarnings('ignore')
import cx_Oracle as ora
import plotly.express as pt

# 차트 만들기...0803
def month_cash_chart(request):
    m_id = request.GET['m_id']
    print(m_id)
    db = oracleDB
    conn = ora.connect(db)
    cursor = conn.cursor()
    # 유출
    sql_out = "select to_char(c_date,'mm') x1, sum(c_price) y1 from cashflow where m_id='" + m_id + "' and c_flow='유출' group by to_char(c_date,'mm') order by x1 asc"
    cursor.execute(sql_out)
    cash_out = cursor.fetchall()
    x1 = [cash_out[i][0] for i in (0, len(cash_out) - 1)]
    y1 = [cash_out[i][1] for i in (0, len(cash_out) - 1)]
    # 유입
    sql_in = "select to_char(c_date,'mm') x2, sum(c_price) y2 from cashflow where m_id='" + m_id + "' and c_flow='유입' group by to_char(c_date,'mm') order by x2 asc"
    cursor.execute(sql_in)
    cash_in = cursor.fetchall()
    x2 = [cash_in[i][0] for i in (0, len(cash_in) - 1)]
    y2 = [cash_in[i][1] for i in (0, len(cash_in) - 1)]
    # 연결닫기
    conn.commit()
    cursor.close()
    conn.close()
    # 그래프
    df = pd.DataFrame({"월": x1,"지출": y1,"유입": y2})
    fig = pt.line(df,x="월",y=["지출","유입"],title="월별 지출,유입")

    fig_json = json.loads(fig.to_json())
    json_callback = request.GET.get('callback')

    if json_callback:
        response = HttpResponse('%s(%s);' % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response['Content-Type'] = "text/javascript; charset=utf-8"

    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


# 은행 연동 0802
def loadbank(bank,m_id):
    path = 'asset/static/{}_{}.xls'.format(bank,m_id)
    print("path ::: ",path)
    df= pd.read_excel(path, header=6)
    new_df = df.loc[:100, :]
    # 기타소득
    기타소득 = ['신한할인캐쉬백']
    # 이전소득
    이전소득 = ['훈련비고용부', '노동부인천북부']
    # 식비
    식비지출 = ['씨유가산디지털', '노브랜드버거', '(주)우아한형제', '이디야커피', '이마트24 가산', '김밥중독', '미니스톱 가산', '써브웨이 가산', '메이플치킨 앤', '502커피 (가산',
            '신림큐슈라멘&', '오누이 떡볶이', '송은택 스시&참', '팔람까오', '땅땅치킨', '주)스타벅스커', '배떡구디점', '자연산활어횟집', '주식회사 씨유']
    # 여가비
    여가비지출 = ['카카오_멜론', '히어로보드게임', '한강더드림자전']
    # 기타 --> 처리
    기타지출 = ['카카오페이', '네이버페이결제', '인천이음카드\u3000', '다이소(부평시']
    # 주거비
    # 주거지출 = ['오피스텔관리비']
    # 차비
    차비지출 = ['신한체크교통']
    # 품위유지비
    품위유지지출 = ['씨제이올리브네']
    # 부채유입
    부채유입 = ['IBK기업']
    new_df['카테고리'] = 0
    for i in range(0, len(new_df)):
        if new_df.loc[i, '내용'] in 기타소득:
            new_df.loc[i, '카테고리'] = '기타소득'
        elif new_df.loc[i, '내용'] in 이전소득:
            new_df.loc[i, '카테고리'] = '이전소득'
        elif new_df.loc[i, '내용'] in 식비지출:
            new_df.loc[i, '카테고리'] = '식비지출'
        elif new_df.loc[i, '내용'] in 여가비지출:
            new_df.loc[i, '카테고리'] = '여가비지출'
        elif new_df.loc[i, '내용'] in 기타지출:
            new_df.loc[i, '카테고리'] = '기타지출'
        elif new_df.loc[i, '내용'] in 품위유지지출:
            new_df.loc[i, '카테고리'] = '품위유지지출'
        elif new_df.loc[i, '내용'] in 부채유입:
            new_df.loc[i, '카테고리'] = '부채유입'
        else:
            new_df.loc[i, '카테고리'] = '미분류'

            # FLOW 컬럼 추가 => 유입 유출 판단
    new_df['FLOW'] = np.where(new_df['출금(원)'] != 0, "유출", "유입")
    # C_PRICE 컬럼추가
    new_df['C_PRICE'] = np.where(new_df['출금(원)'] != 0, new_df['출금(원)'], new_df['입금(원)'])
    # 거래일자 2021/07/25 형태로
    date_list = [new_df.iloc[i]['거래일자'].replace('-', '/') for i in range(len(new_df['거래일자']))]
    new_df['거래일자'] = np.array(date_list)
    new_df['거래일자'].astype(str)
    new_df['거래일자'] = new_df['거래일자'].str.slice(start=2)
    new_df['거래일자'] = pd.to_datetime(new_df['거래일자'])
    # 펌 뱅킹 : 기업자금관리의 편의성을 제공하는 금융서비스
    펌뱅킹 = ['FB이체', '타행FB', '국세', 'FB자동', 'FB입금']
    계좌이체 = ["타행MB", "타행IB", 'OP이체', '모바일', '모바일', '타행PC']
    체크카드 = ["신한체", '카드결']
    캐쉬백 = ["SHC입"]
    for i in range(0, len(new_df)):
        if new_df.loc[i, '적요'] in 펌뱅킹:
            new_df.loc[i, '적요'] = '펌뱅킹'
        elif new_df.loc[i, '적요'] in 계좌이체:
            new_df.loc[i, '적요'] = '계좌이체'
        elif new_df.loc[i, '적요'] in 체크카드:
            new_df.loc[i, '적요'] = '체크카드'
        elif new_df.loc[i, '적요'] in 캐쉬백:
            new_df.loc[i, '적요'] = '캐쉬백'
        else:
            new_df.loc[i, '적요'] = '미분류'
    cashf_df = new_df[['FLOW', '카테고리', '내용', '적요', 'C_PRICE', '거래일자']]
    cashf_df.columns = ['C_FLOW', 'C_CATEGORY', 'C_CONTENT', 'C_METHOD', 'C_PRICE', 'C_DATE']

    db = oracleDB
    conn = ora.connect(db)
    cursor = conn.cursor()
    column = ['C_FLOW', 'C_CATEGORY', 'C_CONTENT', 'C_METHOD', 'C_PRICE', 'C_DATE']
    columns = ','.join(cashf_df.columns)  # C_FLOW,C_CATEGORY...
    values = ','.join([':{:d}'.format(i + 1) for i in range(len(cashf_df.columns))])

    sql = "INSERT into cashflow (C_NUM,M_ID,{columns:}) VALUES (cashflow_seq.nextVal,'"+m_id+"',{values:})"
    cursor.executemany(sql.format(columns=columns, values=values),cashf_df.values.tolist())
    conn.commit()
    cursor.close()
    conn.close()

def addcashflow(request):
    bank = request.GET['bank']
    m_id = request.GET['m_id']
    print(bank)
    print(m_id)

    if bank:
        print("성공")
        loadbank(bank, m_id)
        msg = "성공"
    else:
        print("실패!")
        msg = "실패"

    return msg


# ------------------------------------- 정주은

import json

from django.http import HttpResponse, JsonResponse

# Create your views here.

import requests
import xmltodict
import datetime
from datetime import datetime

import pandas as pd
import numpy as np

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
