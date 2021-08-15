from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import json
# Create your views here.
from management import models

# 장우석
# 관리자 로그인
def adminLogin(request):
    print('------LoginPage Access--------')
    print('method : ', request.method)
    if 'admin_id' in request.session:
        return redirect('/management')
    if request.method == 'POST':
        admin_id = request.POST['id']
        admin_pwd = request.POST['pwd']
        admin_info = (admin_id, admin_pwd)
        print('info : ', admin_info)
        login_data = models.getAdminNum(admin_info)
        print('login_data : ', login_data)
        if login_data:
            if login_data[0]==0:
                print('Login Success!')
                request.session['admin_id'] = admin_id
                request.session['admin_name'] = login_data[1]
            else:
                print('Login Error!')
                errMsg = "관리자 로그인 실패 : 정보를 다시 확인하세요."
                print(errMsg)
                return render(request, "management/login.html", {'errMsg': errMsg})
        else:
            print('Login Error!')
            errMsg="관리자 로그인 실패 : 정보를 다시 확인하세요."
            print(errMsg)
            return render(request, "management/login.html", {'errMsg': errMsg})
        return redirect('/management/adminLogin')
    return render(request, "management/login.html")

# 관리자 로그아웃
def adminLogout(request):
    del request.session['admin_id']
    del request.session['admin_name']
    return redirect('/management/adminLogin')

# 관리자 페이지 메인
def management_index(request):
    if 'admin_id' not in request.session:
        return redirect('/management/adminLogin')
    mc = models.getMemCount()[0]
    bc = models.getBrdCount()[0]
    tmc = models.getToMemCount()[0]
    tbc = models.getToBrdCount()[0]
    infoList = [mc,bc,tmc,tbc]

    return render(request, 'management/index.html',{"infoList":infoList})

# 종류별 요청 횟수 차트
def reqFig(request):
    print('reqFig Access')
    # 요청 횟수 리스트
    reqList = models.getRequestLog()
    df1 = pd.DataFrame(reqList[:10], columns=['request', 'count'])

    # plotly 차트로 만들기
    reqFig = px.pie(df1, values='count', names='request')
    # reqFig.show()

    #jsonp로 파싱
    fig_json = json.loads(reqFig.to_json())
    json_callback = request.GET.get("callback")
    print(fig_json)
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response


# 일별 요청 횟수 차트
def dateFig(request):
    print('dateFig Access')
    # 일별 요청 리스트
    dateList = models.getDateLog()
    df2 = pd.DataFrame(dateList, columns=['date', 'count'])

    # plotly 차트로 만들기
    dateFig = go.Figure(data=go.Scatter(x=df2['date'], y=df2['count']))
    # dateFig.show()

    # jsonp로 파싱
    fig_json = json.loads(dateFig.to_json())
    json_callback = request.GET.get("callback")
    print(fig_json)
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response

# 회원 연령별 분포 차트
def getMemAgesCountChart(request):
    print('MemAgesCountChart Access')
    # 회원 연령대별 데이터 가져오기
    macList = models.getMemAgesCount()
    # 연령대별(0대~90대) 분포 리스트 만들기
    acList = [['0대'], ['10대'], ['20대'], ['30대'], ['40대'], ['50대'], ['60대'], ['70대'], ['80대'], ['90대']]
    for k in acList:
        for e in macList:
            if k[0][0] == e[0]:
                k.append(e[1])
        if len(k) == 1:
            k.append(0)
    # DataFrame으로 만들기
    df = pd.DataFrame(acList, columns=['ages', 'count'])
    # Plotly BarChart로 만들기
    macFig = px.bar(df, x='ages', y='count')
    # jsonp로 파싱
    fig_json = json.loads(macFig.to_json())
    json_callback = request.GET.get("callback")
    print(fig_json)
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response

# 회원 성별 분포 차트
def getMemGenCountChart(request):
    print('MemAgesCountChart Access')
    # 회원 주민등록번호 뒷자리 첫번째 분포 데이터 가져오기
    memGenCount = models.getMemGenCount()
    # 주민등록번호 뒷자리 첫번째를 남녀 분포로 바꾸기
    genList = [['남'], ['여']]
    mCnt = 0
    wCnt = 0
    for e in memGenCount:
        if e[0] == '1':
            mCnt += e[1]
        elif e[0] == '2':
            wCnt += e[1]
        elif e[0] == '3':
            mCnt += e[1]
        else:
            wCnt += e[1]
    genList[0].append(mCnt)
    genList[1].append(wCnt)
    print(genList)
    # 데이터 프레임으로 바꾸기
    df = pd.DataFrame(genList, columns=['Gender', 'Count'])
    # Plotly PieChart로 바꾸기
    mgcFig = px.pie(df, values='Count', names='Gender')
    # jsonp로 파싱
    fig_json = json.loads(mgcFig.to_json())
    json_callback = request.GET.get("callback")
    print(fig_json)
    if json_callback:
        response = HttpResponse("%s(%s);" % (json_callback, json.dumps(fig_json, ensure_ascii=False)))
        response["Content-Type"] = "text/javascript; charset=utf-8"
    else:
        response = JsonResponse(fig_json, json_dumps_params={'ensure_ascii': False}, safe=False)
    return response

# 회원 정보 통계 관리자 페이지
def management_memberInfo(request):
    if 'admin_id' not in request.session:
        return redirect('/management/adminLogin')
    return render(request, 'management/memberInfo.html')





#------------------------------------------------------


def management_login(request):
    return render(request, 'management/login.html')


def management_404(request):
    return render(request, 'management/404.html')


def management_forgot_password(request):
    return render(request, 'management/forgot_password.html')


def dump_button(request):
    return render(request, 'dump/button.html')


def dump_card(request):
    return render(request, 'dump/card.html')