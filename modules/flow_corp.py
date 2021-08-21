#!/usr/bin/env python
# coding: utf-8

from bs4 import BeautifulSoup
import requests
import json
import requests
import threading
import os
from datetime import datetime, time

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings as wr
import plotly.express as px
import plotly.graph_objects as go

mpl.rcParams['axes.unicode_minus'] = False
wr.filterwarnings('ignore')
plt.style.use(['seaborn'])
plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["font.size"] = 12


class Corp_Info:

    def __init__(self):
        self.codes_title = datetime.now().strftime("%Y-%m-%d company_codes.csv")
        self.codes_path = 'stock/static/financial_statements/company_codes'
        self.bubble_title = datetime.now().strftime("%Y-%m-%d 기준 버블차트.csv")
        self.bubble_path = 'stock/static/financial_statements/bubble'

        try:
            print('>>> try :::: company_codes >>>')
            self.company_codes = pd.read_csv('{}/{}'.format(self.codes_path, self.codes_title), index_col=0)
        except:
            print('>>> except :::: company_codes >>>')
            t = threading.Thread(target=self.make_company_codes_csv)
            t.start()
            try:
                codes_title = sorted(os.listdir(self.codes_path))[-2]
                self.company_codes = pd.read_csv('{}/{}'.format(self.codes_path, codes_title), index_col=0)
            except:
                print(self.codes_path, '에 아무런 파일이 없습니다.')

        try:
            print('>>> try :::: bubble_df >>>')
            self.bubble_df = pd.read_csv('{}/{}'.format(self.bubble_path, self.bubble_title), index_col=0)
        except:
            print('>>> except :::: bubble_df >>>')
            kospi = self.get_kospi_stock_names(0)
            kosdaq = self.get_kospi_stock_names(1)
            kospi_corp = self.get_corp_codes_N_names(kospi)
            kosdaq_corp = self.get_corp_codes_N_names(kosdaq)
            df_pool = self.make_sales_profit_list(kospi_corp) + self.make_sales_profit_list(kosdaq_corp,
                                                                                            market='KOSDAQ')
            t = threading.Thread(target=self.make_bubble_csv, args=[df_pool])
            t.start()
            try:
                bubble_title = sorted(os.listdir(self.bubble_path))[-1]
                self.bubble_df = pd.read_csv('{}/{}'.format(self.bubble_path, bubble_title), index_col=0)
            except:
                print(self.bubble_path, '에 아무런 파일이 없습니다.')

    def get_stock_corp_codes_zip(self):
        print('>>> get_stock_corp_codes_zip 진입 >>>')
        import requests
        from io import BytesIO
        from zipfile import ZipFile
        from xml.etree.ElementTree import parse

        url = 'https://opendart.fss.or.kr/api/corpCode.xml'
        params = {'crtfc_key': 'ead0486e8d1b91cc5f958b102a18a288943e97d5'}
        res = requests.get(url, params)

        with ZipFile(BytesIO(res.content)) as zipfile:
            zipfile.extractall(self.codes_path)

    def get_stock_corp_codes_list(self):
        print('>>> get_stock_corp_codes_list 진입 >>>')
        self.get_stock_corp_codes_zip()
        from xml.etree.ElementTree import parse
        xmlTree = parse('{}/CORPCODE.xml'.format(self.codes_path))
        root = xmlTree.getroot()
        company_list = root.findall('list')
        corp_codes_list = []
        for i in range(len(company_list)):
            sub_list = []
            sub_list.append(company_list[i].findtext('corp_code'))
            sub_list.append(company_list[i].findtext('corp_name'))
            sub_list.append(company_list[i].findtext('stock_code'))
            sub_list.append(company_list[i].findtext('modify_date'))
            corp_codes_list.append(sub_list)
        return corp_codes_list

    # 코스피(sosok=0)/코스닥(sosok=1) 거래량 상위종목 목록 받아오기
    def get_kospi_stock_names(self, sosok=0):
        url = 'https://finance.naver.com/sise/sise_quant.nhn?sosok={}'.format(sosok)
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

    # 이름 혹은 상장코드로 기업명, 기업코드(단일) 받아오기
    def get_corp_code_N_name(self, scanner, by='stock_code'):
        # company_codes = self.get_company_codes_df()
        is_searched_company = self.company_codes[by] == scanner
        res = self.company_codes[is_searched_company]
        corp_code = str(res.values[0][0]).zfill(8)
        corp_name = res.values[0][1]
        return corp_code, corp_name

    # 이름 혹은 상장코드로 기업명, 기업코드(목록) 받아오기
    # scanner : 검색 필터(기업명, 상장코드), by : corp_name(기업명) / stock_code(상장코드)
    def get_corp_codes_N_names(self, scanner, by='corp_name'):
        print('>>> get_corp_codes_N_names 진입 >>>')
        is_searched_company = self.company_codes[by].isin(scanner)
        company_codes = self.company_codes[is_searched_company]
        company_codes['corp_code'] = company_codes['corp_code'].astype('str')
        cond = company_codes['stock_code'] == ' '
        company_codes = company_codes[~cond]
        company_codes['corp_code'] = company_codes['corp_code'].str.zfill(8)
        corp_codes_N_names = company_codes[['corp_code', 'corp_name']].values.tolist()
        return corp_codes_N_names

    def make_sales_profit_list(self, corp_codes_N_names, market='KOSPI', bsns_year='2020'):
        df_pool = []
        # 다중회사 주요계정
        url = 'https://opendart.fss.or.kr/api/fnlttMultiAcnt.json'
        for code, name in corp_codes_N_names:
            params = {'crtfc_key': 'ead0486e8d1b91cc5f958b102a18a288943e97d5',
                      'corp_code': code, 'bsns_year': bsns_year, 'reprt_code': '11011'}
            res = requests.get(url, params)
            data = json.loads(res.text).get('list')
            try:
                sales = int(data[22].get('thstrm_amount').replace(',', ''))
                profit = int(data[24].get('thstrm_amount').replace(',', ''))
                df_pool.append([name, sales, profit, market])
            except:
                pass
        return df_pool

    def make_bubble_csv(self, df_pool):
        """
        설명 :
        [input] kospi, kosdaq 거래량 상위 100개 기업 기업명, 당기 매출, 당기 영업이익, 시장 리스트
        [output] csv
        """
        print('>>> make_bubble_csv 진입 >>>')
        bubble_df = pd.DataFrame(df_pool, columns=['name', 'sales', 'profit', 'market'])
        bubble_df = self.put_min_max_scaler_on_sales_N_profit(bubble_df)
        bubble_df.to_csv('{}/{}'.format(self.bubble_path, self.bubble_title))

        # 매출, 영업이익 정규화 수치 컬럼 추가하기

    def put_min_max_scaler_on_sales_N_profit(self, bubble_df):
        max_p = bubble_df.profit.max()
        min_p = bubble_df.profit.min()
        max_s = bubble_df.sales.max()
        min_s = bubble_df.sales.min()
        bubble_df['min_max_profit'] = bubble_df.profit.apply(lambda x: (x - min_p) / (max_p - min_p))
        bubble_df['min_max_sales'] = bubble_df.sales.apply(lambda x: (x - min_s) / (max_s - min_s))
        return bubble_df

    # 매출, 영업이익 버블차트 띄우기
    # by : 'profit' (이익), 'sales' (매출)
    def get_bubble_chart(self, by='profit'):
        fig = px.scatter(self.bubble_df, x="sales", y="profit",
                         size="min_max_" + by, color="market",
                         hover_name="name", log_x=True, size_max=60)
        # fig.show()
        return fig.to_json()

    def make_company_codes_csv(self):
        print('>>> make_company_codes_csv 진입 >>>')
        corp_codes_list = self.get_stock_corp_codes_list()
        company_codes = pd.DataFrame(corp_codes_list, columns=['corp_code', 'corp_name', 'stock_code', 'modify_date'])
        company_codes.to_csv('{}/{}'.format(self.codes_path, self.codes_title))

    def get_company_codes_df(self):
        try:
            company_codes = pd.read_csv('{}/{}'.format(self.codes_path, self.codes_title), index_col=0)
        except:
            t = threading.Thread(target=self.make_company_codes_csv)
            t.start()
            codes_title = sorted(os.listdir(self.codes_path))[-2]
            company_codes = pd.read_csv('{}/{}'.format(self.codes_path, codes_title), index_col=0)
        return company_codes

    def get_fs_from_corp_code(self, corp_code, bsns_year='2020', cfs_or_ofs='None'):
        """
        설명 : corp_code를 입력받아 재무제표 데이터프레임 만들기
        속성 :
        bsns_year : 2015 to 2020
        cfs_or_ofs : CFS(연결재무제표) or OFS(재무제표)
        """
        url = 'https://opendart.fss.or.kr/api/fnlttMultiAcnt.json'
        params = {'crtfc_key': 'ead0486e8d1b91cc5f958b102a18a288943e97d5',
                  'corp_code': corp_code, 'bsns_year': bsns_year, 'reprt_code': '11011'}
        print(params)
        res = requests.get(url, params)
        json.loads(res.text)
        company_fs = pd.DataFrame(json.loads(res.text).get('list'))

        try:
            company_fs = self.get_refined_fs(company_fs)
            if cfs_or_ofs != 'None':
                company_cfs_or_ofs = company_fs.groupby('fs_div').get_group(cfs_or_ofs)
                return company_cfs_or_ofs
            else:
                return company_fs

        except:
            return '조회 정보가 없습니다.'

    # 재무제표 데이터프레임에서 x축 인덱스 가져오기
    def get_report_index_from_fs(self, company_fs):
        report_index = company_fs[['thstrm_nm', 'frmtrm_nm', 'bfefrmtrm_nm']].iloc[1]
        report_index = report_index.to_list()
        return report_index

    def str_to_int_processor(self, x):
        try:
            return int(x)
        except:
            return 0

    # 연결재무제표(CFS), 재무제표(OFS)
    def get_cfs_or_ofs(self, company_fs, cfs_or_ofs):
        company_cfs_or_ofs = company_fs.groupby('fs_div').get_group(cfs_or_ofs)
        return company_cfs_or_ofs

    def get_refined_fs(self, company_fs):
        # 문자열 정수형 변환
        company_fs['thstrm_amount'] = company_fs['thstrm_amount'].str.replace('-|,', '').apply(
            self.str_to_int_processor)
        company_fs['frmtrm_amount'] = company_fs['frmtrm_amount'].str.replace('-|,', '').apply(
            self.str_to_int_processor)
        company_fs['bfefrmtrm_amount'] = company_fs['bfefrmtrm_amount'].str.replace('-|,', '').apply(
            self.str_to_int_processor)
        # 필요 컬럼 추출
        refined_company_fs = company_fs[['fs_div', 'sj_nm', 'account_nm',
                                         'thstrm_nm', 'thstrm_dt', 'thstrm_amount',
                                         'frmtrm_nm', 'frmtrm_dt', 'frmtrm_amount',
                                         'bfefrmtrm_nm', 'bfefrmtrm_dt', 'bfefrmtrm_amount'
                                         ]]
        return refined_company_fs

    # 재무제표에서 당기, 전기, 전전기 데이터 추출
    def get_data_from_fs(self, refined_company_fs, keyword='None', bs_is='재무상태표'):
        company_bs_or_is = refined_company_fs.groupby('sj_nm').get_group(bs_is)
        res = []
        if keyword != 'None':
            is_keyword = company_bs_or_is['account_nm'] == keyword
            res = company_bs_or_is[is_keyword].iloc[0, :]
            res = [res.thstrm_amount, res.frmtrm_amount, res.bfefrmtrm_amount]
        return res

    # 자본총계, 부채총계, x축 인덱스, 기업명 입력해 자산 막대 그래프 출력
    def get_capital_debt_chart(self, capital_sum, debt_sum, report_index, corp_name):
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
        return fig.to_json()


