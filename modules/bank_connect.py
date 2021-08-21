class bank_connect:
    import warnings as wr 
    wr.filterwarnings('ignore')
    
    # 현금흐름표 df화
    def loadbank(bank, m_id):
        print('>>>> loadbank 진입 >>>>')
        import pandas as pd
        import numpy as np
        path = 'asset/static/{}_{}.xls'.format(bank,m_id)
        new_df= pd.read_excel(path, header=6)
        #new_df = pd.read_excel('dataset/banking.xls', header=6)
        category = {
         '근로소득':['플로우컴퍼니'],
         '기타소득':['신한할인캐쉬백'],
         '이전소득':['훈련비고용부', '노동부인천북부'],
         '부채유입':['IBK기업'],
         '식비지출': ['팔람까오','대원당'],
         '여가비지출':[],
         '기타지출' : ['카카오페이', '네이버페이결제', '인천이음카드\u3000', '다이소(부평시','경기지역카드'],
         '주거지출' : ['오피스텔관리비','공과금'],
         '차비지출' : [],
         '품위유지지출' : ['씨제이올리브네','지그재그P','박명순(루비폭','고요향수(GOYOH','(주) 홈앤쇼핑','롯데쇼핑','쿠팡','무신사스토어','샤넬','입생로랑'],
         '보험지출':['동부생명'],
         '통신비지출':['LGU+'],
         '금융지출':['한국장학재단','주택도시기금이자'],
         '투자유출':['NH나무증권'],
         '저축유출':['카카오적금'],
         '건강유지비':['온누리중앙약국'],
         '단기부채유입':['IBK생활비대출'],
         '장기부채유입':['주택도시기금대출']  
        }
        foodlist= ['커피','카페','이디야','스타벅스','빽다방','반점','투썸플레이스','아마스빈','배스킨라빈스','설빙','GS25','씨유','미니스톱','이마트','세븐일레븐','G','GS25','홈플러스','마트',
          '버거','맥도날드','롯데리아','쉐이크쉑','써브웨이','피자','치킨','라멘','스시','모모네','초밥','훠궈','마라','아웃백',
          '김밥','떡볶이','배떡','소금구이','횟','오돌뼈','닭','곱창','뻥쟁이네','삼겹살','육회','푸드','맥주','펍','식당','밥','죽','자판기',
          '케이크','디저트','빵','꽈배기','제과','파리바게','우아한형제']
        translist= ['교통','택시','버스','티머니']
        healthlist = ['병원','약국','의원','후과','피부과']
        leisurelist = ['자전','아트','빠지','보드','멜론','볼링','호텔','요가','워터','ZOOM']


        for i in range(0,len(new_df['내용'])-1):
            # 식비지출, 차비지출, 건강유지비 ,여가비지출
            for e in range(0,len(foodlist)-1):
                if new_df['내용'][i].find(foodlist[e]) != -1:
                    category['식비지출'].append(new_df['내용'][i])
                    break
            for e in range(0,len(translist)-1):        
                if new_df['내용'][i].find(translist[e]) != -1:
                    category['차비지출'].append(new_df['내용'][i])
                    break
            for e in range(0,len(healthlist)-1):        
                if new_df['내용'][i].find(healthlist[e]) != -1:
                    category['건강유지비'].append(new_df['내용'][i])
                    break
            for e in range(0,len(leisurelist)-1):        
                if new_df['내용'][i].find(leisurelist[e]) != -1:
                    category['여가비지출'].append(new_df['내용'][i])
                    break
        new_df['카테고리'] = 0
        for i in range(0, len(new_df)):
            for k, v in category.items():
                list(set(category[k]))
                if new_df.loc[i, '내용'] in category[k]:
                    new_df.loc[i, '카테고리'] = k
                    break
                else:
                    new_df.loc[i, '카테고리'] = '미분류'

        # FLOW 컬럼 추가 => 유입 유출 판단
        new_df['FLOW'] = np.where(new_df['출금(원)'] != 0, "유출", "유입")
        # C_PRICE 컬럼추가
        new_df['C_PRICE'] = np.where(new_df['출금(원)'] != 0, new_df['출금(원)'], new_df['입금(원)'])
        new_df['C_PRICE'].astype(int)
        # 거래일자 2021/07/25 형태로
        date_list = [new_df.iloc[i]['거래일자'].replace('.', '/') for i in range(len(new_df['거래일자']))]
        new_df['거래일자'] = np.array(date_list)
        methodlist = {# 펌 뱅킹 : 기업자금관리의 편의성을 제공하는 금융서비스
        '펌뱅킹' : ['FB이체', '타행FB', '국세', 'FB자동', 'FB입금'],
        '계좌이체' : ["타행MB", "타행IB", 'OP이체', '모바일', '모바일', '타행PC'],
        '체크카드' : ["신한체", '카드결'],
        '캐쉬백' : ["SHC입"]
        }
        for i in range(0, len(new_df)):
            for k, v in methodlist.items():
                list(set(methodlist[k]))
                if new_df.loc[i, '내용'] in methodlist[k]:
                    new_df.loc[i, '적요'] = k
                    break
                else:
                    new_df.loc[i, '적요'] = '미분류'
        cashf_df = new_df[['FLOW', '카테고리', '내용', '적요', 'C_PRICE', '거래일자']]
        cashf_df.columns = ['C_FLOW', 'C_CATEGORY', 'C_CONTENT', 'C_METHOD', 'C_PRICE', 'C_DATE']
        cashf_df['C_DATE'].astype(str)
        cashf_df['C_DATE'] = pd.to_datetime(cashf_df['C_DATE'])
        return cashf_df
    
    # 현금흐름표 인서트 자산 업데이트
    def incashUpasset(bank, m_id):
        print('>>>> incashUpasset 진입 >>>>')
        import pandas as pd
        import cx_Oracle as ora
        from modules import database as db
        cashf_df = bank_connect.loadbank(bank, m_id)
        db = db.oracleDB
        conn = ora.connect(db)
        cursor = conn.cursor()
        columns = ','.join(cashf_df.columns)  
        values = ','.join([':{:d}'.format(i + 1) for i in range(len(cashf_df.columns))])

        sql = "INSERT into cashflow (C_NUM,M_ID,{columns:}) VALUES (cashflow_seq.nextVal,'"+m_id+"',{values:})"
        cursor.executemany(sql.format(columns=columns, values=values),cashf_df.values.tolist())
        # 자산 업데이트 
        # 현금성자산 # 본인은 빼야함
        sql_inself = "select sum(c_price) from cashflow where m_id='"+m_id+"' and c_flow='유입' and c_content=(select m_name from member where m_id='"+m_id+"')"
        cursor.execute(sql_inself)
        inself = cursor.fetchone()
        sql_outself = "select sum(c_price) from cashflow where m_id='"+m_id+"' and c_flow='유출' and c_content=(select m_name from member where m_id='"+m_id+"')"
        cursor.execute(sql_outself)
        outself = cursor.fetchone()
        sql_incash = "select sum(c_price) from cashflow where m_id='"+m_id+"' and c_flow='유입'"
        cursor.execute(sql_incash)
        incash = cursor.fetchone()
        sql_outcash = "select sum(c_price) from cashflow where m_id='"+m_id+"' and c_flow='유출'"
        cursor.execute(sql_outcash)
        outcash = cursor.fetchone()
        a_cash = (incash[0]-inself[0])-(outcash[0]-outself[0])
        # 투자자산
        sql_invest = "select sum(c_price) from cashflow where m_id='"+m_id+"' and c_category='투자유출' or c_category='저축유출'"
        cursor.execute(sql_invest)
        a_investment = cursor.fetchone()
        if str(a_investment[0]) == 'None':
            a_investment = [0,0]
        # 장기 부채 부동산
        sql_long_loan = "select sum(c_price) from cashflow where m_id='"+m_id+"' and c_category='장기부채유입'"
        cursor.execute(sql_long_loan)
        a_loan = cursor.fetchone()
        if str(a_loan[0]) == 'None':
            a_loan = [0,0]
        # 단기 부채
        sql_credit = "select sum(c_price) from cashflow where m_id='"+m_id+"' and c_category='단기부채유입'"
        cursor.execute(sql_credit)
        a_credit = cursor.fetchone()
        if str(a_credit[0]) == 'None':
            a_credit = [0,0]
        sql_asset = "update asset set a_cash={},a_investment={}, a_property ={} ,a_loan={}, a_credit={} where m_id='"+m_id+"'"
        cursor.execute(sql_asset.format(a_cash,a_investment[0],a_loan[0],a_loan[0],a_credit[0]))
        conn.commit()
        cursor.close()
        conn.close()


