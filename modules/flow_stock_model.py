import pandas as pd
import FinanceDataReader as fdr
from pykrx import stock
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import os

from sklearn.preprocessing import Normalizer
from sklearn.cluster import KMeans
from modules.flow_stock_chart import query_OracleSQL




class Stock_Clustering:

    def __init__(self, num=10):
        self.num = num
        self.path = "{}/static/clustering/{}".format(os.getcwd(), num)
        filename = f'clustered_result_{num}.csv'
        self.file_path = f'{self.path}/{filename}'
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            print(f'make dir :: {self.path}')
        if filename not in os.listdir(self.path):
            print(f'{filename} not found')
            self.clustering()

    def make_dataframe(self):
        prices_list = list()
        for code in tqdm(self.stock_code):
            try:
                yearago = datetime.now() - relativedelta(years=1)
                yearago = yearago.strftime('%Y-%m-%d')
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
        df_norm = pd.DataFrame(array_norm, columns=df.columns)
        final_df = df_norm.set_index(df.index)
        return final_df

    def clustering(self):
        sql = "SELECT c_code, c_name, c_category, c_market FROM company where c_market in ('KOSPI', 'KOSDAQ')"
        df_db = query_OracleSQL(sql)
        #         self.stock_code = df_db['C_CODE']

        self.stock_code = stock.get_index_portfolio_deposit_file("1028") # KOSPI 200

        df = self.make_dataframe()
        clusters = KMeans(self.num)  # 10개 클러스터
        clusters.fit(df)
        labels = clusters.predict(self.movements)
        clustered_result = pd.DataFrame({'labels': labels, 'codes': self.codes})

        merge_df = pd.merge(clustered_result, df_db, how='inner', left_on='codes', right_on='C_CODE')
        del merge_df['codes']
        print(merge_df.value_counts())
        merge_df.to_csv(self.file_path)

    def search(self, code):
        df_final = pd.read_csv(self.file_path,
                               index_col=0,
                               dtype=str,
                               converters={'labels': int})
        df_final.index = df_final['C_CODE']
        del df_final['C_CODE']
        try:
            res_df = df_final[(df_final.labels == (df_final.loc[code]['labels'])) & (df_final.index != code)]
            # res2 = res_df.sample(3)['C_NAME']  # 추천을 해야하지만 일단 랜덤으로..
            # {k: v for k, v in res2.items()}  # 요렇게 전달하면 될듯
        except:
            print('해당 종목 없음 => 전체 종목 리턴')
            return df_final
        return res_df

