class Asset_Accounter:

    def status_calculator(self, dividend, divisor, opt):
        index = dividend / divisor
        print('index :::: ', index)
        if opt == '유동성 비율':
            if index > 2:
                result = '좋음'
            elif index > 1:
                result = '양호'
            else:
                result = '주의'
            return result
        elif opt == '안정성 비율':
            if index > 2:
                result = '주의'
            elif index > 1:
                result = '양호'
            else:
                result = '좋음'
            return result
        elif opt == '수익성 비율':
            return str(round(index * 100)) + '%'
        else:
            return 'Undefined'

    def get_status_plot(self, labels, values, opt='유동성 비율'):
        """
        설명 : 기업 재무건전성 차트
        속성 :
        labels : ['유동자산','유동부채']
        values : [유동자산, 유동부채]
        opt : + / -
        """
        result = self.status_calculator(dividend=values[0], divisor=values[1], opt=opt)
        print(labels[0], ':', values[0])
        print(labels[1], ':', values[1])
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.7)])
        fig.update_layout(
            title={
                'text': opt,
                'y': 0.9,
                'x': 0.46},
            font={
                'size': 20,
            },
            annotations=[dict(text=result, font_size=50, showarrow=False)]
        )
        fig.update_traces(
            marker=dict(colors=['#106eea', '#dfdfdf']))

        # fig.show()
        return fig.to_json()