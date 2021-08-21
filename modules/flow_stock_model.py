import pandas as pd
import FinanceDataReader as fdr
from pykrx import stock
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import os
import joblib
import threading

from sklearn.preprocessing import Normalizer
from sklearn.cluster import KMeans
from modules.flow_stock_chart import query_OracleSQL




class Stock_Clustering:
    """
    num: 몇 개의 그룹으로 묶을지 지정 (default = 10)
    """

    def __init__(self, num=10):
        self.num = num
        self.path = "{}/stock/static/clustering/{}".format(os.getcwd(), num)
        self.now = datetime.now()
        filename = f'clustered_result_{num}_{self.now.strftime("%Y%m%d")}.csv'
        modelname = f'clusters_{self.num}_{self.now.strftime("%Y%m%d")}.pkl'
        self.file_path = f'{self.path}/{filename}'
        self.model_path = f'{self.path}/{modelname}'
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            print(f'make dir :: {self.path}')
        if modelname not in os.listdir(self.path):
            print(f'{filename} not found')
            t = threading.Thread(target=self.clustering)
            t.start()

    def __make_dataframe(self,codes):
        """
        해당 종목들의 1년치 주가 움직임을 데이트프레임으로

        :param codes: 종목 코드의 리스트
        :return: 종목들의 1년치 주가 움직임을 데이트프레임으로
        """
        yearago = self.now - relativedelta(years=1)
        yearago = yearago.strftime('%Y-%m-%d')
        prices_list = list()

        for code in tqdm(codes):
            try:
                prices = fdr.DataReader(code, yearago)['Close']
                prices = pd.DataFrame(prices)
                prices.columns = [code]
                prices_list.extend([prices])
            except:
                pass
        prices_df = pd.concat(prices_list, axis=1)
        prices_df.sort_index(inplace=True)
        prices_df.dropna(axis=1, thresh=int(len(prices_df) * 0.99), inplace=True)  # nan이 1% 이상인거 제외
        prices_df.fillna(method='bfill', inplace=True)
        df = prices_df.pct_change().iloc[1:].T  # 주가 수익률, index:종목코드, col:날짜
        self.codes = list(df.index)
        self.movements = df.values
        normalize = Normalizer()
        array_norm = normalize.fit_transform(df)
        final_df = pd.DataFrame(array_norm, columns=df.columns, index=df.index)
        return final_df

    def clustering(self):
        """
        클러스터링 모델 저장, Kospi200 종목 클러스터링 결과 저장

        :return: clustered_result_{num}_{date}.csv & clusters_{num}_{today}.pkl
        """
        k200 = stock.get_index_portfolio_deposit_file("1028")  # KOSPI 200
        df = self.__make_dataframe(k200)
        clusters = KMeans(self.num)  # 10개 클러스터
        clusters.fit(df)
        labels = clusters.labels_
        joblib.dump(clusters, f'{self.model_path}')

        clustered_result = pd.DataFrame({'labels': labels, 'codes': self.codes})

        sql = "SELECT c_code, c_name, c_category FROM company where c_market ='KOSPI'"
        df_db = query_OracleSQL(sql)
        merge_df = pd.merge(clustered_result, df_db, how='inner', left_on='codes', right_on='C_CODE')
        del merge_df['codes']
        print(merge_df.labels.value_counts())
        merge_df.to_csv(self.file_path)

    def search(self, code):
        """
        :param code: 기업 코드
        :return: code와 같은 group의 DataFrame
        """
        df_final = pd.read_csv(self.file_path,
                               index_col=0,
                               dtype=str,
                               converters={'labels': int})
        df_final.index = df_final['C_CODE']
        del df_final['C_CODE']
        if code in df_final.index: # code가 KOSPI200 안에 있으면 이미 저장된 csv 파일 이용
            res_df = df_final[(df_final.labels == (df_final.loc[code]['labels']))
                              & (df_final.index != code)]
        else:
            model = joblib.load(self.model_path) # 없으면 모델을 통해 예측
            final_df = self.__make_dataframe([code])
            try:
                labels = model.predict(final_df.values)
                res_df = df_final[df_final.labels == labels[0]]
            except:
                print(f'예외 발생 => 전체 종목 리턴')
                return df_final
        return res_df

















